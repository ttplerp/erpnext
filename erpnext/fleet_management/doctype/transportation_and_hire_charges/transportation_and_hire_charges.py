# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _, qb, throw, bold
from erpnext.custom_utils import check_future_date
from erpnext.controllers.accounts_controller import AccountsController
from frappe.utils import flt, cint, money_in_words
from erpnext.accounts.utils import get_tds_account, get_account_type
from erpnext.accounts.general_ledger import (make_gl_entries, merge_similar_entries)
from erpnext.accounts.party import get_party_account
from frappe.model.naming import make_autoname

class TransportationandHireCharges(AccountsController):
	def autoname(self):
		abbr = frappe.db.get_value("Charge Type", self.invoice_type, "abbr")
		if abbr:
			self.name = make_autoname(f"{abbr}-.YYYY.-.MM.-.####")
		else:
			frappe.throw(_("Abbreviation not found for Charge Type: {0}").format(self.invoice_type), title="Missing Abbreviation")

	def validate(self):
		check_future_date(self.posting_date)		
		self.calculate_totals()
		self.validate_amount()

	def on_submit(self):
		self.update_reference_document()
		self.make_gl_entry()

	def on_cancel(self):
		self.update_reference_document()
		self.make_gl_entry(cancel=True)

	def validate_amount(self):
		for d in self.material_issue_details:
			if flt(d.allocated_amount) > flt(d.total_amount):
				frappe.throw("Row #{}. Allocated amount {} cannot be more than {}".format(
					frappe.bold(d.idx), 
					frappe.bold(frappe.format_value(d.allocated_amount, {"fieldtype":"Currency"})),
					frappe.bold(frappe.format_value(d.total_amount, {"fieldtype":"Currency"}))
				))
		
		if flt(self.net_payable) < 0:
			frappe.throw("{} has more deduction than grand total {}".format(
				frappe.bold(self.supplier), 
				frappe.bold(frappe.format_value(self.amount, {"fieldtype":"Currency"}))
			))

	@frappe.whitelist()
	def get_equiment_issue_detail(self):
		if self.party_type == "Customer":
			return
		
		res = frappe.db.sql("""
							select name, outstanding_amount, posting_date, debit_account
							from `tabEquipment Material Issue`
							where docstatus = 1
							and supplier = %s 
					  		and outstanding_amount > 0
							""", self.party, as_dict=True)
		self.set("material_issue_details", [])

		if res:
			for a in res:
				entry = {
					'reference_name': a.name,
					'posting_date': a.posting_date,
					'total_amount': a.outstanding_amount,
					'allocated_amount': a.outstanding_amount,
					'account': a.debit_account,
				}
				self.append("material_issue_details", entry)
		# else:
		# 	frappe.msgprint("No entries found.")

	def get_total_allocated(self):
		total = 0
		for d in self.material_issue_details:
			total += flt(d.allocated_amount)
		return total
	
	def get_total_deduction(self):
		total = 0
		for d in self.deduction_items:
			total += flt(d.amount)
		return total
	
	def get_total_additional(self):
		total = 0
		for d in self.addition_items:
			total += flt(d.amount)
		return total

	@frappe.whitelist()
	def calculate_totals(self):
		self.total_additional_amount = self.get_total_additional()
		self.total_allocated_amount = self.get_total_allocated()
		self.total_deduction_amount = self.get_total_deduction()
		self.grand_total = flt(self.amount) + flt(self.total_additional_amount) if self.total_additional_amount else self.amount
		
		if self.tds_percent:
			self.tds_amount = flt(flt(self.grand_total, 2) * flt(self.tds_percent, 2) / 100.0, 2)
			self.tds_account = get_tds_account(self.tds_percent, self.company)
		else:
			self.tds_amount = 0
			self.tds_account = None

		self.net_payable = self.outstanding_amount = flt(self.grand_total) - flt(self.total_deduction_amount) - flt(self.total_allocated_amount) - flt(self.tds_amount)

	def update_reference_document(self, cancel=False):
		for item in self.material_issue_details:
			allocated_amount = 0.0
			if flt(item.allocated_amount) > 0:
				balance_amount = frappe.db.get_value("Equipment Material Issue", item.reference_name, "outstanding_amount")
				if flt(balance_amount) < flt(item.allocated_amount) and self.docstatus < 2:
					frappe.throw(_("Row #{0} : Allocated amount Nu. {1}/- cannot be more than Advance Balance Nu. {2}/-").format(item.reference_name, "{:,.2f}".format(flt(item.allocated_amount)),"{:,.2f}".format(flt(balance_amount))))
				else:
					allocated_amount = -1 * flt(item.allocated_amount) if cancel else flt(item.allocated_amount)
					doc = frappe.get_doc("Equipment Material Issue", item.reference_name)
					doc.outstanding_amount = flt(doc.outstanding_amount) - flt(allocated_amount)
					doc.save(ignore_permissions = True)

	def make_gl_entry(self, cancel=False):
		# payable == 58,600     add 	= 10,000
		# tds     == 1,800      amount 	= 50,000
		# mat_iss == 1,000
		# dedut   == 400    
		gl_entries = []
		self.make_supplier_gl_entry(gl_entries)
		self.make_additional_gl_entries(gl_entries)
		self.deduction_gl_entries(gl_entries)
		self.make_tds_gl_entries(gl_entries)
		self.make_material_issue_gl_entries(gl_entries)
		self.make_total_amount_entries(gl_entries)
		gl_entries = merge_similar_entries(gl_entries)
		
		make_gl_entries(gl_entries, update_outstanding="No", cancel=cancel)

	def deduction_gl_entries(self, gl_entries):
		for d in self.deduction_items:
			gl_entries.append(
				self.get_gl_dict(
					{
						"account": d.account,
						"credit": flt(d.amount),
						"credit_in_account_currency": flt(d.amount),
						"against_voucher": self.name,
						"against_voucher_type": self.doctype,
						"party_type": self.party_type,
						"party": self.party,
						"cost_center": self.cost_center,
						"voucher_type": self.doctype,
						"voucher_no": self.name,
					},
					self.currency,
				)
			)

	def make_material_issue_gl_entries(self, gl_entries):
		for d in self.material_issue_details:
			gl_entries.append(
				self.get_gl_dict({
					"account": d.account,
					"credit": flt(d.allocated_amount),
					"credit_in_account_currency": flt(d.allocated_amount),
					"against_voucher": self.name,
					"against_voucher_type": self.doctype,
					"party_type": self.party_type,
					"party": self.party,
					"cost_center": self.cost_center,
					"voucher_type": self.doctype,
					"voucher_no": self.name,
				}, self.currency)
			)
	
	def make_additional_gl_entries(self, gl_entries):
		for d in self.addition_items:
			gl_entries.append(
				self.get_gl_dict({
					"account": d.account,
					"debit": flt(d.amount),
					"debit_in_account_currency": flt(d.amount),
					"against_voucher": self.name,
					"against_voucher_type": self.doctype,
					"party_type": self.party_type,
					"party": self.party,
					"cost_center": self.cost_center,
					"voucher_type": self.doctype,
					"voucher_no": self.name,
				}, self.currency)
			)
	

	def make_total_amount_entries(self, gl_entries):
		expense_account = frappe.db.get_value("Charge Type", self.invoice_type, "default_expense_account")
		if not expense_account:
			frappe.throw(
				"The default expense account is not set for the selected Charge Type. Please configure it in the Charge Type record: {}".format(
					frappe.get_desk_link("Charge Type", self.invoice_type)
				),
				title="Expense Account Missing"
			)

		gl_entries.append(
			self.get_gl_dict({
				"account": expense_account,
				"debit": self.amount,
				"debit_in_account_currency": self.amount,
				"against_voucher": self.name,
				"against_voucher_type": self.doctype,
				"party_type": self.party_type,
				"party": self.party,
				"cost_center": self.cost_center,
				"voucher_type": self.doctype,
				"voucher_no": self.name,
			}, self.currency)
		)

	def make_tds_gl_entries(self, gl_entries):
		if flt(self.tds_amount) > 0:
			gl_entries.append(
				self.get_gl_dict(
					{
						"account": self.tds_account,
						"credit": flt(self.tds_amount, 2),
						"credit_in_account_currency": flt(self.tds_amount, 2),
						"against_voucher": self.name,
						"against_voucher_type": self.doctype,
						"party_type": self.party_type,
						"party": self.party,
						"cost_center": self.cost_center,
						"voucher_type": self.doctype,
						"voucher_no": self.name,
					},
					self.currency,
				)
			)
			
	def make_supplier_gl_entry(self, gl_entries):
		payable_account = frappe.db.get_value("Charge Type", self.invoice_type, "default_payable_account")
		if not payable_account:
			frappe.throw(
				"The default payable account is not set for the selected Charge Type. Please configure it in the Charge Type record: {}".format(
					frappe.get_desk_link("Charge Type", self.invoice_type)
				),
				title="Payable Account Missing"
			)
		gl_entries.append(
			self.get_gl_dict(
				{
					"account": payable_account,
					"credit": flt(self.outstanding_amount),
					"credit_in_account_currency": flt(self.outstanding_amount),
					"against_voucher": self.name,
					"party_type": "Employee" if self.settle_imprest_advance else self.party_type,
					"party": self.imprest_party if self.settle_imprest_advance else self.party,
					"against_voucher_type": self.doctype,
					"cost_center": self.cost_center,
					"voucher_type": self.doctype,
					"voucher_no": self.name,
				},
				self.currency,
			)
		)