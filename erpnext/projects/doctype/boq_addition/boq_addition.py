# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

# import frappe
from __future__ import unicode_literals
from frappe.model.document import Document
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cstr, flt, getdate, today, now_datetime

class BOQAddition(Document):
	def validate(self):
		self.set_defaults()
		self.validate_boq_and_items()

	def on_submit(self):
		self.set_defaults()
		self.validate_boq_and_items()
		self.update_boq_item()
		self.update_additional_history()
		self.update_boq_and_project()

	def on_cancel(self):
		self.update_boq_item(cancel=False)
		self.update_additional_history(cancel=True)
		self.update_boq_and_project()

	def set_defaults(self):
		total_amount = 0.0
		for item in self.boq_item:
			item.amount = flt(item.quantity) * flt(item.rate)
			if item.amount <= 0:
				frappe.throw("Amount Should be Greater Than Zero at Index '{0}'".format(item.idx))
			total_amount  += flt(item.amount)

		self.total_amount = flt(total_amount)
		if flt(self.total_amount) <= 0:
			frappe.throw("Total Amount Should be Greater Than Zero")

	def validate_boq_and_items(self):
		if self.addition_date  < self.boq_date:
			frappe.throw(_("Addition Date cannot be earlier to BOQ Date"),title="Invalid Data")
		elif self.addition_date > today():
			frappe.throw(_("Addition Date cannot be a future date"),title="Invalid Data")

	def update_boq_item(self, cancel=False):
		boq = frappe.get_doc("BOQ", self.boq)	
		for d in self.boq_item:
			if cancel:
				frappe.db.sql(""" delete from `tabBOQ Item` where ref_name = '{0}'""".format(d.name))
			else:
				boq.flags.ignore_permissions = 1
				boq.append('boq_item', {
						"bsr_code": d.bsr_code,
						"description": d.description,
						"uom": d.uom,
						"no": d.no,
						"length": d.length,
						"height": d.height, 
						"breath": d.breath,
						"coefficient": d.coefficient,
						"quantity": d.quantity,
						"rate": d.rate,
						"amount": d.amount,
						"claimed_quantity": 0.0,
						"adjustment_amount": 0.0,
						"claimed_amount": 0.0,
						"booked_amount": 0.0,
						"unclaimed_quantity": flt(d.quantity),
						"unclaimed_amount":  flt(d.amount),
						"quantity_before_subcontract": flt(d.quantity),
						"quantity_after_subcontract": flt(d.quantity),
						"remarks": d.remarks,
					})
				boq.save(ignore_permissions=True)
				boq.submit()
				

	def update_additional_history(self, cancel=False):
		if cancel:
			frappe.db.sql(""" 
				delete from `tabBOQ Addition History` where parent='{boq}' and  transaction_name = '{reference_name}'
			""".format(boq = self.boq, reference_name=self.name))
		else:
			doc = frappe.get_doc("BOQ", self.boq)
			row = doc.append("boq_addition_item", {})
			row.reference_name          = self.name
			row.reference_date          = self.addition_date
			row.initial_amount          = flt(doc.total_amount)
			row.additional_amount      	= flt(self.total_amount)
			row.final_amount 			= flt(self.total_amount)+flt(doc.total_amount)
			row.remarks    				= self.remarks
			row.save(ignore_permissions=True)

	def update_boq_and_project(self):
		#update Total Amount for BOQ and Project 
		if self.total_amount:
			mul_factor = -1 if self.docstatus == 2 else 1
			# Update BOQ
			boq_doc = frappe.get_doc("BOQ", self.boq)
			boq_doc.total_amount   = flt(boq_doc.total_amount) + flt(self.total_amount) * flt(mul_factor)
			boq_doc.total_unclaimed_amount = flt(boq_doc.total_unclaimed_amount) + flt(self.total_amount) * flt(mul_factor)
			boq_doc.addition_amount = flt(boq_doc.addition_amount) + flt(self.total_amount) * flt(mul_factor)
			boq_doc.save(ignore_permissions = True)

			# Update Project
			pro_doc = frappe.get_doc("Project", self.project)
			pro_doc.flags.dont_sync_tasks = True
			pro_doc.project_value = flt(pro_doc.project_value) + flt(self.total_amount) * flt(mul_factor)
			pro_doc.save(ignore_permissions = True)
