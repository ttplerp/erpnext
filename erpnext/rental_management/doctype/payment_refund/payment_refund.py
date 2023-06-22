# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from erpnext.accounts.doctype.business_activity.business_activity import get_default_ba
from erpnext.controllers.accounts_controller import AccountsController

class PaymentRefund(AccountsController):
	def validate(self):
		self.get_default_account()
		self.validate_amount()

	def get_default_account(self):
		company = frappe.db.get("Company", self.company)
		if not self.account_refund_from:
			self.account_refund_from = company.get("default_bank_account")
		if not self.account_refund_to:
			if self.type == "Excess Amount":
				self.account_refund_to = company.get("excess_payment_account")
			else:
				self.account_refund_to = company.get("security_deposit_account")

	def validate_amount(self):
		if self.refund_amount < 0 or self.refund_amount == 0:
			frappe.throw("Invalid Refund Amount figure.")

	def on_submit(self):
		self.post_journal_entry()

	def post_journal_entry(self):
		r = []
		if self.remarks:
			r.append(_("Note: {0}").format(self.remarks))

		remarks = ("").join(r) 

		je = frappe.new_doc("Journal Entry")

		je.update({
			"doctype": "Journal Entry",
			"voucher_type": "Bank Entry",
			"naming_series": "Bank Payment Voucher",
			"title": self.customer + " - Payment Refund",
			"user_remark": remarks if remarks else "Note: " + "Payment Refund - " + self.name,
			"posting_date": self.posting_date,
			"company": self.company,
			"total_amount_in_words": money_in_words(self.refund_amount),
			"branch": self.branch,
			# "apply_tds": 1 if self.tds_amount > 0 else 0,
			# "tax_withholding_category": self.tax_withholding_category
		})

		je.append("accounts",{
			"account": self.account_refund_to,
			"debit_in_account_currency": self.refund_amount,
			"cost_center": self.cost_center,
			"party_check": 0,
			"party_type": "Customer",
			"party": self.customer,
			"reference_type": "Payment Refund",
			"reference_name": self.name,
			"business_activity": ba,
			# "apply_tds": 1 if self.tds_amount > 0 else 0,
			# "add_deduct_tax": "Deduct" if self.tds_amount > 0 else "",
			# "tax_account": tds_account,
			# "rate": tds_rate,
			# "tax_amount_in_account_currency": self.tds_amount,
			# "tax_amount": self.tds_amount
		})

		je.append("accounts",{
			"account": self.account_refund_from,
			"credit_in_account_currency": self.refund_amount,
			"cost_center": self.cost_center,
			"business_activity": ba,
		})

		je.insert()
		self.db_set("journal_entry",je.name)
		frappe.msgprint(_('Journal Entry {} posted to Accounts').format(frappe.get_desk_link(je.doctype,je.name)))
