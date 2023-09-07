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
		self.populate_imprest_advance()

	def calculate_amount(self):
		total_payable_amt, tot_bal_amt = 0,0
		for d in self.imprest_advance_list:
			tot_bal_amt += d.balance_amount

		for d in self.items:
			total_payable_amt += d.amount

		self.total_amount = total_payable_amt

		if self.docstatus != 1:
			if tot_bal_amt < self.total_amount:
				frappe.throw("Expense amount cannot be more than balance amount.")
		
	def on_submit(self):
		self.update_advance()
		self.post_journal_entry()
	
	def before_cancel(self):
		if self.journal_entry:
			je = frappe.get_doc("Journal Entry", self.journal_entry)
			for a in je.accounts:
				frappe.db.sql("""
					update `tabJournal Entry Account` set reference_type = NULL, reference_name = NULL
					where name = '{}'
				""".format(a.name))
			frappe.db.sql("""
				update `tabReimbursement` set journal_entry = NULL
				where name = '{}'
			""".format(self.name))
			je.cancel()
			# for t in frappe.get_all("Journal Entry", ["name"], {"name": self.journal_entry, "docstatus": ("<",2)}):
			# 	frappe.throw(_('Journal Entry  <a href="#Form/Journal Entry/{0}">{0}</a> for this transaction needs to be cancelled first').format(self.journal_entry),title='Not permitted')

	def on_cancel(self):
		self.update_advance(1)

	@frappe.whitelist()
	def populate_imprest_advance(self):
		self.set('imprest_advance_list',[])
		data = []
		query = """
			SELECT 
				a.name, a.amount, a.balance_amount, a.journal_entry, a.is_opening
			FROM `tabImprest Advance` a
			WHERE a.docstatus = 1 
			AND a.branch = '{branch}'
			AND a.posting_date <= '{date}'
			AND a.balance_amount > 0
			AND CASE WHEN a.is_opening=0 THEN exists (select 1 from `tabJournal Entry` where name=a.journal_entry and docstatus=1) ELSE a.is_opening END
			ORDER BY a.posting_date
		""".format(branch = self.branch, date=self.posting_date)
		data = frappe.db.sql(query,as_dict=True)

		# if there is no advance with balance than pick latest advance with 0 value
		if not self.total_amount: 
			allocated_amount = 0
		else:
			allocated_amount = self.total_amount
		total_amount_adjusted = 0
		
		if not data:
			frappe.throw("No Imprest Advance")

		for d in data:
			row = self.append('imprest_advance_list',{})
			row.imprest_advance = d.name
			row.advance_amount = d.amount 

			if d.balance_amount >= allocated_amount:
				row.allocated_amount = allocated_amount
				row.balance_amount = d.balance_amount - flt(allocated_amount)
				allocated_amount = 0

			elif d.balance_amount < allocated_amount:
				row.allocated_amount = d.balance_amount
				row.balance_amount = d.balance_amount - flt(row.allocated_amount)
				allocated_amount = flt(allocated_amount) - d.balance_amount
				
		if not self.imprest_advance_list:
			frappe.throw("No Imprest Advance")

	def update_advance(self, cancel=0):
		if cancel == 1:
			for d in self.imprest_advance_list:
				doc = frappe.get_doc("Imprest Advance", d.imprest_advance)
				doc.balance_amount  = flt(doc.balance_amount) + flt(d.allocated_amount)
				doc.adjusted_amount = flt(doc.adjusted_amount) - flt(d.allocated_amount)
				doc.save(ignore_permissions=True)
		else:
			for d in self.imprest_advance_list:
				doc = frappe.get_doc("Imprest Advance", d.imprest_advance)
				doc.balance_amount  = flt(doc.balance_amount) - flt(d.allocated_amount)
				doc.adjusted_amount = flt(doc.adjusted_amount) + flt(d.allocated_amount)
				doc.save(ignore_permissions=True)

	def post_journal_entry(self):
		if not self.total_amount:
			frappe.throw(_("Total Payable Amount should be greater than zero"))

		credit_account = frappe.db.get_value('Company',self.company,'default_imprest_account')
		if not credit_account:
			frappe.throw("Setup Default Imprest Account in Company Settings")

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
			"title": "Reimbursement - " + self.name,
			"user_remark": remarkss if remarkss else "Note: " + "Reimbursement - " + self.name,
			"posting_date": self.posting_date,
			"company": self.company,
			"total_amount_in_words": money_in_words(self.total_amount),
			"branch": self.branch
		})

		je.append("accounts",{
			"account": credit_account,
			"credit_in_account_currency": self.total_amount,
			"cost_center": self.cost_center,
			"reference_type": "Reimbursement",
			"reference_name": self.name,
			"party_type": party_type,
			"party": party,
			"business_activity": self.business_activity,
		})

		for i in self.items:
			je.append("accounts",{
				"account": i.expense_account,
				"debit_in_account_currency": i.amount,
				"cost_center": self.cost_center,
				"business_activity": self.business_activity,
				"party_type": i.party_type,
				"party": i.party,
			})

		je.insert()
		#Set a reference to the claim journal entry
		self.db_set("journal_entry",je.name)
		frappe.msgprint(_('Journal Entry <a href="#Form/Journal Entry/{0}">{0}</a> posted to accounts').format(je.name))