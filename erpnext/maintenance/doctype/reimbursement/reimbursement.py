# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from erpnext.custom_utils import check_budget_available
from frappe import _
from frappe.utils import flt, cint, nowdate, getdate, formatdate, money_in_words

class Reimbursement(Document):
	def validate(self):
		self.calculate_amount()

	def calculate_amount(self):
		total = 0
		for d in self.items:
			total += d.amount
		self.amount = total

	def before_cancel(self):
		if self.journal_entry:
			for t in frappe.get_all("Journal Entry", ["name"], {"name": self.journal_entry, "docstatus": ("<",2)}):
				frappe.throw(_('Journal Entry {} for this transaction needs to be cancelled first').format(frappe.get_desk_link(self.doctype,self.journal_entry)),title='Not permitted')

	def on_submit(self):
		check_budget_available(self.cost_center,self.expense_account,self.posting_date,self.amount,self.business_activity)
		self.post_journal_entry()

	def post_journal_entry(self):
		if not self.amount:
			frappe.throw(_("Amount should be greater than zero"))

		debit_account = self.expense_account
		if not self.credit_account:
			advance_account = frappe.db.get_value("Company", self.company, "default_bank_account")
		else:
			advance_account = self.credit_account

		if not debit_account:
			frappe.throw("Expense Account is mandatory")
		if not advance_account:
			frappe.throw("Setup Default Bank Account in Company Settings")

		voucher_type = "Journal Entry"
		voucher_series = "Journal Voucher"
		party_type = ""
		party = ""
		account_type = frappe.db.get_value("Account", advance_account, "account_type")
		if account_type == "Bank":
			voucher_type = "Bank Entry"
			voucher_series = "Bank Payment Voucher"
		elif account_type == "Payable" or account_type == "Receivable":
			party_type = self.party_type
			party = self.party
		
		r = []
		if self.remarks:
			r.append(_("Note: {0}").format(self.remarks))

		remarkss = ("").join(r)

		je = frappe.new_doc("Journal Entry")

		je.update({
			"doctype": "Journal Entry",
			"voucher_type": voucher_type,
			"naming_series": voucher_series,
			"title": "Reimbursement - " + self.name,
			"user_remark": remarkss if remarkss else "Note: " + "Reimbursement - " + self.name,
			"posting_date": self.posting_date,
			"company": self.company,
			"total_amount_in_words": money_in_words(self.amount),
			"branch": self.branch
		})

		je.append("accounts",{
			"account": advance_account,
			"credit_in_account_currency": self.amount,
			"cost_center": self.cost_center,
			"reference_type": "Reimbursement",
			"reference_name": self.name,
			"business_activity": self.business_activity,
			"party_type": party_type,
			"party": party
		})


		je.append("accounts",{
			"account": debit_account,
			"debit_in_account_currency": self.amount,
			"cost_center": self.cost_center,
			"business_activity": self.business_activity
		})

		je.insert()
		self.db_set("journal_entry",je.name)
		frappe.msgprint(_('Journal Entry {} posted to accounts').format(frappe.get_desk_link(je.doctype,je.name)))