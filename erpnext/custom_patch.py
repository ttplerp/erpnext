import frappe
from erpnext.setup.doctype.employee.employee import create_user
# import pandas as pd
import csv
from frappe.utils import flt, cint, nowdate, getdate, formatdate

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
		ds.new_password = 'nhdcl@2023'
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
	with open("/home/frappe/erp/apps/Final.csv") as f:
		reader = csv.reader(f)
		mylist = list(reader)
		c = 0
		for i in mylist:
			ss = frappe.db.sql("select name, employee, employee_name, branch, is_active from `tabSalary Structure` where employee='{}' and branch = '{}' and employee_name = '{}'".format(i[1], i[0], i[2]), as_dict=1)		
			for d in ss:
				ss_doc = frappe.get_doc("Salary Structure", {"name": d.name})
				if ss_doc.employee == i[1] and ss_doc.branch == i[0]:
					row = ss_doc.append('earnings',{})
					row.salary_component = "Overtime Allowance"
					row.amount = flt(i[3])
					row.from_date = "2023-03-01"
					row.to_date = "2023-03-31"
				ss_doc.save(ignore_permissions=True)
				
				# rem_list = []
				# for a in ss_doc.get("earnings"):
				# 	if ss_doc.employee == i[2] and ss_doc.branch == i[0] and a.salary_component == "Overtime Allowance":
				# 		rem_list.append(a)

				# [ss_doc.remove(a) for a in rem_list]
				# ss_doc.save(ignore_permissions=True)
			c += 1
		print('DONE')
		print(str(c))

def update_customer_code():
	customer = frappe.db.get_all("Customer", {"customer_group": "Rental"}, ["name"])
	# data=[]
	for a in customer:
		code = a['name'].split("-")
		frappe.db.sql("update tabCustomer set customer_code='{0}' where name='{1}'".format(code[1],a.name))
		# data.append(code[1])
	# log(data)
		
	# log(customer)