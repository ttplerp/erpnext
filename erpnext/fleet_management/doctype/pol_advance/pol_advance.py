# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from erpnext.accounts.doctype.business_activity.business_activity import get_default_ba
from frappe.utils import money_in_words, cstr, flt, fmt_money, formatdate, getdate, nowdate, cint, get_link_to_form, now_datetime, get_datetime
from erpnext.custom_workflow import validate_workflow_states, notify_workflow_states
from frappe import _, qb, throw, bold
from erpnext.accounts.party import get_party_account
from erpnext.controllers.accounts_controller import AccountsController
from erpnext.accounts.general_ledger import (
	get_round_off_account_and_cost_center,
	make_gl_entries,
	make_reverse_gl_entries,
	merge_similar_entries,
)

class POLAdvance(AccountsController):
	def validate(self):
		# if flt(self.is_opening) == 0:
		# 	validate_workflow_states(self)
		self.set_advance_limit()
		self.posting_date = self.entry_date
		self.validate_amount()

		self.credit_account = frappe.db.get_value("Branch", self.fuelbook_branch, "expense_bank_account")

		# if flt(self.is_opening) == 0 and self.workflow_state != "Approved" :
		# 	notify_workflow_states(self)
	
	def on_submit(self): 
		if not self.is_opening:
			self.post_journal_entry()
		# if flt(self.is_opening) == 0:
			# notify_workflow_states(self)

	def before_cancel(self):
		if self.is_opening:
			return
		if frappe.db.exists("Journal Entry",self.journal_entry):
			doc = frappe.get_doc("Journal Entry", self.journal_entry)
			if doc.docstatus != 2:
				frappe.throw("Journal Entry exists for this transaction {}".format(frappe.get_desk_link("Journal Entry",self.journal_entry)))
				
	def on_cancel(self):
		self.ignore_linked_doctypes = ("GL Entry", "Stock Ledger Entry", "Payment Ledger Entry")
		if cint(self.use_common_fuelbook) == 0:
			self.make_gl_entries()

	@frappe.whitelist()
	def set_advance_limit(self):
		if cint(self.use_common_fuelbook) == 1:
			if not self.fuel_book:
				frappe.throw("Fuel book is missing")
			if flt(self.advance_limit) <= 0 :
				self.advance_limit = frappe.db.get_value("Fuelbook", self.fuel_book, "expense_limit")
		else:
			if not self.equipment:
				frappe.throw("Equipment or Fuel book is missing")

			if flt(self.advance_limit) <= 0 and self.equipment_type:
				self.advance_limit = frappe.db.get_value("Equipment Type", self.equipment_type, "pol_expense_limit")
		
	def post_journal_entry(self):
		if self.is_opening:
			return
		if not self.amount:
			frappe.throw(_("Amount should be greater than zero"))
			
		default_ba = get_default_ba()
		
		credit_account = self.credit_account
		advance_account = frappe.db.get_value("Equipment Category", self.equipment_category, 'pol_advance_account')
		if not advance_account:
			advance_account = frappe.db.get_value("Company", self.company, "pol_advance_account")
		if not credit_account:
			frappe.throw("Credit Account is mandatory")
		
		r = []
		if self.cheque_no:
			if self.cheque_date:
				r.append(_('Reference #{0} dated {1}').format(self.cheque_no, formatdate(self.cheque_date)))
			else:
				msgprint(_("Please enter Cheque Date date"), raise_exception=frappe.MandatoryError)
		
		if self.user_remark:
			r.append(_("Note: {0}").format(self.user_remark))

		remarks = ("").join(r) #User Remarks is not mandatory
		
		# Posting Journal Entry
		je = frappe.new_doc("Journal Entry")
		je.flags.ignore_permissions=1
		je.update({
			"doctype": "Journal Entry",
			"voucher_type": "Bank Entry",
			"naming_series": "Bank Payment Voucher",
			"title": "POL Advance - " + self.equipment if cint(self.use_common_fuelbook) == 0 else self.fuel_book,
			"user_remark": "Note: " + "POL Advance - " + self.equipment if cint(self.use_common_fuelbook) == 0 else self.fuel_book,
			"posting_date": self.posting_date,
			"company": self.company,
			"total_amount_in_words": money_in_words(self.amount),
			"branch": self.fuelbook_branch,
		})

		je.append("accounts",{
			"account": credit_account,
			"credit_in_account_currency": self.amount,
			"cost_center": self.cost_center,
			"reference_type": "POL Advance",
			"reference_name": self.name,
			"business_activity": default_ba
		})

		je.append("accounts",{
			"account": advance_account,
			"debit_in_account_currency": self.amount,
			"cost_center": self.cost_center,
			"party_check": 0,
			"party_type": "Supplier",
			"party": self.party,
			"business_activity": default_ba
		})

		je.insert()
		#Set a reference to the claim journal entry
		self.db_set("journal_entry",je.name)
		frappe.msgprint(_('Journal Entry {0} posted to accounts').format(frappe.get_desk_link("Journal Entry",je.name)))
	
	def validate_amount(self):
		if flt(self.amount) <= 0:
			frappe.throw("Amount cannot be less than or equal to Zero")
		if cint(self.use_common_fuelbook) == 0 and flt(self.amount) > flt(self.advance_limit):
			frappe.throw("Amount cannot be greater than advance limit")
		if cint(self.is_opening) == 0 :
			self.outstanding_amount = self.amount

def get_permission_query_conditions(user):
	if not user: user = frappe.session.user
	user_roles = frappe.get_roles(user)

	if user == "Administrator" or "System Manager" in user_roles: 
		return

	return """(
		`tabPOL Advance`.owner = '{user}'
		or
		exists(select 1
			from `tabEmployee` as e
			where e.branch = `tabPOL Advance`.fuelbook_branch
			and e.user_id = '{user}')
		or
		exists(select 1
			from `tabEmployee` e, `tabAssign Branch` ab, `tabBranch Item` bi
			where e.user_id = '{user}'
			and ab.employee = e.name
			and bi.parent = ab.name
			and bi.branch = `tabPOL Advance`.fuelbook_branch)
		or
		(`tabPOL Advance`.approver = '{user}' and `tabPOL Advance`.workflow_state not in  ('Draft','Approved','Rejected','Cancelled'))
	)""".format(user=user)