from __future__ import unicode_literals
import frappe
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
import csv

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
		ds.new_password = 'dsp@2022'
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