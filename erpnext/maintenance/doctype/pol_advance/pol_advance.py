# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from erpnext.accounts.doctype.business_activity.business_activity import get_default_ba
from erpnext.accounts.general_ledger import make_gl_entries
from erpnext.controllers.accounts_controller import AccountsController
from erpnext.custom_utils import check_budget_available
import json
from frappe import _, msgprint
from frappe.utils import flt, cint, nowdate, getdate, formatdate, money_in_words


class PolAdvance(AccountsController):
	def validate(self):
		self.validate_cheque_info()
		self.od_adjustment()
		if self.is_opening and flt(self.od_amount) > flt(0.0):
			self.od_outstanding_amount = flt(self.od_amount)
		else:
			self.od_amount = self.od_outstanding_amount = 0.0

	def before_cancel(self):
		if self.is_opening:
			return
		if self.journal_entry:
			for t in frappe.get_all("Journal Entry", ["name"], {"name": self.journal_entry, "docstatus": ("<",2)}):
				frappe.throw(_('Journal Entry {} for this transaction needs to be cancelled first').format(frappe.get_desk_link(self.doctype,self.journal_entry)),title='Not permitted')

	def on_submit(self):
		if not self.is_opening:
			# check_budget_available(self.cost_center,advance_account,self.entry_date,self.amount,self.business_activity)
			self.update_od_balance()
			self.post_journal_entry()

	def on_cancel(self):
		if not self.is_opening:
			# self.cancel_budget_entry()
			self.update_od_balance()

	def update_od_balance(self):
		if self.is_opening:
			return
		for d in self.items:
			doc = frappe.get_doc('Pol Advance',d.reference)
			if self.docstatus == 2:
				if flt(self.adjusted_amount) - flt(doc.od_amount) < 0:
					self.adjusted_amount = 0
					self.balance_amount = flt(self.amount)
				else:
					self.adjusted_amount = flt(self.adjusted_amount) - flt(doc.od_amount)
					self.balance_amount = flt(self.balance_amount) + flt(doc.od_amount)
				self.od_amount = 0
				self.od_outstanding_amount = 0
				doc.od_adjusted_amount = 0 
				doc.od_outstanding_amount = doc.od_amount
				doc.save(ignore_permissions=True)
			elif self.docstatus == 1:
				if flt(self.adjusted_amount) == flt(self.amount):
					self.od_amount += doc.od_amount
					self.od_outstanding_amount += doc.od_amount
				elif flt(self.adjusted_amount) + flt(doc.od_amount) > flt(self.amount):
					excess_amount = flt(self.adjusted_amount) + flt(doc.od_amount) - flt(self.amount)
					self.od_amount += flt(excess_amount)
					self.od_outstanding_amount += flt(excess_amount)
					if self.adjusted_amount != self.amount:
						self.adjusted_amount = flt(self.amount)
						self.balance_amount = flt(self.amount) - flt(self.adjusted_amount)
				else:
					self.adjusted_amount += flt(doc.od_amount)
					self.balance_amount = flt(self.amount) - flt(self.adjusted_amount)
				doc.od_adjusted_amount = doc.od_outstanding_amount 
				doc.od_outstanding_amount = 0
				doc.save(ignore_permissions=True)
				self.save()

	def od_adjustment(self):
		data = frappe.db.sql('''
			SELECT
				name as reference, od_amount,
				od_outstanding_amount
			FROM `tabPol Advance`
			WHERE od_outstanding_amount > 0
			and docstatus = 1
			and equipment = '{}'
		'''.format(self.equipment),as_dict=True)
		
		if data :
			self.set('items',[])
			for d in data:
				row = self.append('items',{})
				row.update(d)

	def validate_cheque_info(self):
		if self.cheque_date and not self.cheque_no:
			frappe.msgprint(_("Cheque No is mandatory if you entered Cheque Date"), raise_exception=1)
  
	# def cancel_budget_entry(self):
	# 	frappe.db.sql("delete from `tabConsumed Budget` where reference_no = %s", self.name) 
   
	def post_journal_entry(self):
		if not self.amount:
			frappe.throw(_("Amount should be greater than zero"))
		if self.is_opening:
			return

		self.posting_date = self.entry_date
		ba = self.business_activity

		credit_account = self.expense_account
		advance_account = frappe.db.get_value("Company", self.company, "pol_advance_account")
			
		if not credit_account:
			frappe.throw("Expense Account is mandatory")
		if not advance_account:
			frappe.throw("Setup POL Advance Accounts in company {}".format(frappe.get_desk_link(self.company)))

		account_type = frappe.db.get_value("Account", credit_account, "account_type")
		voucher_type = "Journal Entry"
		voucher_series = "Journal Voucher"
		party_type = ''
		party = ''
		if account_type == "Bank":
			voucher_type = "Bank Entry"
			voucher_series = "Bank Receipt Voucher" if self.payment_type == "Receive" else "Bank Payment Voucher"
		elif account_type == "Payable":
			party_type = self.party_type
			party = self.supplier

		r = []
		if self.cheque_no:
			if self.cheque_date:
				r.append(_('Reference #{0} dated {1}').format(self.cheque_no, formatdate(self.cheque_date)))
			else:
				frappe.msgprint(_("Please enter Cheque Date date"), raise_exception=frappe.MandatoryError)
		if self.user_remark:
			r.append(_("Note: {0}").format(self.user_remark))

		remarks = ("").join(r)

		je = frappe.new_doc("Journal Entry")

		je.update({
			"doctype": "Journal Entry",
			"voucher_type": voucher_type,
			"naming_series": voucher_series,
			"title": "POL Advance - " + self.equipment,
			"user_remark": remarks if remarks else "Note: " + "POL Advance - " + self.equipment,
			"posting_date": self.posting_date,
			"company": self.company,
			"total_amount_in_words": money_in_words(self.amount),
			"branch": self.fuelbook_branch,
		})

		je.append("accounts",{
			"account": advance_account,
			"debit_in_account_currency": self.amount,
			"cost_center": self.cost_center,
			"party_check": 1,
			"party_type": self.party_type,
			"party": self.supplier,
			"business_activity": ba
		})

		je.append("accounts",{
			"account": credit_account,
			"credit_in_account_currency": self.amount,
			"cost_center": self.cost_center,
			"reference_type": "Pol Advance",
			"reference_name": self.name,
			"party_type": party_type,
			"party": party,
			"business_activity": ba
		})

		je.insert()

		self.db_set("journal_entry",je.name)
		frappe.msgprint(_('Journal Entry {} posted to accounts').format(frappe.get_desk_link(je.doctype,je.name)))