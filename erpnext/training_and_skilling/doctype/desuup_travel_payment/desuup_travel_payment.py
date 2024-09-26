# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, cint
from frappe.model.document import Document

class DesuupTravelPayment(Document):
	def validate(self):
		self.calculate_total_amount()

	def on_submit(self):
		self.post_journal_entry()
		self.update_payment_status()

	def before_cancel(self):
		if self.journal_entry:
			je_status = frappe.get_value("Journal Entry", {"name": self.journal_entry}, "docstatus")
			if cint(je_status) == 1:
				frappe.throw("Journal Entry {} for this transaction needs to be cancelled first".format(frappe.get_desk_link("Journal Entry", self.journal_entry)))
			else:
				frappe.db.sql("delete from `tabJournal Entry` where name = '{}'".format(self.journal_entry))
				self.db_set("journal_entry", None)

	def on_cancel(self):
		pass

	def update_payment_status(self):
		self.payment_status = "Unpaid"

	def post_journal_entry(self):
		payable_account = frappe.db.get_single_value("Desuup Settings", "arrear_account")
		bank_account = frappe.db.get_value("Company", self.company, "default_bank_account")
		if not bank_account:
			frappe.throw("Set default bank account in company {}".format(frappe.bold(self.company)))
		accounts = []
		for d in self.get('items'):
			accounts.append({
				'account': payable_account,
				'debit': flt(d.total_amount, 2),
				'debit_in_account_currency': flt(d.total_amount, 2),
				'cost_center': self.cost_center,
				'party_type': 'Desuup',
				'party': d.desuup,
				"reference_type": self.doctype,
				"reference_name": self.name,
			})
		

		accounts.append({
			'account': bank_account,
			'credit': flt(self.total_amount, 2),
			'credit_in_account_currency': flt(self.total_amount, 2),
			'cost_center': self.cost_center
		})

		je = frappe.new_doc("Journal Entry")
		je.flags.ignore_permission = 1
		je.update({
			"doctype": "Journal Entry",
			"branch": self.branch,
			"posting_date": self.posting_date,
			"voucher_type": "Bank Entry",
			"naming_series": "Bank Payment Voucher",
			"company": self.company,
			"reference_doctype": self.doctype,
			"reference_name": self.name,
			"accounts": accounts
		})
		je.insert()
		self.db_set('journal_entry', je.name)
		frappe.msgprint(_('Journal Entry {0} posted to accounts').format(frappe.get_desk_link("Journal Entry", je.name)))

	def calculate_total_amount(self):
		total_amt = 0
		for d in self.get("items"):
			total_amt += d.total_amount
		self.total_amount = total_amt

	def get_desuup_list(self):
		base_query = """
				SELECT 
					t1.name AS reference_name, 
					'Training Management' AS reference_doctype,  
					t1.branch, 
					t1.course_cost_center AS cost_center, 
					t2.desuup_id AS desuup, 
					t2.desuup_name
				FROM 
					`tabTraining Management` t1
				INNER JOIN 
					`tabTrainee Details` t2 ON t1.name = t2.parent
				WHERE 
					t1.status = 'On Going'
					AND t2.reporting_date IS NOT NULL
					AND t1.name = %(training_management)s
				"""
		params = {}
		if self.training_management:
			params['training_management'] = self.training_management
		desuup_list = frappe.db.sql(base_query, params, as_dict=True)

		if self.travel_route:
			travel_route_data = frappe.get_doc("Travel Route", self.travel_route)
			if travel_route_data:
				for desuup in desuup_list:
					desuup['bus_fare'] = travel_route_data.bus_fare
					desuup['taxi_fare'] = travel_route_data.taxi_fare
					desuup['da'] = travel_route_data.da
					desuup['total_amount'] = flt(travel_route_data.da) + flt(travel_route_data.taxi_fare) + flt(travel_route_data.bus_fare)

		return desuup_list

	@frappe.whitelist()
	def get_desuup_details(self):
		self.set('items', [])
		desuups = self.get_desuup_list()
		if not desuups:
			frappe.throw(_("No desuups for the mentioned criteria"))

		for d in desuups:
			self.append('items', d)