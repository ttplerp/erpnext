# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
from erpnext.accounts.doctype.business_activity.business_activity import get_default_ba
from erpnext.controllers.accounts_controller import AccountsController
from frappe.utils import flt, cint, nowdate, getdate, formatdate, money_in_words, now_datetime

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
		self.validate_refund_amount()

	def validate_refund_amount(self):
		if self.refund_amount < 0 or self.refund_amount == 0:
			frappe.throw("Invalid Refund Amount figure.")
		
		account = self.account_refund_to
		bal_amount = self.get_party_balance_amount(account)

		if self.refund_amount > bal_amount:
			frappe.throw(
					_(
						"Refund Amount {0} cannot be greater than balance amount {1} for Customer {2} and Account {3}"
					).format(self.refund_amount, flt(bal_amount), self.customer, account)
				)

	def get_party_balance_amount(self, account):
		bal_amount = frappe.db.sql("""
				select ifnull(sum(credit) - sum(debit), 0) as bal_amount
				from `tabGL Entry` 
				Where party_type='Customer' 
				and party = '{party}' and account = '{account}' and is_cancelled=0
			""".format(party=self.customer, account=account))[0][0]
		
		return bal_amount

	def on_submit(self):
		self.post_journal_entry()

	def post_journal_entry(self):
		ba = get_default_ba()
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
		self.db_set("journal_entry_status", "Forwarded to accounts for processing payment on {0}".format(now_datetime().strftime('%Y-%m-%d %H:%M:%S')))
		frappe.msgprint(_('Journal Entry {} posted to Accounts').format(frappe.get_desk_link(je.doctype,je.name)))
