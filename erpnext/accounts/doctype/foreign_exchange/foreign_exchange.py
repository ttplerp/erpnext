# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import (
	cint,
	cstr,
	flt,
	formatdate,
	get_link_to_form,
	getdate,
	now_datetime,
	nowtime,
	strip,
	strip_html,
)

class ForeignExchange(Document):
	def validate(self):
		self.validate_currency()

	def on_submit(self):
		if not self.is_opening:
			self.post_journal_entry()

	def validate_currency(self):
		if self.currency == "BTN":
			frappe.throw("Please choose currency other than {}".format(frappe.bold("BTN")))

	def post_journal_entry(self):
		accounts = []
		bank_account = frappe.db.get_value("Company", self.company, "default_cash_account")
		if not bank_account:
			frappe.throw("Set Default Bank Account in Company {}".format(frappe.get_desk_link("Company", self.company)))

		account = frappe.db.get_value("Currency", self.currency, "account")
		if not account:
			frappe.throw("Set Account in Currency {}".format(frappe.get_desk_link("Currency", self.currency)))

		accounts.append({
				"account": account,
				"debit_in_account_currency":  flt(self.base_amount, 2),
				"cost_center": self.cost_center,
				"reference_type": self.doctype,
				"reference_name": self.name,
			})

		accounts.append({
				"account": bank_account,
				"credit_in_account_currency": flt(self.base_amount, 2),
				"cost_center": self.cost_center,
				"reference_type": self.doctype,
				"reference_name": self.name,
			})

		je = frappe.new_doc("Journal Entry")
		je.flags.ignore_permission = 1
		je.update({
			"doctype": "Journal Entry",
			"branch": self.branch,
			"posting_date": self.posting_date,
			"voucher_type": "Cash Entry",
			"naming_series": "Cash Payment Voucher",
			"company": self.company,
			
			"accounts": accounts
		})
		je.insert()
		self.db_set('journal_entry', je.name)
		# self.db_set("journal_entry_status", "Forwarded to accounts for processing payment on {0}".format(now_datetime().strftime('%Y-%m-%d %H:%M:%S')))
		frappe.msgprint(_('Journal Entry {0} posted to accounts').format(frappe.get_desk_link("Journal Entry", je.name)))
