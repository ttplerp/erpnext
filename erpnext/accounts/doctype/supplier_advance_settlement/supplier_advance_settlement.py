# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from frappe.utils import flt, now_datetime

class SupplierAdvanceSettlement(Document):
	def validate(self):
		get_balance_amount(self.supplier, self.advance_type)
		self.validate_amount()

	def on_submit(self):
		self.post_journal_entry()
		self.update_supplier_advance()

	def on_cancel(self):
		self.update_supplier_advance(cancel=True)

	def validate_amount(self):
		if flt(self.amount) > flt(self.balance_amount):
			frappe.throw("Settle amount {} cannot be more than balance amount {}".format(
				frappe.bold(self.amount), frappe.bold(self.balance_amount)
			))

	def post_journal_entry(self):
		debit_account = frappe.db.get_value("Company", self.company, "default_payable_account")
		credit_account = frappe.db.get_value("Advance Type", self.advance_type, "account")

		# Posting Journal Entry
		accounts = []
		accounts.append(
			{
				"account": credit_account,
				"credit_in_account_currency": flt(self.amount),
				"cost_center": self.cost_center,
				"party_check": 1,
				"party_type": "Supplier",
				"party": self.supplier,
				"reference_type": self.doctype,
				"reference_name": self.name,
			}
		)

		accounts.append(
			{
				"account": debit_account,
				"debit_in_account_currency": flt(self.amount),
				"cost_center": self.cost_center,
			}
		)

		je = frappe.new_doc("Journal Entry")
		je.update(
			{
				"doctype": "Journal Entry",
				"voucher_type": "Journal Entry",
				"naming_series": "Journal Voucher",
				"title": "Advance Settlemet " + self.supplier,
				"user_remark": self.supplier,
				"posting_date": self.posting_date,
				"company": self.company,
				"accounts": accounts,
				"branch": self.branch,
				
			}
		)

		je.save(ignore_permissions=True)
		self.db_set("journal_entry", je.name)
		self.db_set(
			"journal_entry_status",
			"Forwarded to accounts on {0}".format(
				now_datetime().strftime("%Y-%m-%d %H:%M:%S")
			),
		)
		frappe.msgprint(
			_("{} posted to accounts").format(frappe.get_desk_link(je.doctype, je.name))
		)


	def update_supplier_advance(self, cancel=False):
		doc = frappe.get_doc(
			"Advance Item",
			frappe.get_value(
				"Advance Item",
				{'parent': self.supplier, 'advance_type': self.advance_type},
				'name'
			)
		)
		if cancel:
			doc.balance_amount = flt(doc.balance_amount) + flt(self.amount)
			doc.adjusted_amount = flt(doc.adjusted_amount) - flt(self.amount)
		else:
			doc.balance_amount = flt(doc.balance_amount) - flt(self.amount)
			doc.adjusted_amount = flt(doc.adjusted_amount) + flt(self.amount)

		doc.save()


@frappe.whitelist()
def get_balance_amount(supplier, advance_type):
	result = frappe.db.sql(
		"""
		SELECT 
			balance_amount
		FROM 
			`tabAdvance Item` 
		WHERE 
			advance_type = %s AND 
			parent = %s
		""", (advance_type, supplier), as_dict=1
	)

	if result:
		return flt(result[0].balance_amount)

	return flt(0)

