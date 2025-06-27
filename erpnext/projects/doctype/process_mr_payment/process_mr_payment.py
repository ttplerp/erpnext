# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, cint, datetime, get_last_day
from calendar import monthrange
from erpnext.custom_utils import check_budget_available, get_branch_cc

class ProcessMRPayment(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from erpnext.projects.doctype.mr_payment_item.mr_payment_item import MRPaymentItem
		from frappe.types import DF

		amended_from: DF.Link | None
		branch: DF.Link
		cost_center: DF.Link
		deduction: DF.Currency
		employee_type: DF.Literal["", "Muster Roll Employee"]
		fiscal_year: DF.Link | None
		from_date: DF.Date | None
		gross_amount: DF.Currency
		items: DF.Table[MRPaymentItem]
		month: DF.Literal["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
		monthyear: DF.Literal["201701", "201702", "201703", "201704", "201705", "201706", "201707", "201708", "201709", "201710", "201711", "201712", "201801", "201802", "201803", "201804", "201805", "201806", "201807", "201808", "201809", "201810", "201811", "201812", "201901", "201902", "201903", "201904", "201905", "201906", "201907", "201908", "201909", "201910", "201911", "201912", "202001", "202002", "202003", "202004", "202005", "202006", "202007", "202008", "202009", "202010", "202011", "202012", "202101", "202102", "202103", "202104", "202105", "202106", "202107", "202108", "202109", "202110", "202111", "202112", "202201", "202202", "202203", "202204", "202205", "202206", "202207", "202208", "202209", "202210", "202211", "202212", "202301", "202302", "202303", "202304", "202305", "202306", "202307", "202308", "202309", "202310", "202311", "202312", "202401", "202402", "202403", "202404", "202405", "202406", "202407", "202408", "202409", "202410", "202411", "202412", "202501", "202502", "202503", "202504", "202505", "202506", "202507", "202508", "202509", "202510", "202511", "202512", "202601", "202602", "202603", "202604", "202605", "202606", "202607", "202608", "202609", "202610", "202611", "202612", "202701", "202702", "202703", "202704", "202705", "202706", "202707", "202708", "202709", "202710", "202711", "202712"]
		ot_amount: DF.Currency
		payment_jv: DF.Data | None
		posting_date: DF.Date
		project: DF.Link | None
		to_date: DF.Date | None
		total_health_amount: DF.Currency
		total_overall_amount: DF.Currency
		wages_amount: DF.Currency
	# end: auto-generated types
	def validate(self):
		month = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"].index(self.month) + 1
		month = str(month) if cint(month) > 9 else str("0" + str(month))
		self.monthyear = str(self.fiscal_year)+str(month)
		total_days = monthrange(cint(self.fiscal_year), cint(month))[1]	

	def on_submit(self):
		# self.check_budget()
		self.post_journal_entry()
		self.bank_journal_entry()

	def before_cancel(self):
		self.ignore_linked_doctypes = ("GL Entry", "Payment Ledger Entry")
		cl_status = frappe.db.get_value("Journal Entry", self.payment_jv, "docstatus")
		if cl_status and cl_status != 2:
			frappe.throw("You need to cancel the journal entry related to this payment first!")
		
		self.db_set('payment_jv', "")
		
	def check_budget(self):
			budget_error= []
			overtime_account = frappe.db.get_value ("Company", self.company, "mr_overtime_account")
			wages_account = frappe.db.get_value ("Company", self.company, "mr_expense_account")
			error = check_budget_available(self.cost_center, overtime_account, self.posting_date, self.ot_amount, False)
			if error:					
				budget_error.append(error)

			errors= check_budget_available(self.cost_center, wages_account, self.posting_date, self.wages_amount, throw_error = False)
			if errors:
				budget_error.append(errors)
			if budget_error:
				for e in budget_error:
					frappe.msgprint(str(e))
					frappe.throw("", title="Insufficient Budget")


	def duplicate_entry_check(self, employee, employee_type, idx):
			pl = frappe.db.sql("""
                                select
                                        i.name,
                                        i.parent,
                                        i.docstatus,
                                        i.person_name,
                                        i.employee
                                from `tabMR Payment Item` i, `tabProcess MR Payment` m
                                where i.employee = '{0}'
                                and i.employee_type = '{1}'
                                and i.fiscal_year = '{2}'
                                and i.month = '{3}'
                                and m.docstatus in (0,1)
                                and i.parent != '{4}'
				and i.parent = m.name
				and m.cost_center = '{5}'
                        """.format(employee, employee_type, self.fiscal_year, self.month, self.name, self.cost_center), as_dict=1)

			for l in pl:
					msg = 'Payment already processed for `{2}({3})`<br>RowId#{1}: Reference# <a href="#Form/Process MR Payment/{0}">{0}</a>'.format(l.parent, idx, l.person_name, l.employee)
					frappe.throw(_("{0}").format(msg), title="Duplicate Record Found")                        
                
	#Populate Budget Accounts with Expense and Fixed Asset Accounts
	def load_employee(self):
		#frappe.throw("hi")
		if self.employee_type == "GEP Employee":
			query = "select 'GEP Employee' as employee_type, name as employee, person_name, id_card, rate_per_day as daily_rate, rate_per_hour as hourly_rate from `tabGEP Employee` where status = 'Active'"
		elif self.employee_type == "Muster Roll Employee":
			#frappe.throw("1")
			query = "select 'Muster Roll Employee' as employee_type, r.name as employee, r.person_name, r.id_card, m.rate_per_day as daily_rate, m.rate_per_hour as hourly_rate from `tabMuster Roll Employee` r, tabMusterroll m where r.status = 'Active' and r.name=m.parent order by m.rate_per_day desc"
		else:
			frappe.throw("Select employee record first!")
	
		if not self.branch:
			frappe.throw("Set Branch before loading employee data")
		else:
			query += " and branch = \'" + str(self.branch) + "\'"	
			
		entries = frappe.db.sql(query, as_dict=True)
		if not entries:
			frappe.msgprint("No Attendance and Overtime Record Found")

		self.set('items', [])
		frappe.throw(str(entries))
		for d in entries:
			row = self.append('items', {})
			row.update(d)

	def bank_journal_entry(self):
		expense_bank_account  = frappe.db.get_value("Branch", self.branch, "expense_bank_account")
		if not expense_bank_account:
			frappe.throw("Setup Default Salary Payable Account in Branch <b>{}</b>".format(self.branch))
		payable_account = frappe.db.get_value("Company", self.company, "mr_payable_account")		
		if self.employee_type == "Muster Roll Employee":
			if not expense_bank_account:
				frappe.throw("Setup Default Expense Bank Account in Branch".format(self.branch))
			deduction_account = frappe.db.get_value("Company", self.company, "mr_deduction_account")
			if not deduction_account and self.deduction:
				frappe.throw("Setup Mess Deduction Account in Company Settings")
		else:
			frappe.throw("Invalid Employee Type")

		je = frappe.new_doc("Journal Entry")
		je.flags.ignore_permissions = 1 
		je.title = "Payment for " + self.employee_type  + " (" + self.branch + ")"
		je.voucher_type = 'Bank Entry'
		je.naming_series = 'Bank Payment Voucher'
		je.remark = 'Payment against : ' + self.name
		je.posting_date = self.posting_date
		je.branch = self.branch
		total_amount = self.total_overall_amount

		je.append("accounts", {
				"account": payable_account,
				"cost_center": self.cost_center,
				"reference_type": "Process MR Payment",
				"reference_name": self.name,
				"debit_in_account_currency": flt(self.total_overall_amount),
				"debit": flt(self.total_overall_amount),
			})

		if self.deduction:	
			je.append("accounts", {
					"account": deduction_account,
					"reference_type": "Process MR Payment",
					"reference_name": self.name,
					"cost_center": self.cost_center,
					"debit_in_account_currency": flt(self.deduction),
					"debit": flt(self.deduction),
				})

		je.append("accounts", {
				"account": expense_bank_account,
				"cost_center": self.cost_center,
				"credit_in_account_currency": flt(self.gross_amount),
				"credit": flt(self.gross_amount),
			})
			
		# frappe.throw("<pre>{}</pre>".format(frappe.as_json(je.get('accounts'))))
		je.insert()
	
	def post_journal_entry(self):
		expense_bank_account  = frappe.db.get_value("Branch", self.branch, "expense_bank_account")
		payable_account = frappe.db.get_value("Company", self.company, "mr_payable_account")		
		if not expense_bank_account:
			frappe.throw("Setup Default Salary Payable Account in Branch <b>{}</b>".format(self.branch))
			
		if self.employee_type == "Muster Roll Employee":
			ot_account = frappe.db.get_value("Company", self.company, "mr_overtime_account")
			if not ot_account:
				frappe.throw("Setup MR Overtime Account in Company Settings")
			wage_account = frappe.db.get_value("Company", self.company, "mr_expense_account")
			if not wage_account:
				frappe.throw("Setup MR Wages Account in Company Settings")
			deduction_account = frappe.db.get_value("Company", self.company, "mr_deduction_account")
			if not deduction_account and self.deduction:
				frappe.throw("Setup Deduction Account in Company Settings")
		else:
			frappe.throw("Invalid Employee Type")

		je = frappe.new_doc("Journal Entry")
		je.flags.ignore_permissions = 1 
		je.title = "Payment for " + self.employee_type  + " (" + self.branch + ")"
		je.voucher_type = 'Journal Entry'
		je.naming_series = 'Journal Entry'
		je.remark = 'Payment against : ' + self.name
		je.posting_date = self.posting_date
		je.branch = self.branch
		
		if self.ot_amount:	
			je.append("accounts", {
					"account": ot_account,
					"reference_type": "Process MR Payment",
					"reference_name": self.name,
					"cost_center": self.cost_center,
					"debit_in_account_currency": flt(self.ot_amount),
					"debit": flt(self.ot_amount),
				})
		
		if self.wages_amount:
			je.append("accounts", {
				"account": wage_account,
				"reference_type": "Process MR Payment",
				"reference_name": self.name,
				"cost_center": self.cost_center,
				"debit_in_account_currency": flt(self.wages_amount),
				"debit": flt(self.wages_amount) ,
			})

		je.append("accounts", {
				"account": payable_account,
				"cost_center": self.cost_center,
				"credit_in_account_currency": flt(self.total_overall_amount),
				"credit": flt(self.total_overall_amount),
			})
		
		if self.deduction:	
			je.append("accounts", {
					"account": deduction_account,
					"reference_type": "Process MR Payment",
					"reference_name": self.name,
					"cost_center": self.cost_center,
					"credit_in_account_currency": flt(self.deduction),
					"credit": flt(self.deduction),
				})
		# frappe.throw("<pre>{}</pre>".format(frappe.as_json(je.get('accounts'))))
		je.insert()
		je.submit()
		self.db_set("payment_jv", je.name)
			
	@frappe.whitelist()
	def get_records(self, fiscal_year, fiscal_month, cost_center, branch, dn):
		
		''' 
		This method updates the follwoing details for the given month 
			1. `tabAttendance Others`.rate_per_day
			2. `tabOvertime Entry`.rate_per_hour & `tabOvertimeEntry.rate_per_hour_normal`
		'''
		# docname = frappe.get_doc("Process MR Payment", docname)
		month = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"].index(fiscal_month) + 1
		month = str(month) if cint(month) > 9 else str("0" + str(month))

		total_days = monthrange(cint(fiscal_year), cint(month))[1]
		
		from_date = str(fiscal_year) + '-' + str(month) + '-' + str('01')
		to_date   = str(fiscal_year) + '-' + str(month) + '-' + str(total_days)

		data    = []
		
		master  = frappe._dict()
		emp_list = frappe.db.sql("""
			SELECT e.name, e.person_name, e.id_card, e.status, e.designation, 
				e.salary, bank_name AS bank, bank_ac_no AS account_no,e.amount
			FROM `tabMuster Roll Employee` as e
			INNER JOIN `tabMusterroll` mr on mr.parent = e.name
			INNER JOIN 
				(
					SELECT mr_employee
					FROM `tabMuster Roll Attendance`
					WHERE date between '{from_date}' and '{to_date}'
					AND cost_center = '{cost_center}'
					AND status = 'Present'
					AND docstatus = 1
					UNION
					SELECT mr_employee as employee
					FROM `tabMuster Roll Overtime Entry`
					WHERE date between '{from_date}' and '{to_date}'
					AND cost_center = '{cost_center}'
					AND docstatus = 1
				) as r
				ON e.name=r.mr_employee
			WHERE e.status = 'Active'
				AND NOT EXISTS(
						SELECT 1
						FROM `tabMR Payment Item` i, `tabProcess MR Payment` m
						WHERE m.fiscal_year = '{fiscal_year}'
						AND m.month = '{fiscal_month}'
						AND m.docstatus < 2
						AND m.cost_center = '{cost_center}'
						AND m.name != '{dn}'
						AND i.parent = m.name
						AND i.employee = e.name
						AND i.employee_type = 'Muster Roll Employee'
					)
		""".format(fiscal_year=fiscal_year, fiscal_month=fiscal_month,
		dn=dn, cost_center=cost_center, from_date = from_date, to_date = to_date), as_dict=True)
		# frappe.throw(str(emp_list))
		for e in emp_list:
			pay_details=get_pay_details(e.name, fiscal_year, month)
			rate_per_day 		 = flt(pay_details[0]['rate_per_day'])
			rate_per_hour 		 = flt(pay_details[0]['rate_per_hour'])
			rate_per_hour_normal = flt(pay_details[0]['rate_per_hour_normal'])
		

			master.setdefault(e.name, frappe._dict({
				"mr_employee": e.name,
				"person_name": e.person_name,
				"id_card": e.id_card,
				"rate_per_day": rate_per_day,
				"rate_per_hour": rate_per_hour,
				"rate_per_hour_normal": rate_per_hour_normal,
				"designation" : e.designation,
				"account_no" : e.account_no,
				"bank" : e.bank,
				"salary": e.salary,
				"amount":e.amount
			}))
		
				
		rest_list = frappe.db.sql("""
			SELECT mr_employee,
				SUM(number_of_days)     AS number_of_days,
				SUM(number_of_hours_regular)    AS number_of_hours_regular,
				SUM(number_of_hours_special)    AS number_of_hours_special,
				SUM(total_wage)         AS total_wage,
				SUM(total_ot)           AS total_ot,
				{total_days} 			AS noof_days_in_month
			FROM (
				SELECT DISTINCT mr_employee, date, 
				CASE 
					WHEN status = 'Present' THEN 1
					WHEN status = 'Half Day' THEN 0.5
				END AS number_of_days, 0 AS number_of_hours_regular, 0 AS number_of_hours_special,
					IFNULL(rate_per_day,0) AS total_wage, 0 AS total_ot
				FROM `tabMuster Roll Attendance`
				WHERE docstatus = 1
				AND date BETWEEN '{from_date}' AND '{to_date}'
				AND cost_center = '{cost_center}' AND status IN ('Present', 'Half Day')
				UNION ALL
				SELECT DISTINCT mr_employee AS employee, date, 
					0 AS number_of_days, ifnull(number_of_hours_regular,0) AS number_of_hours,
					ifnull(number_of_hours_special,0) AS number_of_hours_special, 0 AS total_wage, 
					(IFNULL(number_of_hours_regular,0) * IFNULL(rate_per_hour_normal,0) + IFNULL(number_of_hours_special,0) * IFNULL(rate_per_hour,0)) AS total_ot	
				FROM `tabMuster Roll Overtime Entry`
				WHERE date BETWEEN '{from_date}' AND '{to_date}'
				AND cost_center = '{cost_center}'
				AND docstatus = 1
			) AS abc
			GROUP BY mr_employee
		""".format(from_date = from_date, to_date = to_date, 
		cost_center = cost_center, total_days = total_days), as_dict=True)
		# frappe.throw(str(rest_list))
		
		total_overall_amount = ot_amount = wages_amount = deduction = 0
		for r in rest_list:
			
			if master.get(r.mr_employee) and (flt(r.total_wage)+flt(r.total_ot)) >=0:
				row = self.append("items", {})
				master[r.mr_employee].update(r)
				row.employee_type 	= "Muster Roll Employee"
				row.employee 		= r.mr_employee
				row.person_name 	= master.get(r.mr_employee).person_name
				row.id_card 		= master.get(r.mr_employee).id_card
				row.fiscal_year 	= self.fiscal_year
				row.month 			= self.month
				row.number_of_days 	= r.number_of_days
				row.number_of_hours = flt(r.number_of_hours_regular)
				row.number_of_hours_special = flt(r.number_of_hours_special)
				row.bank = r.bank
				row.account_no = r.account_no
				row.designation = r.designation

				row.daily_rate 			= flt(master.get(r.mr_employee).rate_per_day)
				row.hourly_rate 		= flt(master.get(r.mr_employee).rate_per_hour)
				row.hourly_rate_normal 	= flt(master.get(r.mr_employee).rate_per_hour_normal)
				row.amount_regular 		= flt(r.number_of_hours_regular) * flt(row.hourly_rate_normal)
				row.amount_special 		= flt(r.number_of_hours_special) * flt(row.hourly_rate)
				row.total_ot_amount 	= flt(r.number_of_hours_regular) * flt(row.hourly_rate_normal) + flt(r.number_of_hours_special) * flt(row.hourly_rate)
				row.total_wage 			= flt(row.daily_rate) * flt(r.number_of_days)
				
				# row.mess_deduction 		= flt(master.get(r.mr_employee).amount, 2)
				row.wage_payable    	= flt(row.total_wage, 2)
				row.total_amount 		= flt(flt(row.total_ot_amount, 2) + flt(row.wage_payable, 2), 2)
				row.net_pay				= flt(flt(row.total_amount, 2) - flt(row.mess_deduction, 2), 2)

				total_overall_amount 	+= flt(row.total_amount, 2)
				ot_amount 			 	+= flt(row.total_ot_amount, 2)
				wages_amount 		 	+= flt(row.wage_payable, 2)
				deduction 			 	+= flt(row.mess_deduction, 2)
			
		self.total_overall_amount 	= flt(total_overall_amount) - flt(deduction)
		self.ot_amount 			 	= flt(ot_amount, 2)
		self.wages_amount 		 	= wages_amount
		self.deduction 			 	= deduction
		self.gross_amount		 	= flt(wages_amount) + flt(ot_amount)
		
def get_pay_details(employee, year, month):
	from_date = "-".join([str(year), str(month), '01'])
	to_date   = str(get_last_day(from_date))

	return  frappe.db.sql("""
			SELECT
				rate_per_day, rate_per_hour, rate_per_hour_normal
			FROM `tabMusterroll`
			WHERE parent = '{employee}'
			
			ORDER BY from_date DESC
			LIMIT 1
		""".format(employee=employee), as_dict = True)

@frappe.whitelist()
def check_if_holiday_overtime_entry(branch, date, fiscal_year = None, fiscal_month = None):
	from datetime import datetime
	is_holiday = 0
	holiday_list = frappe.db.get_value("Branch", branch, "holiday_list")

	holiday_dates = frappe.db.sql("select holiday_date from `tabHoliday` where parent='{}'".format(holiday_list), as_dict=1)

	# date = []
	for holiday_date in holiday_dates:
		if datetime.strptime(str(date),"%Y-%m-%d") == datetime.strptime(str(holiday_date.holiday_date),"%Y-%m-%d"):
			is_holiday = 1
	return is_holiday