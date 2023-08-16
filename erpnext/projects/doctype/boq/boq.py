# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt
from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from frappe.model.naming import make_autoname
from frappe.utils import cstr, flt, getdate, today, nowdate, now_datetime
from datetime import date
from erpnext.accounts.party import get_party_account

class BOQ(Document):	
	def validate(self):
		self.update_defaults()
		self.validate_defaults()
		self.update_boq_history()
	
	def on_submit(self):
		self.update_project_value()
		self.project_boq_item_entry()

	def on_cancel(self):
		self.update_project_value()
		self.project_boq_item_entry()

	def on_update_after_submit(self):
		self.project_boq_item_entry()

	def calculate_quantity(self): 
		for d in self.boq_item:
			d.quantity = d.no * d.coefficient * d.breath * d.height * d.length

	def project_boq_item_entry(self):
		if self.docstatus == 2:
			frappe.db.sql("delete from `tabProject BOQ Item` where parent='{project}' and boq_name = '{boq_name}'".format(project=self.project, boq_name=self.name))
		else:
			if not frappe.db.exists("Project BOQ Item", {"parent": self.project, "boq_name": self.name}):
				doc = frappe.get_doc("Project", self.project)
				row = doc.append("project_boq_item", {})
				row.boq_name            = self.name
				row.boq_date            = self.boq_date
				row.amount              = flt(self.total_amount)
				row.price_adjustment    = flt(self.price_adjustment)
				row.total_amount        = flt(self.total_amount)+flt(self.price_adjustment)
				row.received_amount     = flt(self.received_amount)
				row.paid_amount         = flt(self.paid_amount)
				row.balance_amount      = flt(self.balance_amount)
				row.save(ignore_permissions=True)
			else:
				row = frappe.get_doc("Project BOQ Item", {"parent": self.project, "boq_name": self.name})
				row.boq_date            = self.boq_date
				row.amount              = flt(self.total_amount)
				row.price_adjustment    = flt(self.price_adjustment)
				row.total_amount        = flt(self.total_amount)+flt(self.price_adjustment)
				row.received_amount     = flt(self.received_amount)
				row.paid_amount         = flt(self.paid_amount)
				row.balance_amount      = flt(self.balance_amount)
				row.save(ignore_permissions=True)
							
	def update_boq_history(self):
		for i in self.boq_history_item:
			if i.transaction_type != self.doctype or (i.transaction_name and i.transaction_name != self.name):
				self.remove(i)

		# make entry in history for the current BOQ if it doesn't already exist, else update the details
		if not self.boq_history_item:
			self.append("boq_history_item",{
						"transaction_type": self.doctype,
						"transaction_date": self.boq_date,
						"initial_amount": flt(self.total_amount),
						"adjustment_amount": 0,
						"final_amount": flt(self.total_amount),
						"owner": frappe.session.user,
						"creation": now_datetime(),
						"modified_by": frappe.session.user,
						"modified": now_datetime()
			})
		else:
			for i in self.boq_history_item:
				if i.transaction_type == self.doctype:
					i.transaction_name  = self.name
					i.transaction_date  = self.boq_date
					i.initial_amount    = flt(self.total_amount)
					i.adjustment_amount = 0
					i.final_amount      = flt(self.total_amount)

	def validate_defaults(self):
		if not all((self.project, self.branch, self.cost_center)):
			frappe.throw("Either one of them is not set <b>Project, Branch or Cost Center</b> cannot be null.")

		if flt(self.total_amount,0) <= 0:
			frappe.throw(_("Invalid total amount."), title="Invalid Data")

	def update_defaults(self):
		item_group = ""
		self.total_amount = self.price_adjustment = self.claimed_amount = self.received_amount = self.balance_amount = 0.0
		
		non_group_items = [item for item in self.boq_item]
		for item in non_group_items:
			item.amount = flt(item.quantity) * flt(item.rate)
			item.claimed_quantity = item.claimed_amount = item.booked_quantity = item.booked_amount = 0.0
			item.balance_quantity = flt(item.quantity)
			item.balance_rate = flt(item.rate)
			item.balance_amount = flt(item.amount)
			
			self.total_amount += flt(item.amount)
			self.balance_amount += flt(item.amount)
			
			if flt(item.amount) < 0:
				frappe.throw(_("Row#{0} : Invalid amount."), title="Invalid Data")
			
			item.parent_item = item_group
		
		# Defaults
		base_project = frappe.get_doc("Project", self.project)
		self.party_type = base_project.party_type
		self.party = base_project.party
		
		if base_project.status in ('Completed', 'Cancelled'):
			frappe.throw(_("Operation not permitted on already {0} Project.").format(base_project.status), title="BOQ: Invalid Operation")
		
		if not self.branch:
			self.branch = base_project.branch
		
		if not self.cost_center:
			self.cost_center = base_project.cost_center
		
		if not self.boq_date:
			self.boq_date = date.today()

	def update_project_value(self):
		if self.total_amount:
			pro_doc = frappe.get_doc("Project", self.project)
			pro_doc.flags.dont_sync_tasks = True
			pro_doc.boq_value = flt(pro_doc.boq_value)+(-1*(self.total_amount) if self.docstatus==2 else flt(self.total_amount))
			pro_doc.save(ignore_permissions = True)

@frappe.whitelist()
def make_boq_adjustment(source_name, target_doc=None):
	def update_master(source_doc, target_doc, source_parent):
		target_doc.total_amount = 0.0
			
	def update_item(source_doc, target_doc, source_parent):
		target_doc.balance_rate         = flt(source_doc.balance_rate) if flt(source_doc.balance_rate) else flt(source_doc.rate)
		target_doc.balance_quantity_adj = flt(target_doc.balance_quantity)
		target_doc.balance_rate_adj     = flt(target_doc.balance_rate)
		target_doc.balance_amount_adj   = flt(target_doc.balance_amount)
		target_doc.adjustment_quantity  = 0
		target_doc.adjustment_rate      = 0
		target_doc.adjustment_amount    = 0
			
	doclist = get_mapped_doc("BOQ", source_name, {
		"BOQ": {
			"doctype": "BOQ Adjustment",
			"field_map": {
					"name": "boq"
			},
			"postprocess": update_master
		},

		"BOQ Item": {
			"doctype": "BOQ Adjustment Item",
			"field_map": {
					"name": "boq_item_name",
					"balance_rate": "balance_rate",
			},
			"postprocess": update_item
		}
	}, target_doc)

	return doclist
	
@frappe.whitelist()
def make_boq_substitution(source_name, target_doc=None):
	def update_master(source_doc, target_doc, source_parent):
		target_doc.total_amount = 0.0

	doclist = get_mapped_doc("BOQ", source_name, {
		"BOQ": {
			"doctype": "BOQ Substitution",
			"field_map": {
					"name": "boq"
			},
			"postprocess": update_master
		}

	}, target_doc, ignore_child_tables=True)

	return doclist

@frappe.whitelist()
def make_additional_boq(source_name, target_doc=None):
	def update_master(source_doc, target_doc, source_parent):
		target_doc.total_amount = 0.0
	doclist = get_mapped_doc("BOQ", source_name, {
		"BOQ": {
			"doctype": "BOQ Addition",
			"field_map": {
					"name": "boq"
			},
			"postprocess": update_master
		}
	}, target_doc, ignore_child_tables=True)
	return doclist


@frappe.whitelist()
def make_direct_invoice(source_name, target_doc=None):
	def update_master(source_doc, target_doc, source_parent):
		target_doc.invoice_title = str(target_doc.project) + "(Project Invoice)"
		target_doc.invoice_type = "Direct Invoice"
		target_doc.check_all = 1
			
	def update_item(source_doc, target_doc, source_parent):
		target_doc.invoice_rate = flt(source_doc.balance_rate) if flt(source_doc.balance_rate) else flt(source_doc.rate)
		target_doc.act_quantity = flt(target_doc.invoice_quantity)
		target_doc.act_rate     = flt(target_doc.invoice_rate)
		target_doc.act_amount   = flt(target_doc.invoice_amount)
		target_doc.original_rate= flt(target_doc.invoice_rate)
			
	doclist = get_mapped_doc("BOQ", source_name, {
		"BOQ": {
			"doctype": "Project Invoice",
			"field_map": {
					"project": "project"
			},
			"postprocess": update_master
		},

		"BOQ Item": {
			"doctype": "Project Invoice BOQ",
			"field_map": {
					"name": "boq_item_name",
					"balance_quantity": "invoice_quantity",
					"balance_rate": "invoice_rate",
					"balance_amount": "invoice_amount",
					"quantity": "original_quantity",
					"amount": "original_amount"
			},
			"postprocess": update_item
		}
	}, target_doc)

	return doclist

@frappe.whitelist()
def make_boq_subcontract(source_name, target_doc=None):
	def update_master(source_doc, target_doc, source_parent):
		target_doc.boq          = source_doc.name
		target_doc.party_type   = "Supplier" if source_doc.party_type == "Customer" else None
		target_doc.party        = None
		target_doc.total_amount = 0
		target_doc.price_adjustment = 0
		target_doc.paid_amount = 0
		target_doc.received_amount = 0
		target_doc.claimed_amount = 0
		target_doc.balance_amount = 0
			
	def update_item(source_doc, target_doc, source_parent):
		target_doc.boq_quantity = target_doc.quantity = source_doc.balance_quantity
		target_doc.boq_rate     = target_doc.rate     = source_doc.balance_rate
		target_doc.boq_amount   = target_doc.amount   = source_doc.balance_amount
		
		target_doc.claimed_quantity    = target_doc.claimed_amount    = 0
		target_doc.booked_quantity     = target_doc.booked_amount     = 0
		target_doc.adjustment_quantity = target_doc.adjustment_amount = 0
			
	doclist = get_mapped_doc("BOQ", source_name, {
		"BOQ": {
			"doctype": "Subcontract",
			"field_map": {
					"project": "project"
			},
			"postprocess": update_master
		},
		"BOQ Item": {
			"doctype": "Subcontract Item",
			"field_map": {
					"name": "boq_item_name",
			},
			"postprocess": update_item
		},
	}, target_doc)

	return doclist

@frappe.whitelist()
def make_mb_invoice(source_name, target_doc=None):
	def update_master(source_doc, target_doc, source_parent):
		target_doc.invoice_title = str(target_doc.project) + "(Project Invoice)"
		target_doc.invoice_type = "MB Based Invoice"
		target_doc.check_all_mb = 1
		target_doc.debit_credit_account = get_party_account(source_doc.party_type, source_doc.party, source_doc.company)
			
	doclist = get_mapped_doc("BOQ", source_name, {
		"BOQ": {
			"doctype": "Project Invoice",
			"field_map": {
					"project": "project"
			},
			"postprocess": update_master
		}
	}, target_doc)

	return doclist


@frappe.whitelist()
def make_book_entry(source_name, target_doc=None):
	def update_master(source_doc, target_doc, source_parent):
		target_doc.check_all = 1
			
	def update_item(source_doc, target_doc, source_parent):
		target_doc.entry_rate   = flt(source_doc.balance_rate) if flt(source_doc.balance_rate) else flt(source_doc.rate)
		target_doc.act_quantity = flt(target_doc.entry_quantity)
		target_doc.act_rate     = flt(target_doc.entry_rate)
		target_doc.act_amount   = flt(target_doc.entry_amount)
		target_doc.original_rate= flt(target_doc.entry_rate)
			
	doclist = get_mapped_doc("BOQ", source_name, {
		"BOQ": {
			"doctype": "MB Entry",
			"field_map": {
					"project": "project"
			},
			"postprocess": update_master
		},

		"BOQ Item": {
			"doctype": "MB Entry BOQ",
			"field_map": {
					"name": "boq_item_name",
					"balance_quantity": "entry_quantity",
					"balance_rate": "entry_rate",
					"balance_amount": "entry_amount",
					"quantity": "original_quantity",
					"amount": "original_amount"
			},
			"postprocess": update_item
		}
	}, target_doc)

	return doclist

@frappe.whitelist()
def make_boq_advance(source_name, target_doc=None):
	doclist = get_mapped_doc("BOQ", source_name, {
		"BOQ": {
			"doctype": "Project Advance",
			"field_map":{
				"project": "project",
				"party_type": "party_type",
				"party": "party",
				"party_address": "party_address"
			},
		}
	}, target_doc)
	return doclist
