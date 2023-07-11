import frappe
from erpnext.setup.doctype.employee.employee import create_user
import pandas as pd
import csv
from frappe.utils import flt, cint, nowdate, getdate, formatdate

def update_sle_gl():
	for b in ["PRO-23-07-05-095","PRO-23-07-06-062","PRO-23-07-06-069","PRO-23-07-06-064","PRO-23-07-06-070"]:
		#frappe.db.sql("delete from `tabGL Entry` where voucher_type='Production' and voucher_no='{}'".format(b))
		for a in frappe.db.sql("""select name, actual_qty, incoming_rate,
									valuation_rate, qty_after_transaction
									from `tabStock Ledger Entry` 
									where voucher_no="{}"
									and item_code="300023"	
								""".format(b), as_dict=True):
			stock_value = a.qty_after_transaction * a.valuation_rate
			stock_value_difference = a.actual_qty * a.incoming_rate
			frappe.db.sql("""  update `tabStock Ledger Entry`
							set stock_value='{}', stock_value_difference='{}'
							where name ='{}'
						""".format(stock_value, stock_value_difference, a.name))
		doc = frappe.get_doc("Production", b)
		#doc.make_gl_entries()
		#frappe.db.commit()
		print("Done for Production No: " + str(b))

def get_wrong_dn():
	i=0
	for a in frappe.db.sql("""
					select is_cancelled docstatus, voucher_no, credit, posting_date, account from `tabGL Entry`
					where voucher_type="Delivery Note"
					and account="Cost of Goods Manufactured - SMCL"
					and credit > 0
					and is_cancelled = 0
					order by posting_date 
				""", as_dict=True):
		i+=1
		print(str(i) + ", " + str(a.voucher_no))
		
def rename_asset():
	i = 0
	abbr = "SMCL-BCS-23-"
	for d in frappe.db.sql("select name, asset_category, creation from `tabAsset` \
			where asset_category in ('Building & Civil Structure') and docstatus = 0 order by creation",as_dict=True):
		name  = ""
		if len(str(i)) == 1:
			name = abbr +"000"+ str(i)
		elif len(str(i)) == 2:
			name = abbr +"00"+ str(i)
		elif len(str(i)) == 3:
			name = abbr +"0"+ str(i)
		else:
			name = abbr + str(i)
			
		print(name)
		i += 1
def delete_asset_gl():
	for d in frappe.db.sql("select name, asset_category from `tabAsset` \
			where asset_category in ('Furniture & Fixture', 'Plant & Machinery','Building & Civil Structure') and docstatus = 2",as_dict=True):
		frappe.db.sql("delete from `tabGL Entry` where against_voucher_type='Asset' and against_voucher= '{}'".format(d.name))
		for je in frappe.db.sql("select distinct(parent) as name from `tabJournal Entry Account` where reference_name= '{}'".format(d.name),as_dict=1):
			je_doc = frappe.get_doc("Journal Entry",je.name)
			print(je_doc.name)
			je_doc.delete()
	# 	asset = frappe.get_doc("Asset",d.name)
	# 	print(asset.name, ' ',asset.asset_category,' ', asset.docstatus)
	# 	asset.cancel()
	print("Done")
	frappe.db.commit()
def pol_entry_correction():
	for d in frappe.bd.sql("select name,reference_type,reference,equipment from `tabPOL Entry` where rate <= 0"):
		if d.reference_type == "POL Receive":
			doc = frappe.get_doc(d.reference_type,d.reference)
			if doc.name:
				frappe.db.sql('''
					update `tabPOL Entry` set fuelbook = '{}', supplier='{}', item_name='{}',
					memo_number = '{}', pol_slip_no = '{}', mileage = '{}', km_difference = '{}',
					current_km = '{}', rate = {} where name = '{}'
					'''.format(doc.fuelbook,doc.supplier,doc.item_name, doc.memo_number, 
				doc.pol_slip_no, doc.mileage, doc.km_difference, doc.cur_km_reading, doc.rate, d.name))
		elif d.reference_type == "POL Issue":
			doc = frappe.get_doc("POL Issue Items",{"parent":d.reference,"equipment":d.equipment})
			if doc.name:
				frappe.db.sql('''
					update `tabPOL Entry` set fuelbook = '{}', mileage = '{}', km_difference = '{}',
					current_km = '{}', rate = {} where name = '{}' and equipment = '{}'
					'''.format(doc.fuelbook, doc.mileage, doc.km_difference, doc.cur_km_reading, doc.rate, d.name, doc.equipment))
	
def cost_center_correction_budget():
	for d in frappe.db.get_list("Committed Budget",filters={"reference_type":"Journal Entry"},fields=["cost_center","name"]):
		parent_cost_center = frappe.db.get_value("Cost Center",{"name":d.cost_center,"use_budget_from_parent":1},["budget_cost_center"])
		if parent_cost_center:
			frappe.db.sql("update `tabCommitted Budget` set cost_center = '{}' where name = '{}'".format(parent_cost_center,d.name))
			print(d.cost_center,' ',d.name)
	print('<===================================================>')
	for d in frappe.db.get_list("Consumed Budget",filters={"reference_type":"Journal Entry"},fields=["cost_center",'name']):
		parent_cost_center = frappe.db.get_value("Cost Center",{"name":d.cost_center,"use_budget_from_parent":1},["budget_cost_center"])
		if parent_cost_center:
			frappe.db.sql("update `tabConsumed Budget` set cost_center = '{}' where name = '{}'".format(parent_cost_center,d.name))
			print(parent_cost_center,' ',d.name)
	print('done')
	frappe.db.commit()

def create_gl_for_previous_production():
	for p in frappe.db.get_list("Production",filters={"creation":["<=","2023-03-02"],"docstatus":1}, fields=["name","creation"]):
		doc = frappe.get_doc("Production",p.name)
		if len(doc.raw_materials) > 0:
			frappe.db.sql("delete from `tabGL Entry` where voucher_no = '{}' and voucher_type = 'Production'".format(doc.name))
			doc.make_gl_entries()
			print(doc.name)
	frappe.db.commit()
	print('done')
def create_leave_ledger_entry():
	for e in frappe.db.sql('''select name from `tabEmployee` where status = "Active"''',as_dict=1):
		if frappe.db.exists("Leave Allocation",{"employee":e.name,"leave_type":"Earned Leave","docstatus":1}):
			leave_allocation = frappe.get_doc("Leave Allocation",{"employee":e.name,"leave_type":"Earned Leave","docstatus":1})
			print(leave_allocation.employee, ' : ', leave_allocation.name, ' : ', leave_allocation.leave_type)
			leave_ledger_entry = frappe.new_doc("Leave Ledger Entry")
			leave_ledger_entry.flags.ignore_permissions=1
			leave_ledger_entry.update({
				"employee":leave_allocation.employee,
				"employee_name":leave_allocation.employee_name,
				"leave_type":leave_allocation.leave_type,
				"transaction_type":"Leave Allocation",
				"transaction_name":leave_allocation.name,
				"leaves":2.5,
				"company":leave_allocation.company,
				"from_date":"2023-01-01",
				"to_date":'2023-12-31'
			})
			leave_ledger_entry.insert()
			leave_ledger_entry.submit()

# def post_payment_je_leave_encashment():
#     le = frappe.db.sql("""
#         select expense_claim from `tabLeave Encashment` where
#         docstatus = 1
#     """,as_dict=1)
#     for a in le:
#         expense_claim = frappe.get_doc("Expense Claim", a.expense_claim)
#         if expense_claim.docstatus = 1:
#             expense_claim.post_accounts_entry()
#             print(expense_claim.name)
#     frappe.db.commit()

def change_account_name():
	# print('here')
	for d in        [
					{
					"old_name": "Tshophhangma Consumable Warehouse",
					"new_name": "Tshophangma Consumable Warehouse - SMCL"
					}
					]:
		if frappe.db.exists("Account",{"account_name":d.get("old_name")}):
			doc = frappe.get_doc("Account",{"account_name":d.get("old_name")})
			print('old : ',doc.account_name,'\nNew Name : ' ,d.get("new_name"))
			doc.account_name = d.get("new_name")
			doc.save()

def assign_je_in_invoice():
	print('<------------------------------------------------------------------------------------------------>')
	for d in frappe.db.sql('''
				select reference_name, reference_type, parent from `tabJournal Entry Account` where reference_type in ('Transporter Invoice','EME Invoice')
				''', as_dict=True):
		if d.reference_type and d.reference_name and frappe.db.exists(d.reference_type, d.reference_name):
			doc = frappe.get_doc(str(d.reference_type),str(d.reference_name))
			doc.db_set("journal_entry",d.parent)
	print('Done')
def assign_ess_role():
	users = frappe.db.sql("""
		select name from `tabUser` where name not in ('Guest', 'Administrator')
	""",as_dict=1)
	for a in users:
		user = frappe.get_doc("User", a.name)
		user.flags.ignore_permissions = True
		if "Employee Self Service" not in frappe.get_roles(a.name):
			user.add_roles("Employee Self Service")
			print("Employee Self Service role added for user {}".format(a.name))


def delete_salary_detail_salary_slip():
	ssd = frappe.db.sql("""
		select name from `tabSalary Detail` where parenttype = 'Salary Slip'
	""",as_dict=1)
	for a in ssd:
		frappe.db.sql("delete from `tabSalary Detail` where name = '{}'".format(a.name))
		print(a.name)

def create_users():
	print("here")

	employees = frappe.db.sql("""
		select name from `tabEmployee` where company_email is not NULL and user_id is NULL
	""",as_dict=1)
	if employees:
		for a in employees:
			employee = frappe.get_doc("Employee", a.name)
			if not frappe.db.exists("User",employee.company_email):
				create_user(a.name, email = employee.company_email)
				print("User created for employee {}".format(a.name))
				employee.db_set("user_id", employee.company_email)
	frappe.db.commit()

def update_employee_user_id():
	print()
	users = frappe.db.sql("""
		select name from `tabUser`
	""",as_dict=1)
	if users:
		for a in users:
			employee = frappe.db.get_value("Employee",{"company_email":a.name},"name")
			if employee:
				employee_doc = frappe.get_doc("Employee",employee)
				employee_doc.db_set("user_id",a.name)
				print("Updated email for "+str(a.name))
	frappe.db.commit()

def update_benefit_type_name():
	bt = frappe.db.sql("""
		select name, benefit_type from `tabEmployee Benefit Type`;
	""", as_dict=True)
	if bt:
		for a in bt:
			frappe.db.sql("update `tabEmployee Benefit Type` set name = '{}' where name = '{}'".format(a.benefit_type, a.name))
			print(a.name)

def update_department():
	el = frappe.db.sql("""
		select name from `tabEmployee`
		where department = 'Habrang & Tshophangma Coal Mine - SMCL'
		and status = 'Active'
	""",as_dict=1)
	if el:
		for a in el:
			frappe.db.sql("""
				update `tabEmployee` set department = 'PROJECTS & MINES DEPARTMENT - SMCL'
				where name = '{}'
			""".format(a.name))
			print(a.name)

def update_user_pwd():
	user_list = frappe.db.sql("select name from `tabUser` where name not in ('Administrator', 'Guest')", as_dict=1)
	c = 1
	non_employee = []
	for i in user_list:
		print("NAME '{}':  '{}'".format(c,str(i.name)))
		if not frappe.db.exists("Employee", {"user_id":i.name}):
			non_employee.append({"User ID":i.name, "User Name":frappe.db.get_value("User",i.name,"full_name")})
		ds = frappe.get_doc("User", i.name)
		ds.new_password = 'smcl@2022'
		ds.save(ignore_permissions=1)
		c += 1
	# df = pd.DataFrame(data = non_employee) # convert dict to dataframe
	# df.to_excel("Users Without Employee Data.xlsx", index=False)
	# print("Dictionery Converted in to Excel")

def update_ref_doc():
	for a in frappe.db.sql("""
							select name 
							from 
								`tabExpense Claim` 
							where 
								docstatus != 2
							"""):
		print(a[0])
		reference = frappe.db.sql("""
							select expense_type
							from 
								`tabExpense Claim Detail` 
							where 
							parent = "{}"
							""".format(a[0]))
		print(reference[0][0])
		frappe.db.sql("""
			update 
				`tabExpense Claim`
			set ref_doc ="{0}"
			where name ="{1}"
		""".format(reference[0][0],a[0]))

	
def update_overtime_application_in_ss():
	with open("/home/frappe/erp/apps/Overtime.csv") as f:
		reader = csv.reader(f)
		mylist = list(reader)
		c = 0
		for i in mylist:
			ss = frappe.db.sql("select name, employee, employee_name, branch, is_active from `tabSalary Structure` where employee='{}'and name='{}'".format(i[1], i[0]), as_dict=1)		
			for d in ss:
				ss_doc = frappe.get_doc("Salary Structure", {"name": d.name})
				if ss_doc.employee == i[1]:
					row = ss_doc.append('earnings',{})
					row.salary_component = "Overtime Allowance"
					row.amount = flt(i[3])
					row.from_date = "2023-04-01"
					row.to_date = "2023-04-30"
				ss_doc.save(ignore_permissions=True)
				
				# rem_list = []
				# for a in ss_doc.get("earnings"):
				# 	if ss_doc.employee == i[1] and a.salary_component == "Overtime Allowance":
				# 		rem_list.append(a)

				# [ss_doc.remove(a) for a in rem_list]
				# ss_doc.save(ignore_permissions=True)
			c += 1
		print('DONE')
		print(str(c))


def earned_leave_deletion_manual():
	count=0
	for d in frappe.db.sql("select name, employee, from_date, leaves, transaction_name from `tabLeave Ledger Entry` where from_date='2023-06-21'", as_dict=1):
		# print(str(d.transaction_name))	
		# print(str(d.from_date))	
		leave_all = frappe.get_doc("Leave Allocation", d.transaction_name)
		leave_all.total_leaves_allocated = flt(leave_all.total_leaves_allocated) - flt(2.5)
		leave_all.save(ignore_permissions=True)
		frappe.db.sql("delete from `tabLeave Ledger Entry` where from_date='2023-06-21' and name='{}'".format(d.name))
		count+=1
	print(str(count))
