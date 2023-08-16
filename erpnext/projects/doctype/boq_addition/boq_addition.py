# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cstr, flt, getdate, today, now_datetime, cint

class BOQAddition(Document):
	def validate(self):
		self.update_defaults()
		self.validate_boq_and_items()

	def on_submit(self):
		self.update_defaults()
		self.validate_boq_and_items()
		self.update_boq_item(submit = True)
		self.update_history()
		self.update_boq_and_project()

	def on_cancel(self):
		self.update_boq_item(submit = False)
		self.update_history(cancel=1)
		self.update_boq_and_project()

	def update_defaults(self):
		item_group = ""
		total_amount = 0.0
		for item in self.boq_item:
			item.amount           = flt(item.quantity)*flt(item.rate)
			item.claimed_quantity = 0.0
			item.claimed_amount   = 0.0
			item.booked_quantity  = 0.0
			item.booked_amount    = 0.0
			item.balance_quantity = flt(item.quantity)
			item.balance_rate     = flt(item.rate)
			item.balance_amount   = flt(item.amount)
			if item.amount <= 0:
				frappe.throw("Amount Should be Greater Than Zero at Index '{0}'".format(item.idx))
			total_amount    += flt(item.amount)
			item.parent_item = item_group
		
		self.total_amount = flt(total_amount)
		if flt(self.total_amount) <= 0:
			frappe.throw("Total Amount Should be Greater Than Zero")

	def validate_boq_and_items(self):
		# validate adjustment date
		if self.addition_date  < self.boq_date:
			frappe.throw(_("Addition Date cannot be earlier to BOQ Date"),title="Invalid Data")
		elif self.addition_date > today():
			frappe.throw(_("Addition Date cannot be a future date"),title="Invalid Data")

	def update_boq_item(self, submit):
		boq = frappe.get_doc("BOQ", self.boq)	
		for d in self.boq_item:
			if submit:
				boq.flags.ignore_permissions = 1
				boq.append('boq_item', {
						"boq_code": d.boq_code,
						"item_name": d.item_name,
						"uom": d.uom,
						"no": d.no,
						"length": d.length,
						"height": d.height, 
						"breath": d.breath,
						"coefficient": d.coefficient,
						"quantity": d.quantity,
						"rate": d.rate,
						"rate_analysis": d.rate_analysis,
						"amount": d.amount,
						"claimed_quantity": 0.0,
						"adjustment_amount": 0.0,
						"claimed_amount": 0.0,
						"booked_quantity": 0.0,
						"booked_amount": 0.0,
						"balance_quantity": flt(d.quantity),
						"balance_rate":  flt(d.rate),
						"balance_amount":  flt(d.amount),
						"remarks": d.remarks,
						"ref_type": d.parenttype,
						"ref_name": d.name
					})
				boq.save(ignore_permissions=True)
			else:
				frappe.db.sql(""" delete from `tabBOQ Item` where ref_name = '{0}'""".format(d.name))
		
	def update_history(self, cancel=0):
		boq = frappe.get_doc("BOQ", self.boq)
		if cint(cancel) == 1:
			frappe.db.sql(""" 
					delete from `tabBOQ Addition History` where parent='{boq}' and transaction_name = '{transaction_name}'
				""".format(boq = self.boq, transaction_name=self.name))
		else:
			boq.append("boq_addition_item",{
				"transaction_type": self.doctype,
				"transaction_date": self.addition_date,
				"transaction_name": self.name,
				"initial_amount":  flt(boq.total_amount),
				"additional_amount": flt(self.total_amount),
				"final_amount": flt(self.total_amount) + flt(boq.total_amount),
				"owner": frappe.session.user,
				"creation": now_datetime(),
				"modified_by": frappe.session.user,
				"modified": now_datetime()
			})

			boq.save(ignore_permissions=True)

	def update_boq_and_project(self):
		#update Total Amount for BOQ and Project 
		if self.total_amount:
			mul_factor = -1 if self.docstatus == 2 else 1
			# Update BOQ
			boq_doc = frappe.get_doc("BOQ", self.boq)
			boq_doc.total_amount   = flt(boq_doc.total_amount) + flt(self.total_amount) * flt(mul_factor)
			boq_doc.balance_amount = flt(boq_doc.balance_amount) + flt(self.total_amount) * flt(mul_factor)
			boq_doc.addition_amount = flt(boq_doc.addition_amount) + flt(self.total_amount) * flt(mul_factor)
			boq_doc.save(ignore_permissions = True)

			# Update Project
			pro_doc = frappe.get_doc("Project", self.project)
			pro_doc.flags.dont_sync_tasks = True
			pro_doc.boq_value = flt(pro_doc.boq_value) + flt(self.total_amount) * flt(mul_factor)
			pro_doc.save(ignore_permissions = True)
