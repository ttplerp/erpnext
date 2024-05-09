from __future__ import unicode_literals
import frappe
import erpnext
from frappe import _
from frappe.model.document import Document
from frappe import msgprint
from frappe.utils import flt, cint, nowdate, getdate, formatdate, today
from erpnext.accounts.utils import get_fiscal_year
from frappe.utils.data import date_diff, add_days, get_first_day, get_last_day, add_years,date_diff
from frappe.desk.form.linked_with import get_linked_doctypes, get_linked_docs
from frappe.model.naming import getseries
from datetime import timedelta, date,datetime
import frappe.model.rename_doc as rd
from frappe.model.rename_doc import rename_doc
from erpnext.assets.doctype.asset.depreciation import make_depreciation_entry
from erpnext.assets.doctype.asset_category.asset_category import get_asset_category_account
from erpnext.budget.doctype.budget.budget import validate_expense_against_budget
import csv

def update_pp():
	for a in frappe.db.sql("""
					select name, programme, domain from `tabTraining Management`
				""", as_dict=True):
		#print(a.name, a.programme, a.domain)
		doc = frappe.get_doc("Programme", a.programme)
		if doc.domain != a.domain:
			print(doc.domain, a.domain)
		'''
		frappe.db.sql("""update `tabTraining Management` 
						set domain='{}', 
						programme_classification='{}' 
						where name='{}'
					""".format(doc.domain, doc.programme_classification, a.name))
		frappe.db.commit()
		'''
		
def update_lo():
	for a in frappe.db.sql("select name, lo_user, lo_name, lo_email, lo_mobile from `tabTraining Center`", as_dict=True):
		doc = frappe.get_doc("Training Center", a.name)
		doc.append("item",{
					"user": a.lo_user,
					"lo_name": a.lo_name,
					"mobile_no": a.lo_mobile,
					"email": a.lo_email
				})
		doc.save()

def update_deployment():
	for a in frappe.db.sql("""select name, deployment_title from `tabDeployment` where deployment_title like '%"%' """, as_dict=True):
		title = a.deployment_title
		doc_title = title.replace('"','')
		frappe.db.sql("update `tabDeployment` set deployment_title= '{0}' where name ='{1}'".format(doc_title, a.name))
	frappe.db.commit()

def decrypt_pass():
    doc = frappe.get_doc("User", "kesang.tshomo@thimphutechpark.bt").get_password("api_secret")
    print(str(doc))

def pull_pms():
	pms_list = frappe.db.sql("""
		select a.name,a.employee,a.pms_calendar,a.final_score,a.overall_rating from `tabPerformance Evaluation` a where
		a.eval_workflow_state = 'Approved' and a.overall_rating in ('Outstanding', 'Good', 'Very Good', 'Satisfactory', 'Unsatisfactory')
		and exists(select 1 from `tabEmployee` where `tabEmployee`.status = 'Active' and `tabEmployee`.employee = a.employee)
	""", as_dict=1)
	# print(str(pms_list))
	for a in pms_list:
		print(a.employee)
		print(a.name)
		emp = frappe.get_doc("Employee", a.employee)
		row = emp.append('employee_pms', {})
		row.fiscal_year = a.pms_calendar
		row.final_score = a.final_score
		row.overall_rating = a.overall_rating
		row.performance_evaluation = a.name
		emp.save(ignore_permissions=1)
		print("done")
def update_gl_mapping():
	i = 1
	for a in frappe.db.sql("""select name, account, account_number
						   from `tabGL Mapping` where account_number != "44000307 BTN"
						   """, as_dict=True):
		doc = frappe.get_doc("GL Mapping", a.name)
		for b in frappe.db.sql("select name, account_no, branch_code, segment from `tabBranch Account Segment` where account_no = '{}'".format(a.account_number), as_dict=True):
			doc.append("items", {
							"branch_code": b.branch_code,
							"segment_code": b.segment
						})
		doc.save()
		print(i)
		i+=1
		
def update_account():
	i = 1
	for a in frappe.db.sql("""
							select name, account_without_currency, currency_code
							from `tabBranch Account Segment`
							where currency = "" or currency is NULL
							""", as_dict=True):
		
		if a.currency_code == "344":
			currency = "HDK"
		elif a.currency_code == "356":
			currency = "INR"
		elif a.currency_code == "392":
			currency = "JPY"
		elif a.currency_code == "578":
			currency = "NOK"
		elif a.currency_code == "702":
			currency = "SGD"
		elif a.currency_code == "752":
			currency = "SEK"
		elif a.currency_code == "756":
			currency = "CHF"
		elif a.currency_code == "826":
			currency = "GBP"
		elif a.currency_code == "978":
			currency = "EUR"
		elif a.currency_code == "840":
			currency = "USD"
			
		account_no = str(a.account_without_currency) + " " + str(currency)
		account = frappe.db.get_value("Account", {"account_number": account_no}, "name")
		frappe.db.sql("update `tabBranch Account Segment` set account_no='{}', currency= '{}', account='{}' where name ='{}'".format(account_no, currency, account, a.name))
		frappe.db.commit()
		i += 1
		print(i)        

def delete_sister_brother():
	member_list = frappe.db.sql(""" select name from `tabEmployee Family Details` where relationship in ('Brother','Sister')""", as_dict = 1)
	for a in member_list:
		frappe.db.sql(""" delete from `tabEmployee Family Details` where name = '{}' """.format(a.name))
		print(a.name)

# and a.cost_center = 'Tailoring & Productions of Apparels - Jangsheri - DSP'
def depreciate_asset():
	count=0
	for a in frappe.db.sql("""
						   select a.name,d.schedule_date
						   from `tabAsset` a inner join
						   `tabDepreciation Schedule` d
						   on a.name = d.parent
						   where d.schedule_date <= '2021-07-01'
						   and (d.journal_entry is null or d.journal_entry ='') and a.name='ASSET22003240'
						   and a.status = 'Submitted' group by d.parent
						   """,as_dict=1):
		make_depreciation_entry(a.name, a.schedule_date)
		print(a.name)
		count += 1
	print(count)
# print(a)
# def show_latest_promotion():
	# employees = frappe.db.sql("""
	#             select distinct a.employee, b.grade from `tabEmployee Promotion` a, `tabEmployee` b where a.employee = b.name
	#                           """, as_dict=True)
	# latest = []
	# for emp in employees:
	#     ltst = frappe.db.sql("""
	#             select a.employee, a.name, b.current, .b.new from `tabEmployee Promotion` a, `tabEmployee Property History` b where b.parent = a.name and a.employee = '{0}' order by a.promotion_date desc limit 1
	#             """.format(emp.employee), as_dict = True)
	#     latest.append({"employee":ltst[0].employee, "doc_id":ltst[0].name,"current_grade": ltst[0].current, "new_grade": ltst[0].new, "master_data_grade": emp.grade})
		
	# for a in latest:
	#     if a['new_grade'] != a['master_data_grade']:
	#         actual_current = int(a['master_data_grade']) + 1
	#         actual_new = a['master_data_grade']
	#         frappe.db.sql("""
	#                       update `tabEmployee Property History` set current = '{0}', new = '{1}' where parent = '{2}'
	#                       """.format(actual_current, actual_new, a['doc_id']))
	#         print("Employee: "+ a['employee']+" Employee Promotion ID: "+ a['doc_id'])
	# print(latest)

def show_latest_promotion_master():
	employees = frappe.db.sql("""
				select name from `tabEmployee Internal Work History` a where a.grade is not NULL and a.reference_doctype is NULL
							  """, as_dict=True)
	latest = []
	
	# for emp in employees:
	#     ltst = frappe.db.sql("""
	#             select parent, name, grade, date(from_date) as from_date from `tabEmployee Internal Work History` where parent = '{0}' and reference_doctype = 'Employee Promotion' order by from_date desc limit 1
	#             """.format(emp.employee), as_dict = True)
	#     if ltst:
	#         latest.append({"employee":ltst[0].parent, "doc_id":ltst[0].name,"grade": ltst[0].grade, "from_date": ltst[0].from_date})
		
	# for a in latest:
	#     frappe.db.sql("""
	#         update `tabEmployee` set promotion_due_date = DATE_ADD('{0}', INTERVAL (select next_promotion_years from `tabEmployee Grade` where name = '{1}') YEAR) where name = '{2}'
	#                 """.format(a['from_date'], a['grade'], a['employee']))
	#     frappe.db.sql("""
	#         update `tabEmployee Internal Work History` set promotion_due_date = DATE_ADD('{0}', INTERVAL (select next_promotion_years from `tabEmployee Grade` where name = '{1}') YEAR) where name = '{2}'
	#                 """.format(a['from_date'], a['grade'], a['doc_id']))
	#     print(a['employee'])
	
	# promotion_list = frappe.db.sql("""
	#     select name from `tabEmployee Promotion` where docstatus = 0
	#                                """, as_dict = True)
	# for d in promotion_list:
	#     frappe.db.sql("""
	#                 update `tabEmployee Property History` set fieldname = 'grade' where  parent = '{0}' 
	#                   """.format(d.name))
	#     print(d.name)
	for d in employees:
		frappe.db.sql("""
			update `tabEmployee Internal Work History` set reference_doctype = 'Employee Promotion' where name = '{}'
					  """.format(d.name))
		print(d.name)
		

def rename_employee_bob():
	counter = 0
	for a in frappe.db.sql("""select name, employee, employee_name, old_employee_id 
				from `tabEmployee`
				where concat('EMP',old_employee_id) != name 
				order by name""", as_dict=True):
		counter += 1
		new_name = "EMP"+str(a.old_employee_id)
		print(counter,"Renaming Old ID: {}".format(a.name),"to New ID: {}".format(new_name))
		rd.rename_doc("Employee", a.name, new_name, force=False, merge=False, ignore_permissions=True)
		frappe.db.sql("update `tabEmployee` set employee = name where name = '{}'".format(new_name))
		frappe.db.commit()

def empty_pms():
	for d in frappe.db.sql("""
						   select name from `tabPerformance Evaluation`
						   """, as_dict=True):
		frappe.db.sql("""
					  delete from `tabPerformance Evaluation` where name ='{}'
					  """.format(d.name))


def change_acc_name_and_number():
	account_list = frappe.db.sql("""
		select name from `tabAccount` where name like '%1%' and name not in ('Programmers day celebration (13th September) - TTPL','Office 2019 Standard(Perpetual license) - TTPL')
	""", as_dict=True)
	count = 0
	for d in account_list:
		new_name = d.name[7:]
		print(new_name)
		# frappe.db.sql("""update `tabAccount` set account_number = NULL where name = "{0}" """.format(new_name))
		print(d.name)


def test_query():
	data = frappe.db.sql(
		"""
			SELECT 
				wc.competency,wci.applicable,wci.employee_category
			FROM 
				`tabWork Competency` wc 
			INNER JOIN
				`tabWork Competency Item` wci 
			ON 
				wc.name = wci.parent 
			WHERE	
				wci.applicable = 1 
			AND 
				wci.employee_category = 'Head'
		""", as_dict=True)
	print(str(data))


def update_login_id():
	for a in frappe.db.sql("select name, email from `tabUser`", as_dict=True):
		pass


def update_employee():
	for a in frappe.db.sql("select name, class_per from `tabEmployee Education` where class_per > 0", as_dict=True):
		percent = flt(a.class_per * 100)
		frappe.db.sql("update `tabEmployee Education` set class_per = '{}' where name ='{}'".format(percent, a.name))
		print("Name: " + str(a.name) + ", Percent: " + str(percent))


def update_feedback_provider():
	for a in frappe.db.sql("select name, employee, employee_name from `tabFeedback Recipient Item`", as_dict=True):
		actual_emp_name = frappe.db.get_value("Employee", a.employee, "employee_name")
		if a.employee_name != actual_emp_name:
			print(str(a.employee_name) + " Change to :" + str(actual_emp_name))
			frappe.db.sql("update `tabFeedback Recipient Item` set employee_name = '{}' where name = '{}'".format(
				actual_emp_name, a.name))


def update_employee_id():
	i = 63
	for a in frappe.db.sql("select name, employee, employee_name from `tabEmployee` where cast(employee as decimal) > 62 order by name", as_dict=True):
		new_name = "00"+str(i)
		rd.rename_doc("Employee", a.name, new_name, force=False, merge=False, ignore_permissions=True)
		frappe.db.sql("update `tabEmployee` set employee = name where name = '{}'".format(new_name))
		i += 1
		print("Emp  ID: " + a.employee + " Name :" + a.employee_name + " change toEmp ID: " + new_name)

# method to rename the existing employee IDs with a prefix EMP
# created by SHIV on 2021/01/19


def rename_employees():
	for a in frappe.db.sql("select name, employee, employee_name from `tabEmployee` where name not like 'EMP%' order by name", as_dict=True):
		new_name = "EMP"+str(a.name)
		rename_doc("Employee", a.name, new_name, force=False, merge=False, ignore_permissions=True)
		frappe.db.sql("update `tabEmployee` set employee = name where name = '{}'".format(new_name))

		doc = frappe.get_doc("Employee", new_name)
		doc.add_comments("Employee ID is renamed from {} to {}".format(a.name, new_name))
		print("[{} - {}]".format(a.name, new_name), ":", a.employee_name)
		frappe.db.commit()

# bench execute erpnext.custom_patch.update_employee_history
def update_employee_history():
	for a in frappe.db.sql("select i.employee,te.name,institution_name,start_time,end_time,country,event_name,duration,training_type, training_category,te.obligation_type,te.obligation_till_date,te.has_obligation from `tabTraining Event` te inner join `tabTraining Event Employee` i where te.name=i.parent and te.name='TE/2021/0529'", as_dict=True):
		actual_emp = frappe.db.get_value("Employee", a.employee, "employee")
		emp_id = str(actual_emp)
		doc = frappe.get_doc("Employee", emp_id)        
		if doc.employee == actual_emp:
			row = doc.append('employee_training_history')
			row.reference_doctype = "Training Event"            
			row.reference_docname = a.name           
			row.college_training_institute = a.institution_name
			row.start_date=a.start_time
			row.end_date=a.end_time
			row.country=a.country
			row.course_title=a.event_name
			row.duration=a.duration
			row.training_type=a.training_type 
			row.training_category=a.training_category
			row.obligation_type=a.obligation_type
			row.obligation_end_date=a.obligation_till_date 
			if(a.has_obligation==1):
			 row.status="Active"                    
			doc.save(ignore_permissions=True)

# def update_training_category():
   
#      frappe.db.sql("update `tabTraining Event` set training_category = 'India' where training_category = 'India'")



def update_training_category():
	
	for a in frappe.db.sql("""select name
				from `tabTraining Event`
				where country = 'Nepal'""", as_dict=True):        
		new_name = str(a.name)       
		frappe.db.sql("update `tabTraining Event` set training_category = 'Third Country' where name = '{}'".format(new_name))
		
		# doc.update(ignore_permissions=True
		# )

def update_duration():    
	for a in frappe.db.sql("""select duration,name ,start_time,end_time                            
				from `tabTraining Event`
				where duration =0 """, as_dict=True):  
		new_name = str(a.name)       
		frappe.db.sql("update `tabTraining Event` set duration =DATEDIFF(end_time,start_time) where name = '{}'".format(new_name))

def update_item_ea():
	for a in frappe.db.sql("select name, expense_account from `tabItem`", as_dict=True):
		frappe.db.sql("Update `tabItem Default` set expense_account = '{}' where parent = '{}'".format(a.expense_account, a.name))
	frappe.db.commit()

def emp_pf():
	details = frappe.db.sql("""
		SELECT 
			name, 
			employee, 
			full_name, 
			closing_employee_contribution,
			closing_employer_contribution,
			closing_employer_interest,
			closing_employee_interest
		FROM 
			`tabEmployee PF` 
		WHERE 
			status= 'Active' and 
			cycle="July - December" and 
			docstatus =1 
	""", as_dict = 1)
	duplicates= {
		"adawdawd": 1
	}
	for a in details: 
		if a.employee in duplicates: 
			print(a.name, a.full_name, a.employee)
		else: 
			duplicates[a.employee] = 1
	print("done")
	# create the csv writer
	with open('/home/frappe/erp/apps/erpnext/erpnext/pf_dets.csv', 'w', newline='') as csvfile:
		fieldnames = ['name', 'employee', 'full_name','closing_employee_contribution', 'closing_employer_contribution', 'closing_employer_interest', 'closing_employee_interest' ]
		writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
		for a in details:
			print("writing: {} \n".format(a.full_name))
			writer.writerow({'name':a.name, 'employee': a.employee, 'full_name': a.full_name, 'closing_employee_contribution': a.closing_employee_contribution, 'closing_employer_contribution' :a.closing_employer_contribution,'closing_employee_interest': a.closing_employee_interest,'closing_employer_interest': a.closing_employer_interest})
		
def save_desuup():
	i = 0
	for d in frappe.db.sql("select name from `tabDesuup` where name like 'DS(46)%'", as_dict=True):       
		ds = frappe.get_doc("Desuup", d.name)
		ds.save()
		i += 1
	print('done')
	print(i)

def update_cost_center():
	branch = 'Hairdressing and Makeup - Dzongkhalum'
	cost_center = 'Hairdressing and Makeup - Dzongkhalum - DSP'
	for a in frappe.db.sql(""" Select * from `tabPurchase Order` where name in ('PO22050003')""", as_dict=1):
		print(a.name)
		frappe.db.sql("update `tabPurchase Order Item` set cost_center='{}' where parent='{}'".format(cost_center, a.name))
		frappe.db.sql("update `tabPurchase Order` set branch='{}' where name='{}'".format(branch, a.name))

		frappe.db.sql("update `tabCommitted Budget` set cost_center='{}' where po_no='{}'".format(cost_center, a.name))
		# for z in frappe.db.sql("select name from `tabCommitted Budget` where po_no='{}'".format(a.name), as_dict=1):
		#     print(z.name)
		
		for e in frappe.db.sql("""select distinct(parent) from `tabPayment Entry Reference` where reference_name='{}' and docstatus=1""".format(a.name), as_dict=1):
				# print(e.parent)
				frappe.db.sql("update `tabPayment Entry` set cost_center='{}', branch='{}' where name='{}'".format(cost_center, branch, e.parent))
				frappe.db.sql("update `tabGL Entry` set cost_center='{}' where voucher_no='{}'".format(cost_center, e.parent))

		for b in frappe.db.sql("""select distinct(parent) from `tabPurchase Receipt Item` where purchase_order='{}'""".format(a.name), as_dict=1):
			# print(b.parent)
			frappe.db.sql("update `tabPurchase Receipt Item` set cost_center='{}' where parent='{}'".format(cost_center, b.parent))
			frappe.db.sql("update `tabPurchase Receipt` set branch='{}' where name='{}'".format(branch, b.parent))

		for c in frappe.db.sql("""select distinct(parent) from `tabPurchase Invoice Item` where purchase_order='{}'""".format(a.name), as_dict=1):
			# print(c.parent)
			frappe.db.sql("update `tabPurchase Invoice Item` set cost_center='{}' where parent='{}'".format(cost_center, c.parent))
			frappe.db.sql("update `tabPurchase Invoice` set branch='{}', cost_center='{}' where name='{}'".format(branch, cost_center, c.parent))

			frappe.db.sql("update `tabConsumed Budget` set cost_center='{}' where po_no='{}'".format(cost_center, c.parent))
			frappe.db.sql("update `tabGL Entry` set cost_center='{}' where voucher_no='{}'".format(cost_center, c.parent))
	
			for d in frappe.db.sql("""select distinct(parent) from `tabPayment Entry Reference` where reference_name='{}' and docstatus=1""".format(c.parent), as_dict=1):
				# print(d.parent)
				frappe.db.sql("update `tabPayment Entry` set cost_center='{}', branch='{}' where name='{}'".format(cost_center, branch, d.parent))
				frappe.db.sql("update `tabGL Entry` set cost_center='{}' where voucher_no='{}'".format(cost_center, d.parent))

def cancel_assets():
	i = 0
	for d in frappe.db.sql(""" Select *
		from `tabAsset` a 
		where a.aid_reference in (select name from `tabAsset Issue Details` where docstatus=2 and name='AID2022060002') 
		and a.docstatus = 2""", as_dict=1):
		i += 1
		print(d.name)
		frappe.delete_doc("Asset", d.name)
		frappe.db.commit()
		# frappe.db.sql("update `tabAsset` set status='Cancelled' where name = '{}'".format(d.name))
	print(i)

def update_user_pwd():
	user_list = frappe.db.sql("select name from `tabUser` where name not in ('Administrator', 'Guest')", as_dict=1)

	c = 1
	for i in user_list:
		print("NAME '{}':  '{}'".format(c,str(i.name)))
		ds = frappe.get_doc("User", i.name)
		ds.new_password = 'erp@2023'
		ds.save(ignore_permissions=1)
		c += 1
	print("DONE")

def rename_merge_child_cost_center():
	with open("/home/frappe/erp/apps/erpnext/erpnext/Renaming of Cost_Center_Final.csv") as f:
		reader = csv.reader(f)
		mylist = list(reader)
		c = 1
		for i in mylist:
			# ge_list = frappe.db.sql(""" select name, center_category, parent_cost_center, is_group from `tabCost Center` where name ="{}" """.format(str(i[0])))
			# ge_list_1 = frappe.db.sql(""" update `tabCost Center` set center_category = 'Domain' where name="{0}" """.format(i[0]))
			# print(c)
			# print("list: {} ".format(str(ge_list)))
			old_branch = frappe.db.get_value("Branch", {"cost_center": str(i[0])}, "name")
			# print("list: {} ".format(str(old_branch)))
			print("Old CC: " + str(i[0]))
			print("New CC: " + str(i[1]))
			print(c,"Renaming Old CC: {}".format(i[0]), "to New CC ID: {}".format(i[1]))
			rd.rename_doc("Cost Center", str(i[0]), str(i[1]), force=False, merge=True, ignore_permissions=True)
			print(c,"Renaming Old Branch: {}".format(old_branch), "to New Branch ID: {}".format(i[1]))
			print("Old Branch: " + str(old_branch))
			print("New Branch: " + str(i[1]))
			rd.rename_doc("Branch", old_branch, str(i[1]), force=False, merge=True, ignore_permissions=True)
			c += 1
	print("done")

def rename_cc():
	c = 1
	for i in frappe.db.sql("select name from `tabCost Center` where is_group=0", as_dict=1):
		print(c)
		frappe.db.sql(""" update `tabCost Center` set cost_center_name={} where name = "{}" and is_group=0 """.format(c, i.name))
		c += 1
	print("DONE")

def assign_parent_child():
	with open("/home/frappe/erp/apps/erpnext/erpnext/Assigning Parent CC_Final.csv") as f:
		reader = csv.reader(f)
		mylist = list(reader)
		c = 1
		for i in mylist:
			# ge_list = frappe.db.sql(""" select name, center_category, parent_cost_center, is_group from `tabCost Center` where name ="{}" """.format(str(i[0])))
			# ge_list = frappe.db.sql(""" select name, center_category, parent_cost_center, is_group from `tabCost Center` where name ="{}" """.format(str(i[1])))
			frappe.db.sql(""" update `tabCost Center` set  parent_cost_center = "{1}" where name="{0}" and is_group=0 """.format(i[0], i[1]))
			print(c)
			# print("list: {} ".format(str(ge_list)))
			c += 1
	print("done")

def rename_merge_programme():
	with open("/home/frappe/erp/apps/erpnext/erpnext/Renaming of Programme to Domain_Final.csv") as f:
		reader = csv.reader(f)
		mylist = list(reader)
		c = 1
		for i in mylist:
			# ge_list = frappe.db.sql(""" select name, center_category, parent_cost_center, is_group from `tabCost Center` where name ="{}" and is_group=1 """.format(i[1]))
			# ge_list_1 = frappe.db.sql(""" update `tabCost Center` set center_category = 'Domain' where name="{0}" """.format(i[0]))
			# print(c)
			# print("list: {} ".format(str(ge_list)))
			print(c,"Renaming Old CC: {}".format(i[0]), "to New CC ID: {}".format(i[2]))
			print(str([i[0]]))
			print(str([i[2]]))
			rd.rename_doc("Cost Center", str(i[0]), str(i[2]), force=False, merge=True, ignore_permissions=True)
			c += 1
	print("done")

def rename_merge_f_cost_center():
	with open("/home/frappe/erp/apps/erpnext/erpnext/Renaming of F Cost Centers_Final.csv") as f:
		reader = csv.reader(f)
		mylist = list(reader)
		c = 1
		for i in mylist:
			# ge_list = frappe.db.sql(""" select name, center_category, parent_cost_center, is_group from `tabCost Center` where name ="{}" """.format(str(i[0])))
			# ge_list_1 = frappe.db.sql(""" update `tabCost Center` set center_category = 'Domain' where name="{0}" """.format(i[0]))
			# print(c)
			# print("list: {} ".format(str(ge_list)))
			old_branch = frappe.db.get_value("Branch", {"cost_center": str(i[0])}, "name")
			print(c,"Renaming Old CC: {}".format(i[0]), "to New CC ID: {}".format(i[1]))
			print("Old CC: " + str(i[0]))
			print("New CC: " + str(i[1]))
			rd.rename_doc("Cost Center", str(i[0]), str(i[1]), force=False, merge=True, ignore_permissions=True)
			
			print(c,"Renaming Old Branch: {}".format(old_branch), "to New Branch ID: {}".format(i[1]))
			print("Old Branch: " + str(old_branch))
			print("New Branch: " + str(i[1]))
			rd.rename_doc("Branch", old_branch, str(i[1]), force=False, merge=True, ignore_permissions=True)
			c += 1
	print("done")

def rename_item_group():
	with open("/home/frappe/erp/apps/erpnext/erpnext/Renaming of Item Group.csv") as f:
		reader = csv.reader(f)
		mylist = list(reader)
		c = 1
		for i in mylist:
			# ge_list = frappe.db.sql(""" select name, is_group from `tabItem Group` where name ="{}" """.format(str(i[0])))
			# print(c)
			# print("list: {} ".format(str(ge_list)))
			print(c,"Renaming Old IGN: {}".format(i[0]), "to New IGN ID: {}".format(i[1]))
			rd.rename_doc("Item Group", str(i[0]), str(i[1]), force=False, merge=True, ignore_permissions=True)
			c += 1
	print("done")

def rename_item_sub_group():
	with open("/home/frappe/erp/apps/erpnext/erpnext/Renaming-of-Item-Sub-Group.csv") as f:
		reader = csv.reader(f)
		mylist = list(reader)
		c = 1
		for i in mylist:
			# ge_list = frappe.db.sql(""" select name, item_sub_group from `tabItem Sub Group` where name ="{}" """.format(str(i[1])))
			# print(c)
			# print("list: {} ".format(str(ge_list)))
			# check = frappe.db.sql(""" select name from `tabItem Sub Group` where exists (select name from `tabItem Sub Group` where name="{}") """.format(str(i[1]), as_dict=1))
			# if check:
			# 	print(c,"Renaming Old ISGN: {}".format(i[0]), "to New ISGN ID: {}".format(i[1]))
			# 	rd.rename_doc("Item Sub Group", str(i[0]), str(i[1]), force=False, merge=True, ignore_permissions=True)
			# else:
			# 	print(c,"Renaming Old ISGN: {}".format(i[0]), "to New ISGN ID: {}".format(i[1]))
			# 	rd.rename_doc("Item Sub Group", str(i[0]), str(i[1]), force=False, merge=False, ignore_permissions=True)
			
			frappe.db.sql(""" update `tabItem Sub Group` set item_group="{1}" where item_sub_group = "{0}" """.format(str(i[1]), str(i[2])))
			# mylist = frappe.db.sql(""" select name, item_sub_group from `tabItem Sub Group` where item_sub_group = "{0}" """.format(str(i[1])))
			print(c)
			# print(mylist)
			c += 1
	
	print("done")

def update_SE_GL():
	with open("/home/frappe/erp/apps/erpnext/erpnext/Rename Gl - SE.csv") as f:
		reader = csv.reader(f)
		mylist = list(reader)
		c = 1
		for i in mylist:
			frappe.db.sql("update `tabGL Entry` set account ='{0}' where voucher_no='{1}' and account='{2}'".format(i[2], i[1], i[0]))
			# ge_list = frappe.db.sql("select voucher_type, voucher_no, account from `tabGL Entry`where voucher_no='{}' and account='{}'".format(i[1], i[0]))
			frappe.db.sql("update `tabStock Entry` se, `tabStock Entry Detail` sed  set sed.expense_account = '{0}' where se.name=sed.parent and se.name='{1}' and sed.expense_account='{2}'".format(i[2], i[1], i[0]))
			# ge_list = frappe.db.sql("select se.name, sed.expense_account from `tabStock Entry` se, `tabStock Entry Detail` sed where se.name=sed.parent and se.name='{}' and sed.expense_account='{}'".format(i[1], i[0]))
			print(c)
			# print("list: {} ".format(str(ge_list)))
			c += 1
	print("done")

def update_DP_GL():
	with open("/home/frappe/erp/apps/erpnext/erpnext/Rename GL-DP.csv") as f:
		reader = csv.reader(f)
		mylist = list(reader)
		c = 1
		for i in mylist:
			frappe.db.sql("update `tabGL Entry` set account ='{0}' where voucher_no='{1}' and account='{2}'".format(i[2], i[1], i[0]))
			# ge_list = frappe.db.sql("select voucher_type, voucher_no, account from `tabGL Entry`where voucher_no='{}' and account='{}'".format(i[1], i[0]))
			frappe.db.sql("update `tabDirect Payment` dp, `tabDirect Payment Item` dpi  set dpi.account = '{0}' where dp.name=dpi.parent and dp.name='{1}' and dpi.account='{2}'".format(i[2], i[1], i[0]))
			# ge_list = frappe.db.sql("select dp.name, dpi.account from `tabDirect Payment` dp, `tabDirect Payment Item` dpi where dp.name=dpi.parent and dp.name='{}' and dpi.account='{}'".format(i[1], i[0]))
			print(c)
			# print("list: {} ".format(str(ge_list)))
			c += 1
	print("done")

def update_JE_GL():
	with open("/home/frappe/erp/apps/erpnext/erpnext/Rename GL - JE.csv") as f:
		reader = csv.reader(f)
		mylist = list(reader)
		c = 1
		for i in mylist:
			frappe.db.sql("update `tabGL Entry` set account ='{0}' where voucher_no='{1}' and account='{2}'".format(i[2], i[1], i[0]))
			# ge_list = frappe.db.sql("select voucher_type, voucher_no, account from `tabGL Entry`where voucher_no='{}' and account='{}'".format(i[1], i[0]))
			frappe.db.sql("update `tabJournal Entry` je, `tabJournal Entry Account` jea  set jea.account = '{0}' where je.name=jea.parent and je.name='{1}' and jea.account='{2}'".format(i[2], i[1], i[0]))
			# ge_list = frappe.db.sql("select je.name, jea.account from `tabJournal Entry` je, `tabJournal Entry Account` jea where je.name=jea.parent and je.name='{}' and jea.account='{}'".format(i[1], i[0]))
			print(c)
			# print("list: {} ".format(str(ge_list)))
			c += 1
	print("done")

def update_cc():
    count=0
    for d in frappe.db.sql("""select * from `tabCost Center` where branch_created = 1""", as_dict=1):
        count += 1
        doc = frappe.get_doc("Cost Center", d.name)
        doc.center_category = 'Course'
        doc.save()
    
    print(count)

def delete_cost_center():
	with open("/home/frappe/erp/apps/erpnext/erpnext/CC to delete.csv") as f:
		reader = csv.reader(f)
		mylist = list(reader)
		c = 1
		for i in mylist:
			print(c)
			branch  = frappe.db.get_value("Branch", {"cost_center": i[1]}, "name")
			frappe.delete_doc("Cost Center", i[1])
			frappe.delete_doc("Branch", branch)
			frappe.db.commit()
			c += 1
	print("done")

def cancel_asset_am_jv():
	i=0
	# for asset in frappe.get_list("Asset", filters={"is_existing_asset": 1, "posting_date":"2023-03-17", "owner":"pema.dhendup@thimphutechpark.bt"}):
	# 	i+=1
	# 	asset_name = str(asset.name)
	# 	doc = frappe.get_doc("Asset Movement Item", {"asset":asset_name})
	# 	if doc.parent:
	# 		am_doc = frappe.get_doc("Asset Movement", doc.parent)
	# 		am_doc.cancel()
	# 		print("cancelled AM: " + am_doc.name)
	# 		frappe.delete_doc("Asset Movement", am_doc.name)
	# 		frappe.db.commit()

	# 	for d in frappe.get_list("Journal Entry Account", filters={"reference_type":"Asset", "reference_name":asset_name}, fields=["parent"], distinct="parent"):
	# 		if d.parent:
	# 			jv_doc = frappe.get_doc("Journal Entry", d.parent)
	# 			jv_doc.cancel()
	# 			print("JV Cancelled: " + jv_doc.name)
	# 			frappe.db.commit()

	# 	asset_doc = frappe.get_doc("Asset", asset_name)
	# 	asset_doc.cancel()
	# 	frappe.db.commit()

	# for jv in frappe.get_list("Journal Entry",  filters={"docstatus": 2, "posting_date":"2023-03-17", "owner":"pema.dhendup@thimphutechpark.bt"}):
	# 	i+=1
	# 	frappe.delete_doc("Journal Entry", jv.name)
	# 	frappe.db.commit()

	for asset in frappe.get_list("Asset", filters={"is_existing_asset": 1, "posting_date":"2023-03-17", "owner":"pema.dhendup@thimphutechpark.bt", "docstatus": 2}):
		i += 1
		# frappe.delete_doc("Asset", asset.name)
		# frappe.db.commit()

	print(i)

def update_ba():
	i=0
	for a in frappe.db.sql("select * from `tabPol Advance` where docstatus=1 and is_opening=0", as_dict=True):
		i+=1
		# print(a.business_activity +" "+ a.journal_entry)
		frappe.db.sql("update `tabJournal Entry Account` set business_activity='{}' where parent='{}'".format(a.business_activity, a.journal_entry))
		if frappe.db.get_value("Journal Entry", a.journal_entry, "docstatus"):
			# print("JE sumitted: " + a.journal_entry)
			frappe.db.sql("update `tabCommitted Budget` set business_activity='{}' where reference_no='{}'".format(a.business_activity, a.journal_entry))
			frappe.db.sql("update `tabConsumed Budget` set business_activity='{}' where reference_no='{}'".format(a.business_activity, a.journal_entry))
			frappe.db.sql("update `tabGL Entry` set business_activity='{}' where voucher_no='{}'".format(a.business_activity, a.journal_entry))
		print(i)

def update_mr_ba():
	i=0
	for a in frappe.db.sql("select * from `tabMaterial Request` where branch='De-suung Headquarter'", as_dict=1):
		i+=1
		print(a.business_activity +" - "+ str(a.docstatus))
		if a.docstatus == 1:
			cb_name = frappe.db.get_value("Committed Budget", {"reference_no": a.name}, "name")
			ba_activity = frappe.db.get_value("Committed Budget", {"reference_no": a.name}, "business_activity")
			if cb_name and a.business_activity != ba_activity:
				print(str(cb_name))
				frappe.db.sql("update `tabCommitted Budget` set business_activity='{}' where reference_no='{}'".format(a.business_activity, a.name))
				print(i)

def update_pi_ba():
	j=i=0
	for a in frappe.db.sql("select * from `tabPurchase Invoice` where branch='De-suung Headquarter'", as_dict=1):
		i+=1
		print(a.business_activity +" - "+ str(a.docstatus))
		if a.docstatus == 1:
			cb_name = frappe.db.get_value("Consumed Budget", {"reference_no": a.name}, "name")
			ba_activity = frappe.db.get_value("Consumed Budget", {"reference_no": a.name}, "business_activity")
			if cb_name and a.business_activity != ba_activity:
				j+=1
				print(str(cb_name))
				print("J- "+ str(j))
				frappe.db.sql("update `tabCommitted Budget` set business_activity='{}' where reference_no='{}'".format(a.business_activity, a.name))
				frappe.db.sql("update `tabConsumed Budget` set business_activity='{}' where reference_no='{}'".format(a.business_activity, a.name))
		print(i)

def cancel_payment_ledger():
	i=0
	for a in frappe.db.sql("select * from `tabPayment Ledger Entry` where voucher_no='JEJV230300053'", as_dict=1):
		i += 1
		# print(a.against_voucher_no)
		doc = frappe.get_doc("Payment Ledger Entry", a.name)
		doc.cancel()
		frappe.db.commit()
	print(i)

def update_clearing_acc():
	count=0
	for d in frappe.db.sql("""select je.name jv_name, jea.account jea_account, jea.name jea_name from `tabJournal Entry` je, `tabJournal Entry Account` jea 
			where jea.parent=je.name and je.voucher_type='Journal Entry' and jea.account = '116001 - Stock Assets - DS'
			and exists (select 1 from tabAsset a where a.name = jea.reference_name and a.is_existing_asset=1) limit 1000""", as_dict=1):
		print(d.jv_name, d.jea_name, d.jea_account)
		count += 1
		# frappe.db.sql("update `tabJournal Entry Account` set account='130001 - Clearing Account - DS' where name='{0}' and account='116001 - Stock Assets - DS' and parent='{1}'".format(d.jea_name, d.jv_name))
		# frappe.db.sql("update `tabGL Entry` set account='130001 - Clearing Account - DS' where voucher_no='{0}' and account='116001 - Stock Assets - DS'".format(d.jv_name))

	print(count)

def update_budget_cc():
	""" update journal entry trans """
	count = 0
	# for d in frappe.db.sql("select distinct reference_no from `tabCommitted Budget` where reference_type='Journal Entry' and cost_center='Other Domain - DS'", as_dict=1):
	# 	frappe.db.sql("delete from `tabCommitted Budget` where reference_no='{}'".format(d.reference_no))
	# 	frappe.db.sql("delete from `tabConsumed Budget` where reference_no='{}'".format(d.reference_no))
	# 	for args in frappe.db.sql("select * from `tabJournal Entry Account` where parent='{}'".format(d.reference_no), as_dict=1):
	# 		account_types = [d.account_type for d in frappe.get_all("Budget Settings Account Types", fields='account_type')]
	# 		if frappe.db.get_value("Account", args.account, "account_type") in account_types:
	# 			count += 1
	# 			#Commit Budget
	# 			cc_doc = frappe.get_doc("Cost Center", args.cost_center)
	# 			budget_cost_center = cc_doc.budget_cost_center if cc_doc.use_budget_from_parent else args.cost_center
				
	# 			bud_obj = frappe.get_doc({
	# 				"doctype": "Committed Budget",
	# 				"account": args.account,
	# 				"cost_center": budget_cost_center,
	# 				"project": args.project,
	# 				"reference_type": args.parenttype,
	# 				"reference_no": args.parent,
	# 				"reference_date": frappe.db.get_value("Journal Entry", args.parent, "posting_date"),
	# 				"amount": flt(args.debit_in_account_currency) - flt(args.credit_in_account_currency),
	# 				"company": 'De-suung',
	# 				"closed": 1,
	# 				"business_activity": args.business_activity,
	# 			})
	# 			bud_obj.flags.ignore_permissions=1
	# 			bud_obj.submit()
			
	# 			#Consume Budget
	# 			con_obj = frappe.get_doc({
	# 				"doctype": "Consumed Budget",
	# 				"account": args.account,
	# 				"cost_center": budget_cost_center,
	# 				"project": args.project,
	# 				"reference_type": args.parenttype,
	# 				"reference_no": args.parent,
	# 				"reference_date": frappe.db.get_value("Journal Entry", args.parent, "posting_date"),
	# 				"amount": flt(args.debit_in_account_currency) - flt(args.credit_in_account_currency),
	# 				"company": 'De-suung',
	# 				"com_ref": bud_obj.name,
	# 				"business_activity": args.business_activity,
	# 			})
	# 			con_obj.flags.ignore_permissions=1
	# 			con_obj.submit()
	
	""" update Purchase invoice trans """
	# for a in frappe.db.sql("select distinct reference_no from `tabCommitted Budget` where reference_type='Purchase Invoice' ", as_dict=1):
	# 	frappe.db.sql("delete from `tabCommitted Budget` where reference_no='{}'".format(a.reference_no))
	# 	frappe.db.sql("delete from `tabConsumed Budget` where reference_no='{}'".format(a.reference_no))

	# 	for item in frappe.db.sql("select * from `tabPurchase Invoice Item` where parent='{}'".format(a.reference_no), as_dict=1):
	# 		bud_acc_dtl = frappe.get_doc("Account", item.expense_account)
	# 		if bud_acc_dtl.account_type in ("Fixed Asset", "Expense Account"):
	# 			count += 1
	# 			cc_doc = frappe.get_doc("Cost Center", item.cost_center)
	# 			budget_cost_center = cc_doc.budget_cost_center if cc_doc.use_budget_from_parent else item.cost_center

	# 			bud_obj = frappe.get_doc({
	# 				"doctype": "Committed Budget",
	# 				"account": item.expense_account,
	# 				"cost_center": budget_cost_center,
	# 				"project": item.project,
	# 				"reference_type": item.parenttype,
	# 				"reference_no": item.parent,
	# 				"reference_date": frappe.db.get_value("Purchase Invoice", item.parent,"posting_date"),
	# 				"company": 'De-suung',
	# 				"amount": flt(item.amount,2),
	# 				"reference_id": item.name,
	# 				"item_code": item.item_code,
	# 				"closed":1,
	# 				"business_activity": frappe.db.get_value("Purchase Invoice", item.parent,"business_activity"),
	# 			})
	# 			bud_obj.flags.ignore_permissions=1
	# 			bud_obj.submit()
	# 			commited_budget_id = bud_obj.name

	# 			consume = frappe.get_doc({
	# 				"doctype": "Consumed Budget",
	# 				"account": item.expense_account,
	# 				"cost_center": budget_cost_center,
	# 				"project": item.project,
	# 				"reference_type": item.parenttype,
	# 				"reference_no": item.parent,
	# 				"reference_date": frappe.db.get_value("Purchase Invoice", item.parent,"posting_date"),
	# 				"company": 'De-suung',
	# 				"amount": flt(item.amount,2),
	# 				"reference_id": item.name,
	# 				"item_code": item.item_code,
	# 				"com_ref": commited_budget_id,
	# 				"business_activity": frappe.db.get_value("Purchase Invoice", item.parent,"business_activity"),
	# 			})
	# 			consume.flags.ignore_permissions=1
	# 			consume.submit()

	""" MR """
	for a in frappe.db.sql("select distinct reference_no from `tabCommitted Budget` where reference_type='Material Request' and cost_center='Other Domain - DS'", as_dict=1):
		cc_doc = frappe.get_doc("Cost Center", frappe.db.get_value("Material Request",a.reference_no, "cost_center"))
		budget_cost_center = cc_doc.budget_cost_center

		for d in frappe.db.sql("select * from `tabCommitted Budget` where reference_no='{}'".format(a.reference_no), as_dict=1):
			frappe.db.sql("update `tabCommitted Budget` set cost_center='{0}' where name='{1}'".format(budget_cost_center, d.name))
			if frappe.db.get_value("Consumed Budget", {"com_ref": d.name}, "docstatus"):
				con_id = frappe.db.get_value("Consumed Budget", {"com_ref": d.name}, "name")
				frappe.db.sql("update `tabConsumed Budget` set cost_center='{0}' where name='{1}'".format(budget_cost_center, con_id))
		print(budget_cost_center)
		count += 1
	print(count)
	
def delete_consumed_bud():
	count = 0
	for a in frappe.db.sql("select distinct(pi.name) as pi_name from `tabPurchase Invoice` pi where docstatus=2 and exists (select 1 from `tabConsumed Budget` where reference_type='Purchase Invoice' and reference_no=pi.name)", as_dict=1):
		count += 1
		# print(str(a.pi_name))
		frappe.db.sql("delete from `tabConsumed Budget` where reference_type='Purchase Invoice' and reference_no='{}'".format(str(a.pi_name)))
	print(count)

def consume_budget():
	self = frappe.get_doc("Purchase Invoice", "PI23070015")
	for item in self.get("items"):
		# print(item.item_code)
		expense, cost_center = item.expense_account, item.cost_center
		if item.po_detail:
			expense, cost_center = frappe.db.get_value("Purchase Order Item", item.po_detail, ["expense_account", "cost_center"])
		else:
			if frappe.db.get_value("Item", item.item_code, "is_fixed_asset"):
				expense = get_asset_category_account('fixed_asset_account', item=item.item_code,
																company=self.company)
		budget_cost_center = budget_account = ""
		bud_acc_dtl = frappe.get_doc("Account", expense)
		if bud_acc_dtl.centralized_budget:
			budget_cost_center = bud_acc_dtl.cost_center
		else:
			#check Budget Cost for child cost centers
			cc_doc = frappe.get_doc("Cost Center", cost_center)
			budget_cost_center = cc_doc.budget_cost_center if cc_doc.use_budget_from_parent else cost_center
		if expense:
			if bud_acc_dtl.account_type in ("Fixed Asset", "Expense Account"):
				reference_date = commited_budget_id = None
				amount = item.base_net_amount if flt(item.base_net_amount,2) else flt(item.base_amount,2)
				if frappe.db.get_single_value("Budget Settings", "budget_commit_on") == "Material Request":
					mr_name = frappe.db.get_value("Purchase Order Item", {"parent":item.purchase_order, "item_code":item.item_code}, "material_request")
					mr_child_id = frappe.db.get_value("Material Request Item", {"parent": mr_name, "item_code": item.item_code}, "name")
					if mr_name:
						reference_date = frappe.db.get_value("Material Request", mr_name, "transaction_date") if mr_name else self.posting_date
						commited_budget_id = frappe.db.get_value("Committed Budget", {"reference_type":"Material Request", "reference_no": mr_name, "reference_id": mr_child_id}, "name")
				else:
					reference_date = frappe.db.get_value("Purchase Order", item.purchase_order, "transaction_date") if item.purchase_order else self.posting_date
					commited_budget_id = frappe.db.get_value("Committed Budget", {"reference_type":"Purchase Order", "reference_no":item.purchase_order, "reference_id":item.po_detail},"name")
				args = frappe._dict({
						"account": expense,
						"cost_center": budget_cost_center,
						"project": item.project,
						"posting_date": self.posting_date,
						"company": self.company,
						"amount": flt(amount,2),
						"business_activity": self.business_activity,
					})
				if not commited_budget_id:					
					validate_expense_against_budget(args)
					#Commit Budget
					bud_obj = frappe.get_doc({
						"doctype": "Committed Budget",
						"account": expense,
						"cost_center": budget_cost_center,
						"project": item.project,
						"reference_type": self.doctype,
						"reference_no": self.name,
						"reference_date": self.posting_date,
						"company": self.company,
						"amount": flt(amount,2),
						"reference_id": item.name,
						"item_code": item.item_code,
						"company": self.company,
						"closed":1,
						"business_activity": self.business_activity,
					})
					bud_obj.flags.ignore_permissions=1
					bud_obj.submit()
					commited_budget_id = bud_obj.name

				consume = frappe.get_doc({
					"doctype": "Consumed Budget",
					"account": expense,
					"cost_center": budget_cost_center,
					"project": item.project,
					"reference_type": self.doctype,
					"reference_no": self.name,
					"reference_date": reference_date if reference_date else self.posting_date,
					"company": self.company,
					"amount": flt(amount,2),
					"reference_id": item.name,
					"item_code": item.item_code,
					"com_ref": commited_budget_id,
					"business_activity": self.business_activity,
				})
				consume.flags.ignore_permissions=1
				consume.submit()
				com_doc = frappe.get_doc("Committed Budget", commited_budget_id)
				if amount == com_doc.amount and not com_doc.closed:
					frappe.db.sql("update `tabCommitted Budget` set closed = 1 where name = '{}'".format(commited_budget_id))

				print("commited id: " + str(commited_budget_id) + ":" + "consumed id: " + str(consume.name))

def consumed_budget_jv():
	doc = frappe.get_doc("Journal Entry", "JEBP230900118")
	doc.make_gl_entries()
	frappe.db.commit()

def create_asset_received():
	doc = frappe.get_doc("Purchase Receipt", "PR23080001")
	# doc.update_asset_receive_entries()
	doc.update_stock_ledger()
	doc.make_gl_entries()
	frappe.db.commit()
	print("Done")

def update_gl_240422():
	pass
	li = ['SEMR23090003', "SEMR23080019", "SEMR23090016", "SEMI23090228","SEMR23090014-1","SEMI23090152-1","SEMR23090004","SEMI23080409-1","SEMI23080496","SEMR23090007-1","SEMR23070005","SEMR23060002-1","SEMR23040009","SEMR23040008","SEMI23030654-2","SEMI23030384-4","SEMR23030004","SEMI23030481"]
	for a in li:
		frappe.db.sql("delete from `tabGL Entry` where voucher_no='{}'".format(a))
		doc = frappe.get_doc("Stock Entry", a)
		doc.make_gl_entries()
	print('Done')

def update_cid_did_training():
	for a in frappe.db.sql("select name, desuup_id, desuup_cid from `tabTrainee Details` where desuup_cid like 'DS%'", as_dict=True):
		frappe.db.sql("update `tabTrainee Details` set desuup_id='{}', desuup_cid='{}' where name='{}'".format(a.desuup_cid, a.desuup_id, a.name))
		print(str(a.name)+' '+str(a.desuup_id)+' '+str(a.desuup_cid))