# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import flt, cint, nowdate, getdate, formatdate, money_in_words
from erpnext.custom_workflow import validate_workflow_states, notify_workflow_states

class ImprestRecoup(Document):
	def validate(self):
		validate_workflow_states(self)
		self.calculate_amount()
		self.populate_imprest_advance()
		self.set_recoup_account(validate=True)
		if self.workflow_state != "Recouped":
			notify_workflow_states(self)
	
	def set_recoup_account(self, validate=False):
		for d in self.items:
			if not d.account or not validate:
				d.account = get_imprest_recoup_account(d.recoup_type, self.company)[
					"account"
				]

	def calculate_amount(self):
		tot_bal_amt = sum(d.balance_amount for d in self.imprest_advance_list)
		total_payable_amt = sum(d.amount for d in self.items) if self.items else 0
		self.total_amount = total_payable_amt
		self.opening_balance = total_payable_amt + tot_bal_amt
		self.balance_amount = tot_bal_amt

		if self.docstatus != 1 and tot_bal_amt < self.total_amount and self.workflow_state == "Draft":
			frappe.throw("Expense amount cannot be more than balance amount.")

	def on_submit(self):
		notify_workflow_states(self)
		self.update_advance()
		self.post_journal_entry()
		if self.final == "No":
			self.create_auto_imprest_advance()
		else:
			self.post_final_claim_je()
	
	def before_cancel(self):
		if self.journal_entry:
			je_status = frappe.get_value("Journal Entry", {"name": self.journal_entry}, "docstatus")
			if cint(je_status) == 1:
				frappe.throw("Journal Entry {} for this transaction needs to be cancelled first".format(frappe.get_desk_link("Journal Entry", self.journal_entry)))
			else:
				frappe.db.sql("delete from `tabJournal Entry` where name = '{}'".format(self.journal_entry))
				self.db_set("journal_entry", None)

		self.check_imprest_advance_status_and_cancel()
		
	def on_cancel(self):
		self.update_advance(1)
		self.ignore_linked_doctypes = ("GL Entry", "Payment Ledger Entry")
		notify_workflow_states(self)

	def check_imprest_advance_status_and_cancel(self):
		ima = frappe.db.sql("select name from `tabImprest Advance` where imprest_recoup_id = '{}' and docstatus = 1".format(self.name))
		if ima:
			ia_doc = frappe.get_doc("Imprest Advance", {"name": ima})
			ia_doc.cancel()
	
	def post_final_claim_je(self):
		total_balance = sum(d.balance_amount for d in self.imprest_advance_list)

		# if total_balance <= 0:
		# 	frappe.throw(_("Final Settlement Amount should be greater than zero"))
		
		if flt(total_balance) == 0:
			return

		credit_account = frappe.db.get_value('Company', self.company, 'imprest_advance_account')
		debit_account = frappe.db.get_value('Branch', self.branch, 'expense_bank_account')
		if not credit_account:
			frappe.throw("Setup Default Imprest Advance Account in Company Settings")
		
		if not debit_account:
			frappe.throw("Setup Default Bank Account in Branch <b>{}</b>".format(self.branch))

		voucher_type = "Journal Entry"
		voucher_series = "Journal Voucher"
		party_type = ""
		party = ""

		account_type = frappe.db.get_value("Account", credit_account, "account_type")
		if account_type == "Bank":
			voucher_type = "Bank Entry"
			voucher_series = "Bank Payment Voucher"
		elif account_type == "Payable" or account_type == "Receivable":
			party_type = self.party_type
			party = self.party

		remarks = []
		if self.remarks:
			remarks.append(_("Note: {0}").format(self.remarks))
		remarks_str = " ".join(remarks)

		# Posting Journal Entry
		je = frappe.new_doc("Journal Entry")
		je.update({
			"voucher_type": voucher_type,
			"naming_series": voucher_series,
			"title": f"Final Imprest Settlement for - {self.party}",
			"user_remark": remarks_str if remarks_str else f"Note: Final Imprest Settlement for party - {self.party}",
			"posting_date": self.posting_date,
			"company": self.company,
			"total_amount_in_words": money_in_words(total_balance),
			"branch": self.branch
		})

		je.append("accounts", {
			"account": debit_account,
			"debit_in_account_currency": flt(total_balance),
			"cost_center": self.cost_center,
			"project": self.project,
		})
		
		je.append("accounts", {
			"account": credit_account,
			"credit_in_account_currency": flt(total_balance),
			"cost_center": self.cost_center,
			"project": self.project,
			"reference_type": "Imprest Recoup",
			"reference_name": self.name,
			"party_type": party_type,
			"party": party,
		})

		je.insert()

		self.db_set("final_je", je.name)
		frappe.msgprint("Journal Entry created. {}".format(frappe.get_desk_link("Journal Entry", je.name)))
	
	@frappe.whitelist()
	def populate_imprest_advance(self):
		if not self.imprest_type or not self.party or not self.branch:
			frappe.throw("Please insert the mandatory fields")
		else:
			self.set('imprest_advance_list', [])
			if self.project:
				query = """
					SELECT 
						a.name, a.amount, a.balance_amount, a.journal_entry, a.is_opening, a.project
					FROM `tabImprest Advance` a
					WHERE a.docstatus = 1 
						AND a.branch = '{branch}'
						AND a.posting_date <= '{date}'
						AND a.balance_amount > 0
						AND a.imprest_type = '{imprest_type}'
						AND a.party = '{party}'
						AND a.project = '{project}'
						AND CASE WHEN a.is_opening = 0 THEN EXISTS (SELECT 1 FROM `tabJournal Entry` WHERE name = a.journal_entry AND docstatus = 1) ELSE a.is_opening END
					ORDER BY a.posting_date
				""".format(branch=self.branch, date=self.posting_date, imprest_type=self.imprest_type, party=self.party, project=self.project)
			else:
				query = """
					SELECT 
						a.name, a.amount, a.balance_amount, a.journal_entry, a.is_opening, a.project
					FROM `tabImprest Advance` a
					WHERE a.docstatus = 1 
						AND a.branch = '{branch}'
						AND a.posting_date <= '{date}'
						AND a.balance_amount > 0
						AND a.imprest_type = '{imprest_type}'
						AND a.party = '{party}'
						AND CASE WHEN a.is_opening = 0 THEN EXISTS (SELECT 1 FROM `tabJournal Entry` WHERE name = a.journal_entry AND docstatus = 1) ELSE a.is_opening END
					ORDER BY a.posting_date
				""".format(branch=self.branch, date=self.posting_date, imprest_type=self.imprest_type, party=self.party)

			data = frappe.db.sql(query, as_dict=True)

			if not data:
				frappe.throw("No Imprest Advance")

			allocated_amount = self.total_amount or 0
			total_amount_adjusted = 0

			for d in data:
				if d.project and not self.project:
					frappe.throw("You have not selected the Project")

				row = self.append('imprest_advance_list', {
					'imprest_advance': d.name,
					'advance_amount': d.amount,
				})

				if d.balance_amount >= allocated_amount:
					row.allocated_amount = allocated_amount
					row.balance_amount = d.balance_amount - allocated_amount
					allocated_amount = 0
				else:
					row.allocated_amount = d.balance_amount
					row.balance_amount = 0
					allocated_amount -= d.balance_amount

			if not self.imprest_advance_list:
				frappe.throw("No Imprest Advance")

	def update_advance(self, cancel=0):
		for d in self.imprest_advance_list:
			doc = frappe.get_doc("Imprest Advance", d.imprest_advance)
			allocated_amount = flt(d.allocated_amount)

			if cancel == 1:
				doc.balance_amount += allocated_amount
				doc.adjusted_amount -= allocated_amount
				if self.final == "Yes":
					doc.balance_amount += d.balance_amount
					doc.adjusted_amount -= d.balance_amount
			else:
				doc.balance_amount -= allocated_amount
				doc.adjusted_amount += allocated_amount
				if self.final == "Yes":
					doc.balance_amount -= d.balance_amount
					doc.adjusted_amount += d.balance_amount
			
			doc.save(ignore_permissions=True)

	def post_journal_entry(self):
		if self.items:
			if not self.total_amount:
				frappe.throw(_("Total Payable Amount should be greater than zero"))

			credit_account = frappe.db.get_value('Company', self.company, 'imprest_advance_account')
			if not credit_account:
				frappe.throw("Setup Default Imprest Advance Account in Company Settings")

			voucher_type = "Journal Entry"
			voucher_series = "Journal Voucher"
			party_type = ""
			party = ""

			account_type = frappe.db.get_value("Account", credit_account, "account_type")
			if account_type == "Bank":
				voucher_type = "Bank Entry"
				voucher_series = "Bank Payment Voucher"
			elif account_type == "Payable" or account_type == "Receivable":
				party_type = self.party_type
				party = self.party

			remarks = []
			if self.remarks:
				remarks.append(_("Note: {0}").format(self.remarks))
			remarks_str = " ".join(remarks)

			# Posting Journal Entry
			je = frappe.new_doc("Journal Entry")
			je.update({
				"voucher_type": voucher_type,
				"naming_series": voucher_series,
				"title": f"Imprest Recoup - {self.name}",
				"user_remark": remarks_str if remarks_str else f"Note: Imprest Recoup - {self.name}",
				"posting_date": self.posting_date,
				"company": self.company,
				"total_amount_in_words": money_in_words(self.total_amount),
				"branch": self.branch
			})

			for i in self.items:
				je.append("accounts", {
					"account": i.account,
					"debit_in_account_currency": i.amount,
					"cost_center": self.cost_center,
					"project": self.project,

				})
			
			je.append("accounts", {
				"account": credit_account,
				"credit_in_account_currency": self.total_amount,
				"cost_center": self.cost_center,
				"project": self.project,
				"reference_type": "Imprest Recoup",
				"reference_name": self.name,
				"party_type": party_type,
				"party": party,
			})

			je.insert()

			# Set a reference to the claim journal entry
			self.db_set("journal_entry", je.name)
			frappe.msgprint("Journal Entry created. {}".format(frappe.get_desk_link("Journal Entry", je.name)))

	def create_auto_imprest_advance(self):
		if self.total_amount:
			ima = frappe.new_doc("Imprest Advance")
			ima.update({
				"branch": self.branch,
				"posting_date": self.posting_date,
				"title": f"Auto Imprest Allocation from - {self.name}",
				"remarks": f"Note: Auto created Imprest Advance Allocation from Recoup - {self.name}",
				"first_advance": 0,
				"company": self.company,
				"imprest_type": self.imprest_type,
				"party_type": self.party_type,
				"party": self.party,
				"amount": self.total_amount,
				"imprest_recoup_id": self.name,
				"balance_amount": self.total_amount,
				"project": self.project
			})
			ima.insert()
			ima.submit()
			frappe.msgprint("Imprest Advance created. {}".format(frappe.get_desk_link("Imprest Advance", ima.name)))

@frappe.whitelist()
def get_imprest_recoup_account(recoup_type, company):
	account = frappe.db.get_value(
		"Imprest Recoup Account", {"parent": recoup_type, "company": company}, "default_account"
	)
	if not account:
		frappe.throw(
			_("Set the default account for the {0} {1}").format(
				frappe.bold("Recoup Type"), get_link_to_form("Recoup Type", recoup_type)
			)
		)
	return {"account": account}


def get_permission_query_conditions(user):
	if not user: user = frappe.session.user
	user_roles = frappe.get_roles(user)

	if user == "Administrator" or "System Manager" in user_roles or "Accounts User" in user_roles or "Account Manager" in user_roles: 
		return

	return """(
		`tabImprest Recoup`.owner = '{user}'
		or
		exists(select 1
			from `tabEmployee` as e
			where e.branch = `tabImprest Recoup`.branch
			and e.user_id = '{user}')
		or
		exists(select 1
			from `tabEmployee` e, `tabAssign Branch` ab, `tabBranch Item` bi
			where e.user_id = '{user}'
			and ab.employee = e.name
			and bi.parent = ab.name
			and bi.branch = `tabImprest Recoup`.branch)
	)""".format(user=user)