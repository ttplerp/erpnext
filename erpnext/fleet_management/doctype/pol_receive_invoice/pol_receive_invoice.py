# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import flt, money_in_words
from erpnext.accounts.party import get_party_account
from erpnext.accounts.general_ledger import (
	make_gl_entries,
)
from erpnext.controllers.accounts_controller import AccountsController

class POLReceiveInvoice(AccountsController):
	def validate(self):
		self.calcualte_outstanding_amount()
		self.set_status()
		if not self.credit_account:
			self.credit_account = get_party_account(self.party_type, self.party, self.company)

	def on_submit(self):
		self.make_gl_entry()

	def on_cancel(self):
		self.make_gl_entry()

	def calcualte_outstanding_amount(self):
		self.outstanding_amount = self.amount

	def set_status(self, update=False, status=None, update_modified=True):
		outstanding_amount = flt(self.outstanding_amount, 2)
		if not status:
			if self.docstatus == 2:
				status = "Cancelled"
			elif self.docstatus == 1:
				if outstanding_amount > 0 and self.amount > outstanding_amount:
					self.status = "Unpaid"
				elif outstanding_amount <= 0:
					self.status = "Paid"
				else:
					self.status = "Submitted"

		if update:
			self.db_set("status", self.status, update_modified=update_modified)

	def make_gl_entry(self):
		gl_entries = []
		gl_entries.append(
			self.get_gl_dict({
				"account": self.debit_account,
				"debit": self.amount,
				"debit_in_account_currency": self.amount,
				"voucher_no": self.name,
				"voucher_type": self.doctype,
				"cost_center": self.cost_center,
			})
		)

		gl_entries.append(
			self.get_gl_dict({
				"account": self.credit_account,
				"party_type": self.party_type,
				"party": self.party,
				"credit": self.amount,
				"credit_in_account_currency": self.amount,
				"cost_center": self.cost_center,
				"voucher_no": self.name,
				"voucher_type": self.doctype,
				"against_voucher": self.name,
				"against_voucher_type": self.doctype,
			})
		)
		make_gl_entries(gl_entries, update_outstanding="No", cancel=(self.docstatus == 2), merge_entries=False)
