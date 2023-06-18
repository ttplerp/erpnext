# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from erpnext.accounts.doctype.journal_entry.journal_entry import get_tds_account
from frappe.utils import getdate, cint, cstr, flt, fmt_money, formatdate, nowdate
from erpnext.controllers.accounts_controller import AccountsController
from erpnext.custom_utils import generate_receipt_no, check_future_date, get_branch_cc, check_tds_remittance
from erpnext.accounts.doctype.business_activity.business_activity import get_default_ba

class MechanicalPayment(Document):
	def validate(self):
		check_future_date(self.posting_date)
		# self.validate_allocated_amount()
		self.validate_delivery_note()
		self.validate_technical_sanction()
		self.set_missing_values()
		self.clearance_date = None

	def set_missing_values(self):
		self.cost_center = get_branch_cc(self.branch)
		if not self.net_amount:
			frappe.throw("Net Amount cannot be less than Zero")
		if flt(self.tds_amount) < 0:
			frappe.throw("TDS Amount cannot be less than Zero")

	def validate_allocated_amount(self):
		# if not self.receivable_amount > 0 and self.payment_for not in ["Transporter Payment","Maintenance Payment"] and not self.payable_amount:
		# 	frappe.throw("Amount should be greater than 0")	
		to_remove = []
		if self.payment_for != "Job Card": 
			total = flt(self.receivable_amount)
		# if self.payment_for == "Job Card": 
		# 	total = flt(self.payable_amount)
		total_actual = 0
		for d in self.items:
			allocated = 0
			if total > 0 and total >= d.outstanding_amount:
				allocated = d.outstanding_amount
				total_actual += flt(d.outstanding_amount)
			elif total > 0 and total < d.outstanding_amount:
				total_actual += flt(d.outstanding_amount)
				allocated = total
			else:
				allocated = 0
		
			d.allocated_amount = allocated
			total-=allocated
			if d.allocated_amount == 0:
				to_remove.append(d)

		[self.remove(d) for d in to_remove]
		self.actual_amount = total_actual 
		
		if self.receivable_amount > self.actual_amount:
			frappe.throw("Receivable Amount Cannot be grater than Total Outstanding Amount")

	def validate_technical_sanction(self):
		if self.payment_for == "Maintenance Payment":
			for a in self.maintenance_payment_item:
				dtl = frappe.db.sql("select t.technical_sanction as ts, m.name as mno from `tabMechanical Payment` m,\
								`tabMaintenance Payment Item` t where m.name=t.parent and m.docstatus != 2 and \
							t.technical_sanction='{0}' and m.name !='{1}'".format(a.technical_sanction, self.name), as_dict=True)
				if len(dtl) > 0:
					for b in dtl:
						frappe.throw("The Technical Sanction {0} is already in used with Payment No. {1}.".format(b.ts,b.mno));

			# Retrieve Default Account for GL
			self.maintenance_account = frappe.db.get_single_value("Maintenance Accounts Settings", "repair_and_maintenance_expense_account")
			if not self.expense_account:
				self.expense_account = frappe.db.get_value("Branch", self.branch, "expense_bank_account")

	def on_submit(self):
		self.make_gl_entry()
		self.update_ref_doc()
		# self.consume_budget()
	
	def on_cancel(self):
		check_tds_remittance(self.name)
		if self.clearance_date:
			frappe.throw("Already done bank reconciliation.")
		
		self.make_gl_entry()
		self.update_ref_doc(cancel=1)
		# self.cancel_budget_entry()

	def make_gl_entry(self):
		from erpnext.accounts.general_ledger import make_gl_entries
		receivable_account = frappe.db.get_single_value("Maintenance Accounts Settings", "default_receivable_account")
		#creditor_account  = frappe.db.get_value("Company", "default_payable_account")
		#frappe.msgprint("{0}".format(creditor_account))
		creditor_account= frappe.get_doc("Company", self.company).default_payable_account
		if not receivable_account:
			frappe.throw("Setup Default Receivable Account in Maintenance Setting")
		if not creditor_account:
			frappe.throw("Setup Default Payable Account in Company")

		default_ba = get_default_ba()

		gl_entries = []
		if self.payment_for in ["Transporter Payment","Maintenance Payment"]:
			debit_account = self.transportation_account if self.payment_for == "Transporter Payment" else creditor_account #self.maintenance_account
			party_type = "Supplier" if self.payment_for == "Maintenance Payment" else ""
			party = self.supplier if self.payment_for == "Maintenance Payment" else ""
			gl_entries.append(
				self.get_gl_dict({"account": debit_account,
					"debit": flt(self.total_amount),
					"debit_in_account_currency": flt(self.total_amount),
					"cost_center": self.cost_center,
					"party_check": 1,
					"party_type": party_type,
					"party": party,
					"reference_type": self.doctype,
					"reference_name": self.name,
					"business_activity": default_ba,
					"remarks": self.remarks
				})
			)
			if self.other_deduction:
				if not self.other_deduction_account:
					frappe.throw("Required value for Other Deduction Account")
				gl_entries.append(
					self.get_gl_dict({"account": self.other_deduction_account,
						"credit": flt(self.other_deduction),
						"credit_in_account_currency": flt(self.other_deduction),
						"cost_center": self.cost_center,
						"party_check": 1,
						"party_type": party_type,
						"party": party,
						"reference_type": self.doctype,
						"reference_name": self.name,
						"business_activity": default_ba,
						"remarks": self.remarks
					})
				)
			if self.tds_amount:
				gl_entries.append(
					self.get_gl_dict({"account": self.tds_account,
						"credit": flt(self.tds_amount),
						"credit_in_account_currency": flt(self.tds_amount),
						"cost_center": self.cost_center,
						"party_check": 1,
						"reference_type": self.doctype,
						"reference_name": self.name,
						"business_activity": default_ba,
						"remarks": self.remarks
					})
				)
			
			gl_entries.append(
				self.get_gl_dict({"account": self.expense_account,
					"credit": flt(self.net_amount),
					"credit_in_account_currency": flt(self.net_amount),
					"cost_center": self.cost_center,
					"party_check": 1,
					#  "party_type": party_type,
					#  "party": party,
					"reference_type": self.doctype,
					"reference_name": self.name,
					"business_activity": default_ba,
					"remarks": self.remarks
				})
			)
		# else:
		# 	if self.receivable_amount:
		# 		gl_entries.append(
		# 			self.get_gl_dict({"account": self.income_account,
		# 					"debit": flt(self.net_amount),
		# 					"debit_in_account_currency": flt(self.net_amount),
		# 					"cost_center": self.cost_center,
		# 					"party_check": 1,
		# 					"reference_type": self.doctype,
		# 					"reference_name": self.name,
		# 					"business_activity": default_ba,
		# 					"remarks": self.remarks
		# 				})
		# 		)

		# 		if self.tds_amount:
		# 			gl_entries.append(
		# 				self.get_gl_dict({"account": self.tds_account,
		# 					"debit": flt(self.tds_amount),
		# 					"debit_in_account_currency": flt(self.tds_amount),
		# 					"cost_center": self.cost_center,
		# 					"party_check": 1,
		# 					"reference_type": self.doctype,
		# 					"reference_name": self.name,
		# 					"business_activity": default_ba,
		# 					"remarks": self.remarks
		# 				})
		# 			)
				
		# 		gl_entries.append(
		# 			self.get_gl_dict({"account": receivable_account,
		# 				"credit": flt(self.receivable_amount),
		# 				"credit_in_account_currency": flt(self.net_amount),
		# 				"cost_center": self.cost_center,
		# 				"party_check": 1,
		# 				"party_type": "Customer",
		# 				"party": self.customer,
		# 				"reference_type": self.doctype,
		# 				"reference_name": self.name,
		# 				"business_activity": default_ba,
		# 				"remarks": self.remarks
		# 			})
		# 		)
		# 	else:
		# 		gl_entries.append(
		# 			self.get_gl_dict({"account": creditor_account,
		# 				"debit": flt(self.payable_amount),
		# 				"debit_in_account_currency": flt(self.payable_amount),
		# 				"cost_center": self.cost_center,
		# 				"reference_type": self.doctype,
		# 				"party_type": "Supplier",
		# 				"party": self.supplier,
		# 				"reference_name": self.name,
		# 				"business_activity": default_ba,
		# 				"remarks": self.remarks
		# 			})
		# 		)
		# 		if self.tds_amount:
		# 			gl_entries.append(
		# 				self.get_gl_dict({"account": self.tds_account,
		# 					"credit": flt(self.tds_amount),
		# 					"credit_in_account_currency": flt(self.tds_amount),
		# 					"cost_center": self.cost_center,
		# 					"reference_type": self.doctype,
		# 					"reference_name": self.name,
		# 					"business_activity": default_ba,
		# 					"remarks": self.remarks
		# 				})
		# 			)
		# 		gl_entries.append(
		# 			self.get_gl_dict({"account": self.outgoing_account,
		# 				"credit": flt(self.net_amount),
		# 				"credit_in_account_currency": flt(self.net_amount),
		# 				"cost_center": self.cost_center,
		# 				"reference_type": self.doctype,
		# 				"reference_name": self.name,
		# 				"business_activity": default_ba,
		# 				"remarks": self.remarks
		# 			})
		# 		)

		make_gl_entries(gl_entries, cancel=(self.docstatus == 2),update_outstanding="No", merge_entries=False)

	def update_ref_doc(self, cancel=None):
		if self.payment_for == "Maintenance Payment":
			for a in self.maintenance_payment_item:
				doc= frappe.get_doc("Technical Sanction Bill", a.technical_sanction)
			if cancel:
				doc.db_set("maintenance_payment","")
			else:
				doc.db_set("maintenance_payment", self.name)

	def consume_budget(self):
		if self.payment_for == "Transporter Payment":
			bud_obj = frappe.get_doc({
				"doctype": "Committed Budget",
				"account": self.transportation_account,
				"cost_center": self.cost_center,
				"po_no": self.name,
				"po_date": self.posting_date,
				"amount": self.net_amount,
				"poi_name": self.name,
				"date": frappe.utils.nowdate()
			})
			bud_obj.flags.ignore_permissions = 1
			bud_obj.submit()

			consume = frappe.get_doc({
				"doctype": "Consumed Budget",
				"account": self.transportation_account,
				"cost_center": self.cost_center,
				"po_no": self.name,
				"po_date": self.posting_date,
				"amount": self.net_amount,
				"pii_name": self.name,
				"com_ref": bud_obj.name,
				"date": frappe.utils.nowdate()
			})
			consume.flags.ignore_permissions=1
			consume.submit()

	def cancel_budget_entry(self):
		frappe.db.sql("delete from `tabCommitted Budget` where po_no = %s", self.name)
		frappe.db.sql("delete from `tabConsumed Budget` where po_no = %s", self.name)

	@frappe.whitelist()
	def get_tds_details(self, tax_withholding_category):
		# frappe.throw(tax_withholding_category)
		tds_account  = get_tds_account(tax_withholding_category)
		return tds_account
