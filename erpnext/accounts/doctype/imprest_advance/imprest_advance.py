# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import flt, cint, nowdate, getdate, formatdate, money_in_words
from erpnext.custom_workflow import validate_workflow_states, notify_workflow_states

class ImprestAdvance(Document):
	def validate(self):
		if not self.is_opening:
			self.check_imprest_amount()
		if cint(self.first_advance) == 1:
			self.check_for_duplicate_entry()
			validate_workflow_states(self)
			if self.workflow_state != "Approved":
				notify_workflow_states(self)
	
	def check_for_duplicate_entry(self):
		import datetime

		date_obj = datetime.datetime.strptime(str(self.posting_date), "%Y-%m-%d")
		year = date_obj.year

		for d in frappe.db.get_list("Imprest Advance",filters={"branch": self.branch, "imprest_type": self.imprest_type, "docstatus": 1}, fields=["posting_date"]):
			date_obj = datetime.datetime.strptime(str(d.posting_date), "%Y-%m-%d")
			year_old = date_obj.year
			if str(year) == str(year_old):
				frappe.throw("Imprest Advance already taken for branch <b>{}</b> and imprest type <b>{}</b>".format(self.branch, self.imprest_type))

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
			je_status = frappe.get_value("Journal Entry", {"name": self.journal_entry}, "docstatus")
			if cint(je_status) == 1:
				frappe.throw("Journal Entry {} for this transaction needs to be cancelled first".format(frappe.get_desk_link("Journal Entry", self.journal_entry)))
			else:
				frappe.db.sql("delete from `tabJournal Entry` where name = '{}'".format(self.journal_entry))
				self.db_set("journal_entry", None)
	
	def on_cancel(self):
		if self.first_advance == 0 and self.imprest_recoup_id:
			frappe.throw("Imprest Recoup <b>{}</b> needs to to cancelled first.".format(self.imprest_recoup_id))
		
		self.ignore_linked_doctypes = ("GL Entry", "Payment Ledger Entry")
		if cint(self.first_advance) == 1:
			notify_workflow_states(self)

	def on_submit(self):
		if cint(self.first_advance) == 1:
			notify_workflow_states(self)
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
			"account": debit_account,
			"debit_in_account_currency": self.amount,
			"cost_center": self.cost_center,
			"reference_type": "Imprest Advance",
			"reference_name": self.name,
			"party_type": party_type,
			"party": party
		})
		
		je.append("accounts", {
			"account": credit_account,
			"credit_in_account_currency": self.amount,
			"cost_center": self.cost_center,
		})

		je.insert()
		# Set a reference to the claim journal entry
		self.db_set("journal_entry", je.name)
		frappe.msgprint("Journal Entry created. {}".format(frappe.get_desk_link("Journal Entry", je.name)))

def get_permission_query_conditions(user):
	if not user: user = frappe.session.user
	user_roles = frappe.get_roles(user)

	if user == "Administrator" or "System Manager" in user_roles or "Accounts User" in user_roles or "Account Manager" in user_roles: 
		return

	return """(
		`tabImprest Advance`.owner = '{user}'
		or
		exists(select 1
			from `tabEmployee` as e
			where e.branch = `tabImprest Advance`.branch
			and e.user_id = '{user}')
		or
		exists(select 1
			from `tabEmployee` e, `tabAssign Branch` ab, `tabBranch Item` bi
			where e.user_id = '{user}'
			and ab.employee = e.name
			and bi.parent = ab.name
			and bi.branch = `tabImprest Advance`.branch)
	)""".format(user=user)

