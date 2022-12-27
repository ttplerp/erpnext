# -*- coding: utf-8 -*-
# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
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
		imprest_limit = frappe.db.get_value('Branch Imprest Item', {'parent': self.branch }, 'imprest_limit')
		if not imprest_limit:
			frappe.throw('Please assign Imprest Limit in Branch: <a href="#Form/Branch/{0}">{0}</a> under Imprest Settings section'.format(self.branch))
		if self.amount > imprest_limit:
			frappe.throw("Amount requested is greater than Imprest Limit in particular Branch")

	# def before_cancel(self):
	# 	if self.journal_entry:
	# 		for t in frappe.get_all("Journal Entry", ["name"], {"name": self.journal_entry, "docstatus": ("<",2)}):
	# 			frappe.throw(_('Journal Entry  <a href="#Form/Journal Entry/{0}">{0}</a> for this transaction needs to be cancelled first').format(self.journal_entry),title='Not permitted')

	def on_cancel(self):
		if frappe.db.get_value("Journal Entry", self.journal_entry, 'docstatus') == 0:
			frappe.db.sql("update `tabJournal Entry` set docstatus=2 where name='{}'".format(self.journal_entry))
			self.set("docstatus", 2)
		else:
			for t in frappe.get_all("Journal Entry", ["name"], {"name": self.journal_entry, "docstatus": ("<",2)}):
				frappe.throw(_('Journal Entry  <a href="#Form/Journal Entry/{0}">{0}</a> for this transaction needs to be cancelled first').format(self.journal_entry),title='Not permitted')

	def on_submit(self):
		if not self.is_opening:
			self.post_journal_entry()

	# def on_cancel(self):
	# 	frappe.db.sql("update `tabJournal Entry` set docstatus=2 where name='{}'".format(self.journal_entry))

	def post_journal_entry(self):
		if not self.amount:
			frappe.throw(_("Amount should be greater than zero"))

		debit_account = frappe.db.get_value('Company',self.company,'default_imprest_account')
		credit_account = frappe.db.get_value('Branch',self.branch,'expense_bank_account')

		if not debit_account:
			frappe.throw("Setup Default Imprest Account in Company Settings")
		if not credit_account:
			frappe.throw("Setup Expense Bank Account in {} Branch".format(self.branch))

		voucher_type = "Journal Entry"
		voucher_series = "Journal Voucher"
		party_type = ""
		party = ""

		debit_account_type = frappe.db.get_value("Account", debit_account, "account_type")
		credit_account_type = frappe.db.get_value("Account", credit_account, "account_type")

		if credit_account_type == "Bank":
			voucher_type = "Bank Entry"
			voucher_series = "Bank Payment Voucher"
		
		if debit_account_type == "Payable" or debit_account_type == "Receivable":
			party_type = self.party_type
			party = self.party
		
		r = []
		if self.remarks:
			r.append(_("Note: {0}").format(self.remarks))

		remarkss = ("").join(r)

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

		je.append("accounts",{
			"account": credit_account ,
			"credit_in_account_currency": self.amount,
			"cost_center": self.cost_center,
			"business_activity": self.business_activity
		})


		je.append("accounts",{
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
		#Set a reference to the claim journal entry
		self.db_set("journal_entry",je.name)
		frappe.msgprint(_('Journal Entry <a href="#Form/Journal Entry/{0}">{0}</a> posted to accounts').format(je.name))

		