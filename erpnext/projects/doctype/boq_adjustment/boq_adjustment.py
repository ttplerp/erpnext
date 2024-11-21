# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cstr, flt, getdate, today

class BOQAdjustment(Document):
	def validate(self):
		self.validate_boq_and_items()

	def on_submit(self):
		self.update_adjustment_history()
		self.update_boq_and_project()
		
	def on_cancel(self):
		self.update_adjustment_history(cancel=True)
		self.update_boq_and_project(cancel=True)

	def validate_boq_and_items(self):
		if self.adjustment_date < self.boq_date:
			frappe.throw(_("Adjustment Date cannot be earlier to BOQ Date"),title="Invalid Data")
		elif self.adjustment_date > today():
			frappe.throw(_("Adjustment Date cannot be a future date"),title="Invalid Data")

		# do not allow adjustment if there is any adjustment already done on later date
		for t in frappe.get_all("BOQ Adjustment", ["name","adjustment_date"], {"boq": self.boq, "name": ("!=",self.name), "adjustment_date": (">",self.adjustment_date), "docstatus":("<",2)}):
			msg = '<b>Reference# : <a href="#Form/BOQ Adjustment/{0}">{0}</a>, Dated: {1}</b>'.format(t.name,t.adjustment_date)
			frappe.throw(_("Backdating not permitted as there is an adjustment already exists <br>{0}").format(msg),title="Not permitted")

		for i in self.boq_item:
			# create new items if any under BOQ
			if not i.bsr_code:
				frappe.throw(_("Row#{0} : Adding new items not permitted.").format(i.idx), title="Not permitted")

			i.unclaimed_quantity, i.unclaimed_amount = frappe.db.get_value("BOQ Item", {"bsr_code": i.bsr_code}, ["unclaimed_quantity", "unclaimed_amount"])

			if (flt(i.unclaimed_amount)+flt(i.adjustment_amount)) < 0:
				msg = '<b>Reference# : <a href="#Form/BOQ/{0}">{0}</a></b>'.format(self.boq)
				frappe.throw(_("Row#{0} : Adjustment beyond available balance is not allowed.<br>{1}").format(i.idx,msg), title="Insufficient Balance")
	
	def update_adjustment_history(self, cancel=False):
		if cancel:
			frappe.db.sql("delete from `tabBOQ History Item` where parent='{boq}' and reference_name = '{reference_name}'".format(boq=self.boq, reference_name=self.name))

		else:
			total_amt = frappe.db.get_value("BOQ", self.boq, "total_amount")
			doc = frappe.get_doc("BOQ", self.boq)
			row = doc.append("boq_history_item", {})
			row.reference_type          = self.doctype
			row.reference_name          = self.name
			row.adjustment_date         = self.adjustment_date
			row.initial_amount          = flt(total_amt)
			row.adjustment_quantity     = flt(self.total_amount)
			row.adjustment_amount      	= flt(self.total_amount)
			row.final_amount 			= flt(self.total_amount)+flt(total_amt)
			row.remarks    				= self.remarks
			row.save(ignore_permissions=True)

	def update_boq_and_project(self, cancel=False):
		total_amount = 0.0
		for i in self.boq_item:
			adjustment_quantity = -1 * flt(i.adjustment_quantity) if cancel else flt(i.adjustment_quantity)
			adjustment_amount   = -1 * flt(i.adjustment_amount) if cancel else flt(i.adjustment_amount)

			# adjustment_rate     = flt(adjustment_amount)
			total_amount       += flt(adjustment_amount) 

			adjustment_quantity = 0.0 if self.boq_type == "Milestone Based" else flt(adjustment_quantity)
			# adjustment_rate     = flt(adjustment_amount) if self.boq_type == "Milestone Based" else 0.0

			i.unclaimed_quantity, i.unclaimed_amount = frappe.db.get_value("BOQ Item", {"bsr_code": i.bsr_code}, ["unclaimed_quantity", "unclaimed_amount"])

			if (flt(i.unclaimed_amount) + flt(i.adjustment_amount)) < 0:
				msg = '<b>Reference# : <a href="#Form/BOQ/{0}">{0}</a></b>'.format(self.boq)
				frappe.throw(_("Row#{0} : Adjustment beyond available balance is not allowed.<br>{1}").format(i.idx,msg), title="Insufficient Balance")

			# Update BOQ Item
			bi_doc                  	= frappe.get_doc("BOQ Item", {"bsr_code": i.bsr_code})
			# rate                    	= flt(bi_doc.rate) + flt(adjustment_rate)
			bi_doc.adjustment_quantity  += flt(adjustment_quantity)
			bi_doc.adjustment_amount    += flt(adjustment_amount)
			bi_doc.quantity           	= flt(bi_doc.quantity) + flt(adjustment_quantity)
			bi_doc.amount           	= flt(bi_doc.amount) + flt(adjustment_amount)
			bi_doc.unclaimed_quantity 	= flt(bi_doc.unclaimed_quantity) + flt(adjustment_quantity)
			bi_doc.unclaimed_amount   	= flt(bi_doc.unclaimed_amount) + flt(adjustment_amount)

			bi_doc.quantity_before_subcontract += flt(adjustment_quantity)
			bi_doc.quantity_after_subcontract += flt(adjustment_quantity)
			bi_doc.save(ignore_permissions = True)

		if total_amount:
			# Update BOQ
			boq_doc = frappe.get_doc("BOQ", self.boq)
			boq_doc.total_amount   = flt(boq_doc.total_amount) + flt(total_amount)
			boq_doc.total_unclaimed_amount = flt(boq_doc.total_unclaimed_amount) + flt(total_amount)
			boq_doc.save(ignore_permissions = True)

			# Update Project
			pro_doc = frappe.get_doc("Project", self.project)
			pro_doc.flags.dont_sync_tasks = True
			pro_doc.boq_value = flt(pro_doc.boq_value) + flt(total_amount)
			pro_doc.save(ignore_permissions = True)
