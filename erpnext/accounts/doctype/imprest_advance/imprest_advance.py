# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import flt, cint, nowdate, getdate, formatdate, money_in_words

class ImprestAdvance(Document):
	def validate(self):
		if not self.is_opening:
			self.check_imprest_amount()
	
	def check_imprest_amount(self):
		query = """
			SELECT imp.imprest_limit
			FROM `tabBranch Imprest Item` imp
			WHERE imp.parent = %(branch)s and imp.imprest_type = %(imprest_type)s
		"""
		result = frappe.db.sql(query, {'branch': self.branch, 'imprest_type': self.imprest_type}, as_dict=True)
		
		if not result or not result[0].get('imprest_limit'):
			branch_link = frappe.utils.get_link_to_form('Branch', self.branch)
			frappe.throw('Please assign Imprest Limit in Branch: {} under Imprest Settings Section'.format(branch_link))
		
		imprest_limit = result[0].get('imprest_limit')
		
		if self.amount > imprest_limit:
			frappe.throw("Amount requested cannot be greater than Imprest Limit <b>{}</b> for branch <b>{}</b>".format(imprest_limit, self.branch))

	def before_cancel(self):
		if self.journal_entry:
			for t in frappe.get_all("Journal Entry", ["name"], {"name": self.journal_entry, "docstatus": ("<",2)}):
				frappe.throw(_('Journal Entry  <a href="#Form/Journal Entry/{0}">{0}</a> for this transaction needs to be cancelled first').format(self.journal_entry),title='Not permitted')

	def on_submit(self):
		if not self.is_opening:
			self.post_journal_entry()

	def post_journal_entry(self):
		if not self.amount:
			frappe.throw(_("Amount should be greater than zero"))

		query = """
			SELECT comp.imprest_advance_account, br.expense_bank_account
			FROM `tabCompany` comp
			LEFT JOIN `tabBranch` br ON br.name = %(branch)s
			WHERE comp.name = %(company)s
		"""
		result = frappe.db.sql(query, {'branch': self.branch, 'company': self.company}, as_dict=True)

		if not result or not result[0].get('imprest_advance_account'):
			frappe.throw("Setup Default Imprest Advance Account in Company Settings")
		
		if not result[0].get('expense_bank_account'):
			frappe.throw("Setup Expense Bank Account in <b>{}</b> Branch".format(self.branch))

		debit_account = result[0].get('imprest_advance_account')
		credit_account = result[0].get('expense_bank_account')

		voucher_type = "Journal Entry"
		voucher_series = "Journal Voucher"
		party_type = ""
		party = ""

		debit_account_type = frappe.db.get_value("Account", debit_account, "account_type")
		credit_account_type = frappe.db.get_value("Account", credit_account, "account_type")

		if credit_account_type == "Bank":
			voucher_type = "Bank Entry"
			voucher_series = "Bank Payment Voucher"

		if debit_account_type in ("Payable", "Receivable"):
			party_type = self.party_type
			party = self.party

		remarks = []
		if self.remarks:
			remarks.append(_("Note: {0}").format(self.remarks))

		remarkss = "".join(remarks)

		# Posting Journal Entry
		je = frappe.new_doc("Journal Entry")

		je.update({
			"doctype": "Journal Entry",
			"voucher_type": voucher_type,
			"naming_series": voucher_series,
			"title": "Imprest Advance - " + self.name,
			"user_remark": remarkss if remarkss else "Note: " + "Imprest Advance - " + self.name,
			"posting_date": self.posting_date,
			"company": self.company,
			"total_amount_in_words": money_in_words(self.amount),
			"branch": self.branch
		})

		je.append("accounts", {
			"account": credit_account,
			"credit_in_account_currency": self.amount,
			"cost_center": self.cost_center,
			"business_activity": self.business_activity
		})

		je.append("accounts", {
			"account": debit_account,
			"debit_in_account_currency": self.amount,
			"cost_center": self.cost_center,
			"business_activity": self.business_activity,
			"reference_type": "Imprest Advance",
			"reference_name": self.name,
			"party_type": party_type,
			"party": party
		})

		je.insert()
		# Set a reference to the claim journal entry
		self.db_set("journal_entry", je.name)
		frappe.msgprint("Journal Entry created. {}".format(frappe.get_desk_link("Journal Entry", je.name)))
