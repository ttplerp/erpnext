# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import (
	flt,
	money_in_words,
)
from erpnext.custom_workflow import validate_workflow_states, notify_workflow_states


class TransportationandHireChargeEntry(Document):
	def validate(self):
		self.calculate_tds()
		validate_workflow_states(self)

	def calculate_tds(self):
		for a in self.items:
			a.tds_amount = flt(a.tds_percent)/100 * a.amount

	def on_submit(self):
		# self.submit_hire_charge_invoice()
		if not self.settle_imprest_advance_account:
			self.create_transportation_hire_charge_invoice()
		else:
			self.post_to_account()

	def submit_transportation_hire_charge_invoice(self):
		if self.hire_charge_invoice_created == 0:
			frappe.throw("Please create Transportation and Hire Charge Invoice.")

		successful = failed = 0
		for invoice in self.items:
			error = None
			try:
				hire_charge_invocie = frappe.get_doc(
					"Transportation and Hire Charge Invoice",
					{
						"branch": invoice.branch,
						"party_type": invoice.party_type,
						"party": invoice.party,
						"docstatus": 0,
						"transportation_and_hire_charge_entry": self.name,
					},
				)
				hire_charge_invocie.submit()
				successful += 1
			except Exception as e:
				error = e
				failed += 1
				
		if successful > failed:
			self.db_set("hire_charge_invoice_submitted", 1)
		
	@frappe.whitelist()
	def create_transportation_hire_charge_invoice(self):
		self.check_permission("write")

		args = frappe._dict({
			'posting_date': self.posting_date,
		})

		failed = successful = 0
		for a in self.items:
			args.update({
				"doctype": "Transportation and Hire Charge Invoice",
				"transportation_and_hire_charge_entry": self.name,
				"invoice_type": "Transportation Charge Invoice" if self.entry_type == "Transportation Charge" else "Hire Charge Invoice",
				'branch': self.branch,
				'cost_center': self.cost_center,
				'party_type': a.party_type,
				'party': a.party,
				'tds_percent': a.tds_percent,
				'tds_amount': a.tds_amount,
				'tds_account': a.tds_account,
				'grand_total': a.amount,
				'equipment_type': a.equipment_type,
				'equipment_no': a.equipment_no,

			})

			error = None
			try:
				transportation_hire_charge_invoice = frappe.get_doc(args)
				transportation_hire_charge_invoice.set("deduct_items", [])

				for d in self.deductions:
					if d.party_type == a.party_type and d.party == a.party:
						transportation_hire_charge_invoice.append(
							'deduct_items',
							{
								"account": d.account,
								"amount": d.amount,
							},
						)
				transportation_hire_charge_invoice.submit()
				successful += 1

			except Exception as e:
				error = e
				failed += 1
		if failed != 1:
			self.hire_charge_invoice_created = 1
			self.hire_charge_invoice_submitted = 1
		self.save()
		self.reload()
	
	@frappe.whitelist()
	def get_tds_account(self, args):
		account = frappe.db.sql("select account from `tabTDS Account Item` where tds_percent='{}'".format(args.tds_percent))[0][0]
		return account

	@frappe.whitelist()
	def post_to_account(self):
		total_payable_amount = 0
		total_tds_amount = 0
		accounts = []
		if self.settle_imprest_advance_account == 1:
			bank_account = frappe.db.get_value("Company", self.company, "imprest_advance_account")
		else:
			bank_account = frappe.db.get_value("Company", self.company, "default_bank_account")
		hire_charge_payable_acc = frappe.db.get_single_value("Maintenance Settings", "hire_charge_payable_account")

		if not bank_account:
			frappe.throw('Set default bank account in company {}'.format(self.company))

		query = frappe.db.sql("""
						select name from `tabTransportation and Hire Charge Invoice`
						where docstatus = 1
						and transportation_and_hire_charge_entry = '{}'
						and outstanding_amount > 0	
					""".format(self.name, self.branch), as_dict=True)
		if self.settle_imprest_advance_account == 1:
			for a in self.items:
				total_payable_amount += flt(a.amount)
				total_tds_amount += flt(a.tds_amount)
				if self.entry_type == "Hire Charge":
					expense_account = frappe.db.get_single_value("Maintenance Settings", "vehicle_expense_account" if a.equipment_type=="Vehicle" else "machine_expense_account")
				else:
					expense_account = frappe.db.get_single_value("Maintenance Settings", "transportation_expense_account")
				accounts.append({
					"account": expense_account,
					"debit_in_account_currency": flt(a.amount),
					"cost_center": self.cost_center,
					"party_check": 1,
					"party_type": a.party_type,
					"party": a.party,
					"reference_type": self.doctype,
					"reference_name": self.name,
				})

				if a.tds_percent:
					accounts.append({
						"account": a.tds_account,
						"credit_in_account_currency": flt(a.tds_amount),
						"cost_center": self.cost_center,
						"party_check": 1,
						"party_type": a.party_type,
						"party": a.party,
						"reference_type": self.doctype,
						"reference_name": self.name,
					})
		else:
			for a in query:
				transportation_hire_charge_invoice = frappe.get_doc("Transportation and Hire Charge Invoice", a.name)
				total_payable_amount += flt(transportation_hire_charge_invoice.payable_amount, 2)
				accounts.append({
					"account": hire_charge_payable_acc,
					"debit_in_account_currency": flt(transportation_hire_charge_invoice.payable_amount,2),
					"cost_center": transportation_hire_charge_invoice.cost_center,
					"party_check": 1,
					"party_type": transportation_hire_charge_invoice.party_type,
					"party": transportation_hire_charge_invoice.party,
					"reference_type": transportation_hire_charge_invoice.doctype,
					"reference_name": transportation_hire_charge_invoice.name,
				})
		
		if self.settle_imprest_advance_account == 1:
			accounts.append({
				"account": bank_account,
				"credit_in_account_currency": flt(flt(total_payable_amount)-flt(total_tds_amount) ,2),
				"cost_center": self.cost_center,
				"party_type": "Employee",
				"party": self.imprest_party,
			})
		else:
			accounts.append({
				"account": bank_account,
				"credit_in_account_currency": flt(total_payable_amount, 2),
				"cost_center": self.cost_center,
			})
		je = frappe.new_doc("Journal Entry")
		je.flags.ignore_permission = 1
		je.update({
			"doctype": "Journal Entry",
			"voucher_type": "Journal Entry" if self.settle_imprest_advance_account == 1 else "Bank Entry",
			"naming_series": "Journal Voucher" if self.settle_imprest_advance_account == 1 else "Bank Payment Voucher",
			"title": "Hire Charge",
			"user_remark": "Note: Transportation and Hire Charge Invoice Payment",
			"posting_date": self.posting_date,
			"company": self.company,
			"total_amount_in_words": money_in_words(total_payable_amount),
			"branch": self.branch,
			"reference_type":self.doctype,
			"reference_doctype":self.name,
			"accounts":accounts
		})
		je.insert()
		frappe.msgprint(_('Journal Entry {0} posted to accounts').format(frappe.get_desk_link("Journal Entry", je.name)))