# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils.data import time_diff_in_hours
from frappe.utils import cstr, flt, fmt_money, formatdate, nowdate, money_in_words
from frappe.model.mapper import get_mapped_doc
from erpnext.controllers.accounts_controller import AccountsController
from erpnext.custom_utils import check_uncancelled_linked_doc, check_future_date, check_budget_available
from erpnext.maintenance.maintenance_utils import get_equipment_ba
from erpnext.accounts.doctype.business_activity.business_activity import get_default_ba
from frappe import msgprint, _
import datetime
class JobCard(AccountsController):
	def validate(self):
		check_future_date(self.posting_date)
		if self.finish_date:
			check_future_date(self.finish_date)
		self.update_breakdownreport()

		cc_amount = {}
		self.services_amount = self.goods_amount = 0
		for a in self.items:
			if a.which in cc_amount:
				cc_amount[a.which] = flt(cc_amount[a.which]) + flt(a.charge_amount)
			else:
				cc_amount[a.which] = flt(a.charge_amount)
		if 'Service' in cc_amount:
			self.services_amount = cc_amount['Service']
		if 'Item' in cc_amount:
			self.goods_amount = cc_amount['Item']
		self.total_amount = flt(self.services_amount) + flt(self.goods_amount)
		self.outstanding_amount = self.total_amount

	def on_submit(self):
		self.check_items()
		if not self.repair_type:
			frappe.throw("Specify whether the maintenance is Major or Minor")
		if not self.finish_date:
			frappe.throw("Please enter Job Out Date")
		else:
			if self.finish_date < self.posting_date:
				frappe.throw("Job Out Date should be greater than or equal to Job In Date")
			self.update_reservation()

		if self.owned_by == "Own Branch" and self.out_source == 0:
			self.db_set("outstanding_amount", 0)

		if self.supplier and self.out_source and not self.settled_using_imprest:
			maintenance_account = frappe.db.get_single_value("Maintenance Accounts Settings", "maintenance_expense_account")
			check_budget_available(self.cost_center,maintenance_account,self.finish_date,self.total_amount,self.business_activity)
			self.commit_budget(maintenance_account)
			self.consume_budget(maintenance_account)
			self.make_gl_entry()
		else:
			self.post_journal_entry()

		self.update_breakdownreport()

	def before_cancel(self):
		check_uncancelled_linked_doc(self.doctype, self.name)
		cl_status = frappe.db.get_value("Journal Entry", self.journal_entry, "docstatus")
		if cl_status and cl_status != 2:
			frappe.throw("You need to cancel the journal entry related to this job card first!")
		
		self.db_set('journal_entry', None)

	def on_cancel(self):
		bdr = frappe.get_doc("Break Down Report", self.break_down_report)
		if bdr.job_card == self.name:
			bdr.db_set("job_card", None)

		if self.supplier and self.out_source:
			self.make_gl_entry()	
			self.cancel_budget_entry()

		self.cancel_budget_entry()
			
		bdr = frappe.get_doc("Break Down Report", self.break_down_report)
		if bdr.job_card == self.name:
			bdr.db_set("job_card", None)
	
	def get_default_settings(self):
		goods_account = frappe.db.get_single_value("Maintenance Accounts Settings", "default_goods_account")
		services_account = frappe.db.get_single_value("Maintenance Accounts Settings", "default_services_account")
		receivable_account = frappe.db.get_single_value("Maintenance Accounts Settings", "default_receivable_account")
		maintenance_account = frappe.db.get_single_value("Maintenance Accounts Settings", "maintenance_expense_account")

		return goods_account, services_account, receivable_account, maintenance_account

	def check_items(self):
		if not self.items:
			frappe.throw("Cannot submit Job Card with empty job details")
		else:
			for a in self.items:
				if flt(a.amount) == 0: 
					frappe.throw("Cannot submit Job Card without cost details")

	def post_journal_entry(self):
		if not self.total_amount:
			frappe.throw(_("Amount should be greater than zero"))
		self.posting_date = self.finish_date
		ba = self.business_activity

		payable_account = self.expense_account
		maintenance_account = frappe.db.get_single_value("Maintenance Accounts Settings", "maintenance_expense_account")
			
		if not maintenance_account:
			frappe.throw("Setup Default Goods Account in Maintenance Setting")
		if not payable_account:
			frappe.throw("Payable Account in mandatory")

		r = []
		if self.remarks:
			r.append(_("Note: {0}").format(self.remarks))

		remarks = ("").join(r) 

		je = frappe.new_doc("Journal Entry")

		je.update({
			"doctype": "Journal Entry",
			"voucher_type": "Bank Entry",
			"naming_series": "Bank Payment Voucher",
			"title": "Job Card - " + self.name,
			"user_remark": remarks if remarks else "Note: " + "Job Card - " + self.name,
			"posting_date": self.posting_date,
			"company": self.company,
			"total_amount_in_words": money_in_words(self.total_amount),
			"branch": self.branch
		})

		je.append("accounts",{
			"account": maintenance_account,
			"debit_in_account_currency": self.total_amount,
			"cost_center": self.cost_center,
			"reference_type": "Job Card",
			"reference_name": self.name,
			"business_activity": ba
		})

		je.append("accounts",{
			"account": payable_account,
			"credit_in_account_currency": self.total_amount,
			"cost_center": self.cost_center,
			"party_check": 0,
			"party_type": "Supplier",
			"party": self.supplier,
			"business_activity": ba
		})

		je.insert()

		self.db_set("journal_entry",je.name)
		frappe.msgprint(_('Journal Entry {} posted to accounts').format(frappe.get_desk_link(je.doctype,je.name)))

	def make_gl_entry(self):
		if self.total_amount:
			from erpnext.accounts.general_ledger import make_gl_entries
			gl_entries = []
			self.posting_date = self.finish_date

			maintenance_account = frappe.db.get_single_value("Maintenance Accounts Settings", "maintenance_expense_account")
			payable_account = frappe.db.get_value("Company", self.company,"default_payable_account")
			if not maintenance_account:
				frappe.throw("Setup Default Goods Account in Maintenance Setting")
			if not payable_account:
				frappe.throw("Setup Default Payable Account in Company Setting")

			gl_entries.append(
				self.get_gl_dict({
					"account":  maintenance_account,
					"against": self.supplier,
					"debit": self.total_amount,
					"debit_in_account_currency": self.total_amount,
					"against_voucher": self.name,
					"against_voucher_type": self.doctype,
					"cost_center": self.cost_center,
					"business_activity": self.business_activity
				}, self.currency)
			)
			gl_entries.append(
				self.get_gl_dict({
					"account": payable_account,
					"party_type": "Supplier",
					"party": self.supplier,
					"against": self.supplier,
					"credit": self.total_amount,
					"credit_in_account_currency": self.total_amount,
					"business_activity": self.business_activity,
					"cost_center": self.cost_center
					}, self.currency)
				)
			make_gl_entries(gl_entries, cancel=(self.docstatus == 2),update_outstanding="Yes", merge_entries=False)

	def make_gl_entries(self):
		if self.total_amount:
			from erpnext.accounts.general_ledger import make_gl_entries
			gl_entries = []
			self.posting_date = self.finish_date
			ba = get_default_ba()

			goods_account = frappe.db.get_single_value("Maintenance Accounts Settings", "default_goods_account")
			services_account = frappe.db.get_single_value("Maintenance Accounts Settings", "default_services_account")
			receivable_account = frappe.db.get_single_value("Maintenance Accounts Settings", "default_receivable_account")
			if not goods_account:
				frappe.throw("Setup Default Goods Account in Maintenance Setting")
			if not services_account:
				frappe.throw("Setup Default Services Account in Maintenance Setting")
			if not receivable_account:
				frappe.throw("Setup Default Receivable Account in Maintenance Setting")
						
			gl_entries.append(
				self.get_gl_dict({
					"account":  receivable_account,
					"party_type": "Customer",
					"party": self.customer,
					"against": receivable_account,
					"debit": self.total_amount,
					"debit_in_account_currency": self.total_amount,
					"against_voucher": self.name,
					"against_voucher_type": self.doctype,
					"cost_center": self.cost_center,
					"business_activity": ba
					}, self.currency)
			)

			if self.goods_amount:
				gl_entries.append(
					self.get_gl_dict({
						"account": goods_account,
						"against": self.customer,
						"credit": self.goods_amount,
						"credit_in_account_currency": self.goods_amount,
						"business_activity": ba,
						"cost_center": self.cost_center
					}, self.currency)
				)
			if self.services_amount:
				gl_entries.append(
					self.get_gl_dict({
						"account": services_account,
						"against": self.customer,
						"credit": self.services_amount,
						"credit_in_account_currency": self.services_amount,
						"business_activity": ba,
						"cost_center": self.cost_center
					}, self.currency)
				)
			make_gl_entries(gl_entries, cancel=(self.docstatus == 2),update_outstanding="No", merge_entries=False)

	def commit_budget(self, maintenance_account):
		commit_bud = frappe.get_doc({
			"doctype": "Committed Budget",
			"account": maintenance_account,
			"cost_center": self.cost_center,
			"reference_type": "Job Card",
			"reference_no": self.name,
			"reference_date": self.finish_date,
			"amount": self.total_amount
		})
		commit_bud.flags.ignore_permissions=1
		commit_bud.submit()

	def consume_budget(self,maintenance_account):
		consume = frappe.get_doc({
			"doctype": "Consumed Budget",
			"account": maintenance_account,
			"cost_center": self.cost_center,
			"reference_type": "Job Card",
			"reference_no": self.name,
			"reference_date": self.finish_date,
			"amount": self.total_amount
		})
		consume.flags.ignore_permissions = 1
		consume.submit()

	def cancel_budget_entry(self):
		frappe.db.sql("delete from `tabCommitted Budget` where po_no = %s", self.name)
		frappe.db.sql("delete from `tabConsumed Budget` where po_no = %s", self.name)
			
	def update_reservation(self):
		frappe.db.sql("update `tabEquipment Reservation Entry` set to_date = %s, to_time = %s where docstatus = 1 and ehf_name = %s", (self.finish_date, self.job_out_time, self.break_down_report))
		frappe.db.sql("update `tabEquipment Status Entry` set to_date = %s, to_time = %s where docstatus = 1 and ehf_name = %s", (self.finish_date, self.job_out_time, self.break_down_report))

	def update_breakdownreport(self):
		bdr = frappe.get_doc("Break Down Report", self.break_down_report)
		bdr.db_set("job_card", self.name)

	@frappe.whitelist()
	def make_journal_entry(self):
		if not self.total_amount:
			frappe.throw(_("Amount should be greater than zero"))
		self.posting_date = self.finish_date
		ba = self.business_activity

		payable_account = frappe.db.get_value("Company", self.company,"default_payable_account")
		bank_account = frappe.db.get_value("Company", self.company,"default_bank_account")

		if not bank_account:
			frappe.throw("Setup Default Bank Account in Company Setting")
		if not payable_account:
			frappe.throw("Setup Payable Bank Account in Company Setting")

		r = []
		if self.remarks:
			r.append(_("Note: {0}").format(self.remarks))

		remarks = ("").join(r) 

		je = frappe.new_doc("Journal Entry")

		je.update({
			"doctype": "Journal Entry",
			"voucher_type": "Bank Entry",
			"naming_series": "Bank Payment Voucher",
			"title": "Job Card - " + self.name,
			"user_remark": remarks if remarks else "Note: " + "Job Card - " + self.name,
			"posting_date": self.posting_date,
			"company": self.company,
			"total_amount_in_words": money_in_words(self.total_amount),
			"branch": self.branch
		})

		je.append("accounts",{
			"account": payable_account,
			"debit_in_account_currency": self.total_amount,
			"cost_center": self.cost_center,
			"party_check": 0,
			"party_type": "Supplier",
			"party": self.supplier,
			"reference_type": "Job Card",
			"reference_name": self.name,
			"business_activity": ba
		})

		je.append("accounts",{
			"account": bank_account,
			"credit_in_account_currency": self.total_amount,
			"cost_center": self.cost_center,
			"business_activity": ba
		})

		je.insert()
		self.db_set("journal_entry",je.name)
		frappe.msgprint(_('Journal Entry {} posted to accounts').format(frappe.get_desk_link(je.doctype,je.name)))

@frappe.whitelist()
def get_payment_entry(doc_name, total_amount):
	query = """
		select je.docstatus from `tabJournal Entry` je, `tabJob Card` jc 
		where jc.journal_entry = je.name and jc.name='{}'
	""".format(doc_name)
	journal_entry = frappe.db.sql(query, as_dict=1)
	if journal_entry:
		if journal_entry[0].docstatus == 1:
			frappe.db.set_value("Job Card", doc_name, "payment_status", "Paid")
			return ("Paid")
		else:
			frappe.db.set_value("Job Card", doc_name, 'payment_status', "Not Paid")
			return ("Not Paid")