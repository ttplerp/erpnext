# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from datetime import date
import calendar
import frappe
from frappe import msgprint, _
from frappe.utils import cint, flt, nowdate, add_days, getdate, fmt_money, add_to_date, DATE_FORMAT, date_diff, get_last_day
from erpnext.accounts.general_ledger import (
	get_round_off_account_and_cost_center,
	make_gl_entries,
	make_reverse_gl_entries,
	merge_similar_entries,
)

from frappe.model.document import Document
from erpnext.controllers.accounts_controller import AccountsController

class DesuupPaySlip(AccountsController):
	def validate(self):
		if self.payment_to != "OJT":
			self.get_mess_advance()
		self.calculate_amount()

	def on_submit(self):
		self.post_journal_entry()
	# 	self.make_gl_entry()
	
	# def on_cancel(self):
	# 	self.make_gl_entry()

	@frappe.whitelist()
	def set_month_dates(self):
		months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
		month = str(int(months.index(self.month_name))+1).rjust(2,"0")

		month_start_date = "-".join([str(date.today().year), month, "01"])
		month_end_date   = get_last_day(month_start_date)

		self.start_date = month_start_date
		self.end_date = month_end_date
		self.month = month

	def get_mess_advance(self):
		# adv_party = ''
		adv_amt = 0
		if self.is_mess_member:
			# adv_party = frappe.db.get_value("Desuup Mess Advance", {'reference_name':self.reference_name, 'month':self.month, 'fiscal_year': self.fiscal_year}, "paid_to")
			adv_list = frappe.db.sql("""
				SELECT t2.amount, t1.paid_to 
				FROM `tabDesuup Mess Advance` t1, `tabDesuup Mess Advance Item` t2 
				WHERE t1.name = t2.parent
				AND t1.reference_name = %s
				AND t2.desuup = %s
				AND t1.docstatus = 1
				AND t1.month = %s
				AND t1.fiscal_year = %s
			""", (self.reference_name, self.desuup, self.month, self.fiscal_year),as_dict=True)

			# Check if the query returns any results and then get the amount
			if adv_list:
				adv_amt = flt(adv_list[0].amount)
				self.advance_party = adv_list[0].paid_to
			else:
				adv_amt = 0  # Or handle it accordingly

		
		# self.advance_party = adv_party 
		# if self.advance_party:
		# 	self.advance_party_name = frappe.db.get_value("Desuup", self.advance_party, "desuup_name")
		self.mess_advance = flt(adv_amt, 2) if adv_amt else 0

	def calculate_amount(self):

		month_start_date = "-".join([str(date.today().year), self.month, "01"])
		month_end_date   = get_last_day(month_start_date)

		days_in_month = calendar.monthrange(month_end_date.year, month_end_date.month)[1]

		if self.payment_to == "Trainee":
			monthly_stipend = frappe.db.get_single_value("Desuup Settings", "monthly_stipend")
			if not monthly_stipend:
				frappe.throw("Please set monthly Stipend anount in Desuup Settings")
				
			stipend = flt(monthly_stipend)/flt(days_in_month)
			adv_amt = flt(self.mess_advance)/flt(days_in_month)

			self.monthly_stipend = flt(monthly_stipend, 2)

			self.stipend_amount = flt(stipend * self.total_days_present, 2)
			self.advance_amount_used = flt(adv_amt * self.total_days_present, 2)

			self.refundable_amount = flt(self.mess_advance, 2) - flt(self.advance_amount_used)
			
			self.total_amount = flt(self.stipend_amount, 2) - flt(self.advance_amount_used, 2)

			if self.total_amount < self.deduction_amount:
				self.net_pay = 0
			else:
				self.net_pay = flt(self.total_amount - self.deduction_amount, 2)

		elif self.payment_to == "OJT":
			self.monthly_pay = flt(frappe.db.get_value("Deployment Type", self.deployment_type, 'amount'))
			if self.monthly_pay <= 0:
				frappe.throw("Monthly payment for deployment type {} cannot be 0 or less".format(frappe.bold(self.deployment)))
			self.total_amount = self.monthly_pay
			if self.total_amount < self.deduction_amount:
				self.net_pay = 0
			else:
				self.net_pay = flt(self.total_amount - self.deduction_amount, 2)

	def make_gl_entry(self):
		gl_entries = []
		self.make_party_gl_entry(gl_entries)
		self.make_expense_gl_entry(gl_entries)
		gl_entries = merge_similar_entries(gl_entries)
		make_gl_entries(gl_entries, update_outstanding="No", cancel=self.docstatus == 2)

	def make_party_gl_entry(self, gl_entries):
		credit_account = frappe.db.get_single_value("Desuup Settings", "stipend_payable_account")
		if not credit_account:
			frappe.throw("Please set Stipend Payable Account")
		if flt(self.net_pay) > 0:
			gl_entries.append(
				self.get_gl_dict({
					"account": credit_account,
					"credit": flt(self.net_pay, 2),
					"credit_in_account_currency": flt(self.net_pay, 2),
					"against_voucher": self.name,
					"party_type": "Desuup",
					"party": self.desuup,
					"against_voucher_type": self.doctype,
					"cost_center": self.cost_center,
					"voucher_type":self.doctype,
					"voucher_no":self.name,
				}, self.currency)
			) 

	def make_expense_gl_entry(self, gl_entries):
		debit_account = frappe.db.get_single_value("Desuup Settings", "stipend_expense_account")
		if not debit_account:
			frappe.throw("Please set Stipend Expense Account")
		if flt(self.net_pay) > 0:
			gl_entries.append(
				self.get_gl_dict({
					"account": debit_account,
					"debit": flt(self.net_pay, 2),
					"debit_in_account_currency": flt(self.net_pay, 2),
					"against_voucher": self.name,
					"party_type": "Desuup",
					"party": self.desuup,
					"against_voucher_type": self.doctype,
					"cost_center": self.cost_center,
					"voucher_type":self.doctype,
					"voucher_no":self.name,
				}, self.currency)
			) 

	@frappe.whitelist()
	def get_desuup_attendance(self):
		days = 0
		self.set("attendances", [])

		query = """
			SELECT a.name as desuup_attendance, a.status, a.attendance_date
			FROM `tabDesuup Attendance` a
			WHERE a.docstatus = 1
			AND a.desuup = %s
			AND a.attendance_date BETWEEN %s AND %s
			AND a.status IN ('Present', 'Half Day')
		"""

		# Execute the query with parameters
		attendance_records = frappe.db.sql(query, (self.desuup, self.start_date, self.end_date), as_dict=True)

		for record in attendance_records:
			if record.status == "Present":
				days += 1
			elif record.status == "Half Day":
				days += 0.5
			self.append("attendances", record)

		self.total_days_present = days

		if len(self.attendances) == 0:
			frappe.msgprint(
				"No attendance found for month {}".format(frappe.bold(self.month)),
				raise_exception=True
			)

	def post_journal_entry(self):
		if self.refundable_amount == 0:
			return

		accounts = []
		bank_account = frappe.db.get_value("Company", self.company, "default_bank_account")
		credit_account = frappe.db.get_single_value("Desuup Settings", "mess_advance_account")
		if not bank_account:
			frappe.throw("Set default bank account in company {}".format(frappe.bold(self.company)))
		
		accounts.append({
				"account": credit_account,
				"credit_in_account_currency": flt(self.refundable_amount,2),
				"cost_center": self.cost_center,
				"party_check": 1,
				"party_type": "Employee",
				"party": self.advance_party,
				"party_name": self.advance_party_name,
				"reference_type": self.doctype,
				"reference_name": self.name,
			})

		accounts.append({
			"account": bank_account,
			"debit_in_account_currency": flt(self.refundable_amount,2),
			"cost_center": self.cost_center,
		})
		je = frappe.new_doc("Journal Entry")
		je.flags.ignore_permission = 1
		je.update({
			"doctype": "Journal Entry",
			"branch": self.branch,
			"posting_date": self.posting_date,
			"voucher_type": "Bank Entry",
			"naming_series": "Bank Receipt Voucher",
			"company": self.company,
			"reference_doctype":self.doctype,
			"reference_name":self.name,
			"accounts": accounts
		})
		je.insert()
		self.db_set('journal_entry', je.name)
		frappe.msgprint(_('Journal Entry {0} posted to accounts').format(frappe.get_desk_link("Journal Entry",je.name)))			 
