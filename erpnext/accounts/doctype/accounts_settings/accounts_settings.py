# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

# For license information, please see license.txt


import frappe
from frappe import _
from frappe.custom.doctype.property_setter.property_setter import make_property_setter
from frappe.model.document import Document
from frappe.utils import cint

from erpnext.stock.utils import check_pending_reposting


class AccountsSettings(Document):
	def on_update(self):
		frappe.clear_cache()

	def validate(self):
		frappe.db.set_default(
			"add_taxes_from_item_tax_template", self.get("add_taxes_from_item_tax_template", 0)
		)

		frappe.db.set_default(
			"enable_common_party_accounting", self.get("enable_common_party_accounting", 0)
		)

		self.validate_stale_days()
		self.enable_payment_schedule_in_print()
		self.validate_pending_reposts()

	def validate_stale_days(self):
		if not self.allow_stale and cint(self.stale_days) <= 0:
			frappe.msgprint(
				_("Stale Days should start from 1."), title="Error", indicator="red", raise_exception=1
			)

	def enable_payment_schedule_in_print(self):
		show_in_print = cint(self.show_payment_schedule_in_print)
		for doctype in ("Sales Order", "Sales Invoice", "Purchase Order", "Purchase Invoice"):
			make_property_setter(
				doctype, "due_date", "print_hide", show_in_print, "Check", validate_fields_for_doctype=False
			)
			make_property_setter(
				doctype,
				"payment_schedule",
				"print_hide",
				0 if show_in_print else 1,
				"Check",
				validate_fields_for_doctype=False,
			)

	def validate_pending_reposts(self):
		if self.acc_frozen_upto:
			check_pending_reposting(self.acc_frozen_upto)
@frappe.whitelist()
def get_bank_account(branch=None):
	Company = "State Mining Corporation Ltd"
	default_bank_account = frappe.db.get_value('Company',Company,'default_bank_account')
	expense_bank_account = None
	if branch:
		expense_bank_account = frappe.db.get_value('Branch', branch, 'expense_bank_account')

	if not expense_bank_account and not default_bank_account:
		frappe.throw(_("Please set <b>Bank Expense Account</b> under <b>Branch</b> master"))
	return default_bank_account if default_bank_account else expense_bank_account
