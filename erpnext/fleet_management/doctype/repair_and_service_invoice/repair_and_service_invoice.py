# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.mapper import get_mapped_doc
from frappe.model.document import Document
from erpnext.custom_utils import check_future_date
from erpnext.controllers.accounts_controller import AccountsController
from frappe import _, qb, throw, msgprint
from frappe.utils import flt, cint, money_in_words
from erpnext.accounts.party import get_party_account
from erpnext.accounts.utils import get_tds_account,get_account_type

class RepairAndServiceInvoice(AccountsController):
	def validate(self):
		check_future_date(self.posting_date)
		self.calculate_total()
		self.set_status()
		if not self.credit_account:
			self.credit_account = get_party_account(self.party_type,self.party,self.company)
		if not self.tds_account and flt(self.tds_percent) > 0:
			self.tds_account = get_tds_account(self.tds_percent, self.company)
	def on_submit(self):
		self.make_gl_entry()
		self.update_repair_and_service()
		# self.post_journal_entry()

	def on_cancel(self):
		self.ignore_linked_doctypes = ("GL Entry", "Stock Ledger Entry", "Payment Ledger Entry")
		self.make_gl_entry()
		self.update_repair_and_service()

	def update_repair_and_service(self):
		if not self.repair_and_services:
			return
		value = 1
		if self.docstatus == 2:
			value = 0
		doc = frappe.get_doc("Repair And Services", self.repair_and_services)
		doc.db_set("paid", value)
	
	def set_status(self, update=False, status=None, update_modified=True):
		if self.is_new():
			self.status = "Draft"
			return

		outstanding_amount = flt(self.outstanding_amount, 2)
		if not status:
			if self.docstatus == 2:
				status = "Cancelled"
			elif self.docstatus == 1:
				if outstanding_amount > 0 and self.total_amount > outstanding_amount:
					self.status = "Partly Paid"
				elif outstanding_amount > 0 :
					self.status = "Unpaid"
				elif outstanding_amount <= 0:
					self.status = "Paid"
				else:
					self.status = "Submitted"
			else:
				self.status = "Draft"

		if update:
			self.db_set("status", self.status, update_modified=update_modified)

	def calculate_total(self):
		self.total_amount = self.grand_total = self.outstanding_amount = self.tds_amount = 0
		for a in self.items:
			a.charge_amount = flt(flt(a.rate) * flt(a.qty),2)
			self.grand_total += flt(a.charge_amount,2)
		if flt(self.tds_percent) > 0:
			self.tds_amount = flt(self.grand_total) * flt(self.tds_percent) / 100
		self.total_amount =	self.outstanding_amount = flt(self.grand_total) - flt(self.tds_amount)

	def make_gl_entry(self):
		from erpnext.accounts.general_ledger import make_gl_entries
		gl_entries = []
		expense_account = frappe.db.get_value("Equipment Category", self.equipment_category, "r_m_expense_account")
		if not expense_account:
			expense_account = frappe.db.get_value("Company", self.company, "repair_and_service_expense_account")
		
		if not expense_account:
			frappe.throw(
				"Setup Repair And Service Expense Account in Equipment Category {}".format(self.equipment_category))

		gl_entries.append(
			self.get_gl_dict({
				"account": expense_account,
				"debit": self.grand_total,
				"debit_in_account_currency": self.grand_total,
				"voucher_no": self.name,
				"voucher_type": self.doctype,
				"cost_center": self.cost_center,
			}, self.currency)
		)
		gl_entries.append(
			self.get_gl_dict({
				"account": self.credit_account,
				"party_type": self.party_type,
				"party": self.party,
				"credit": self.total_amount,
				"credit_in_account_currency": self.total_amount,
				"cost_center": self.cost_center,
				"voucher_no":self.name,
				"voucher_type":self.doctype,
				"against_voucher":self.name,
				"against_voucher_type":self.doctype
			}, self.currency)
		)
		if flt(self.tds_percent) > 0:
			gl_entries.append(
				self.get_gl_dict({
					"account": self.tds_account,
					"credit": self.tds_amount,
					"credit_in_account_currency": self.tds_amount,
					"cost_center": self.cost_center,
					"voucher_no":self.name,
					"voucher_type":self.doctype,
					"against_voucher":self.name,
					"against_voucher_type":self.doctype
				}, self.currency)
			)
		make_gl_entries(gl_entries, update_outstanding="No", cancel=(self.docstatus == 2), merge_entries=False)

	@frappe.whitelist()
	def post_journal_entry(self):
		if self.journal_entry and frappe.db.exists("Journal Entry",{"name":self.journal_entry,"docstatus":("!=",2)}):
			frappe.msgprint(_("Journal Entry Already Exists {}".format(frappe.get_desk_link("Journal Entry",self.journal_entry))))
		if not flt(self.outstanding_amount) > 0:
			frappe.throw(_("Outstanding Amount should be greater than zero"))
		
		credit_account = self.credit_account
	
		if not credit_account:
			frappe.throw("Credit Account is mandatory")
	
		bank_account = frappe.db.get_value("Branch",self.branch, "expense_bank_account")
		if not bank_account:
			frappe.throw(_("Default bank account is not set in company {}".format(frappe.bold(self.company))))
		# Posting Journal Entry
		je = frappe.new_doc("Journal Entry")
		je.flags.ignore_permissions=1
		je.update({
			"doctype": "Journal Entry",
			"voucher_type": "Bank Entry",
			"naming_series": "Bank Payment Voucher",
			"title": "Transporter Payment "+ self.party,
			"user_remark": "Note: " + "Repair And Service - " + self.party,
			"posting_date": self.posting_date,
			"company": self.company,
			"total_amount_in_words": money_in_words(self.outstanding_amount),
			"branch": self.branch,
			"reference_type":self.doctype,
			"referece_doctype":self.name
		})
		je.append("accounts",{
			"account": credit_account,
			"debit_in_account_currency": self.outstanding_amount,
			"cost_center": self.cost_center,
			"party_check": 1,
			"party_type": self.party_type,
			"party": self.party,
			"reference_type": self.doctype,
			"reference_name": self.name
		})
		je.append("accounts",{
			"account": bank_account,
			"credit_in_account_currency": self.outstanding_amount,
			"cost_center": self.cost_center
		})

		je.insert()
		#Set a reference to the claim journal entry
		self.db_set("journal_entry",je.name)
		frappe.msgprint(_('Journal Entry {0} posted to accounts').format(frappe.get_desk_link("Journal Entry",je.name)))
	
# permission query
def get_permission_query_conditions(user):
	if not user: user = frappe.session.user
	user_roles = frappe.get_roles(user)

	if user == "Administrator" or "System Manager" in user_roles: 
		return

	return """(
		`tabRepair And Services Invoice`.owner = '{user}'
		or
		exists(select 1
			from `tabEmployee` as e
			where e.branch = `tabRepair And Services Invoice`.branch
			and e.user_id = '{user}')
		or
		exists(select 1
			from `tabEmployee` e, `tabAssign Branch` ab, `tabBranch Item` bi
			where e.user_id = '{user}'
			and ab.employee = e.name
			and bi.parent = ab.name
			and bi.branch = `tabRepair And Services Invoice`.branch)
	)""".format(user=user)