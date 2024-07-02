# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
import calendar
import frappe.translate
from datetime import date
from frappe import _
from frappe.utils import cint, flt, nowdate, add_days, getdate, fmt_money, add_to_date, DATE_FORMAT, date_diff, get_last_day
from frappe.model.document import Document


class DesuupMessAdvance(Document):
	def validate(self):
		self.validate_month_entry()
		self.validate_duplicate_desuup_entry()
		self.validate_is_exists_in_training_management()
		# self.validate_duplicate_monthly_advance()
		self.calcualte_mess_amount()
		self.calculate_total_advance()

	def on_submit(self):
		self.db_set("payment_status", "Unpaid")
		self.post_journal_entry()

	def calcualte_mess_amount(self):
		month_start_date, month_end_date = self.get_start_end_month_date()

		from_date = getdate(self.from_date)
		to_date = getdate(self.to_date)

		mess_amt = frappe.db.get_single_value("Desuup Settings", "mess_advance")
		mess_adv_amt = 0

		if from_date.day == 1 and to_date.day == calendar.monthrange(month_end_date.year, month_end_date.month)[1]:
			mess_adv_amt = mess_amt
		else:
			days_in_month = calendar.monthrange(month_end_date.year, month_end_date.month)[1]
			num_days = (to_date - from_date).days + 1
			mess_adv_amt = flt(mess_amt)/days_in_month * num_days 

		for a in self.items:
			a.amount = mess_adv_amt
			
	def calculate_total_advance(self):
		total_adv = 0
		for adv in self.items:
			total_adv += adv.amount
		self.total_advance = total_adv

	def validate_duplicate_desuup_entry(self):
		# validating duplicates entry in a table
		desuups = set()
		for child in self.get('items'):
			if child.desuup in desuups:
				frappe.throw(f"Duplicate entry for Desuup <strong>{child.desuup}</strong>")
			desuups.add(child.desuup)
	
	def validate_is_exists_in_training_management(self):
		for item in self.items:
			if not self.is_desuup_exists_in_tm(item.desuup):
				frappe.throw(f"Desuup {item.desuup} does not exist in the Training Management or is not a mess member")

	def is_desuup_exists_in_tm(self, desuup):
		existing_items = frappe.db.sql(f"""
			SELECT desuup_id as desuup, is_mess_member
			FROM `tabTrainee Details`
			WHERE parenttype = %s
			AND parent = %s
		""", (self.reference_doctype, self.reference_name), as_dict=True)

		# Check if the item_code exists in the fetched items
		for d in existing_items:
			if d['desuup'] == desuup and d['is_mess_member']:
				return True
		return False
	
	def validate_duplicate_monthly_advance(self):
		for child in self.get('items'):
			existing_advance = frappe.db.sql("""
									SELECT t1.name
									FROM `tabDesuup Mess Advance` t1, `tabDesuup Mess Advance Item` t2
									WHERE t1.name = t2.parent
									AND t1.docstatus < 2
									AND t2.desuup = %s
									AND t1.month = %s
									AND t1.reference_name = %s
									AND t2.parent != %s
								""", (child.desuup, self.month, self.reference_name, self.name))
			if existing_advance:
				frappe.throw(f"Desuup <strong>{child.desuup}</strong> has already claimed an advance for month <strong>{self.month}</strong>.")

	def post_journal_entry(self):
		accounts = []
		bank_account = frappe.db.get_value("Company", self.company, "default_bank_account")
		debit_account = frappe.db.get_single_value("Desuup Settings", "mess_advance_account")
		if not bank_account:
			frappe.throw("Set default bank account in company {}".format(frappe.bold(self.company)))
		
		accounts.append({
				"account": debit_account,
				"debit_in_account_currency": flt(self.total_advance,2),
				"cost_center": self.cost_center,
				"party_check": 1,
				"party_type": "Employee",
				"party": self.paid_to,
				"party_name":frappe.db.get_value("Employee", self.paid_to, "employee_name"),
				"reference_type": self.doctype,
				"reference_name": self.name,
			})

		accounts.append({
			"account": bank_account,
			"credit_in_account_currency": flt(self.total_advance,2),
			"cost_center": self.cost_center,
		})
		je = frappe.new_doc("Journal Entry")
		je.flags.ignore_permission = 1
		je.update({
			"doctype": "Journal Entry",
			"branch": self.branch,
			"posting_date": self.posting_date,
			"voucher_type": "Bank Entry",
			"naming_series": "Bank Payment Voucher",
			"company": self.company,
			"reference_doctype":self.doctype,
			"reference_name":self.name,
			"accounts": accounts
		})
		je.insert()
		self.db_set('journal_entry', je.name)
		frappe.msgprint(_('Journal Entry {0} posted to accounts').format(frappe.get_desk_link("Journal Entry",je.name)))

	@frappe.whitelist()
	def set_dates(self):
		self.validate_month_entry()
		month_start_date, month_end_date = self.get_start_end_month_date()

		self.from_date = month_start_date
		self.to_date = month_end_date

	def get_start_end_month_date(self):
		month_start_date = "-".join([str(date.today().year), self.month, "01"])
		month_end_date   = get_last_day(month_start_date)

		return month_start_date, month_end_date
	
	def validate_month_entry(self):
		start_date, end_date = self.get_training_start_end_date()

		start_month = start_date.month
		end_month = end_date.month

		try:
			validate_month = int(self.month)
		except ValueError:
			frappe.throw("Month must be a valid number in 'MM' format.")
		
		# Check if the month_to_validate is within the training period
		if start_month <= end_month:
			# Period within the same year
			if not (start_month <= validate_month <= end_month):
				frappe.throw("The month does not fall within the training period. i.e. from {} to {}".format(frappe.bold(start_date), frappe.bold(end_date)))
		else:
			# Period spans across two years
			if not (validate_month >= start_month or validate_month <= end_month):
				frappe.throw("The month does not fall within the training period. i.e. from {} to {}".format(frappe.bold(start_date), frappe.bold(end_date)))

	def get_training_start_end_date(self):
		if self.reference_doctype == "Training Management" and self.reference_name:
			start_date, end_date = frappe.db.get_value("Training Management", self.reference_name, ['training_start_date', 'training_end_date'])

			if not start_date or not end_date:
				frappe.throw("Training start date or end date is not set for the reference name.")
			
			start_date = getdate(start_date)
			end_date = getdate(end_date)

			return start_date, end_date
		else:
			frappe.throw("Reference doctype or reference name is not set.")


	@frappe.whitelist()
	def set_advance_party(self):
		self.paid_to = frappe.db.get_value("Training Center", self.training_center, "party")
		if not self.paid_to:
			frappe.throw("Please set party in training center '{}'".format(frappe.get_desk_link("Training Center", self.training_center)))

	