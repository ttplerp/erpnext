from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cstr, flt, getdate, today

class SubcontractAdjustment(Document):
	def validate(self):
		self.validate_boq_and_items()
		self.remove_not_selected_bsr()

	def on_submit(self):
		self.update_adjustment_history()
		self.update_boq_and_project()
		self.update_boq_item_in_boq()

	def on_cancel(self):
		self.update_adjustment_history(cancel=True)
		self.update_boq_and_project(cancel=True)
		self.update_boq_item_in_boq(cancel=True)
		   
	def remove_not_selected_bsr(self):
		to_remove = []
		for d in self.get("boq_item"):
			if not d.is_selected:
				to_remove.append(d)
		[self.remove(d) for d in to_remove]

	def validate_boq_and_items(self):
		if self.adjustment_date > today():
			frappe.throw(_("Adjustment Date cannot be a future date"), title="Invalid Data")

		# do not allow adjustment if there is any adjustment already done on later date
		for t in frappe.get_all("Subcontract Adjustment", ["name","adjustment_date"], {"subcontract": self.subcontract, "name": ("!=",self.name), "adjustment_date": (">",self.adjustment_date), "docstatus":("<",2)}):
			msg = '<b>Reference# : <a href="#Form/Subcontract Adjustment/{0}">{0}</a>, Dated: {1}</b>'.format(t.name,t.adjustment_date)
			frappe.throw(_("Adjustment not permitted as an entry already exists at a later date<br>{0}").format(msg),title="Not permitted")

		# do not allow adjustment if there is any MB entry later on dates
		# validate items
		for i in self.boq_item:
			# create new items if any under BOQ
			if not i.bsr_code:
				frappe.throw(_("Row#{0} : Adding new items not permitted.").format(i.idx), title="Not permitted")

			i.unclaimed_quantity, i.unclaimed_amount = frappe.db.get_value("Subcontract Item", {"bsr_code": i.bsr_code}, ["unclaimed_quantity", "unclaimed_amount"])

			if (flt(i.unclaimed_amount)+flt(i.adjustment_amount)) < 0:
				msg = '<b>Reference# : <a href="#Form/Subcontract/{0}">{0}</a></b>'.format(self.subcontract)
				frappe.throw(_("Row#{0} : Adjustment beyond available balance is not allowed.<br>{1}").format(i.idx,msg), title="Insufficient Balance")

	def update_boq_and_project(self, cancel=False):
		total_amount = 0.0
		total_unclaimed_amount = 0.0
		
		for i in self.boq_item:
			adjustment_quantity = -1 * flt(i.adjustment_quantity) if self.docstatus == 2 else flt(i.adjustment_quantity)
			adjustment_amount   = -1 * flt(i.adjustment_amount) if self.docstatus == 2 else flt(i.adjustment_amount)
			# adjustment_rate     = flt(adjustment_amount)
			
			total_amount       += flt(adjustment_amount) 
			total_unclaimed_amount += flt(adjustment_amount)

			adjustment_quantity = 0.0 if self.boq_type == "Milestone Based" else flt(adjustment_quantity)
			# adjustment_rate     = flt(adjustment_amount) if self.boq_type == "Milestone Based" else 0.0
			
			i.unclaimed_quantity, i.unclaimed_amount = frappe.db.get_value("Subcontract Item", {"bsr_code": i.bsr_code}, ["unclaimed_quantity","unclaimed_amount"])

			if (flt(i.unclaimed_amount)+flt(adjustment_amount)) < 0:
					msg = '<b>Reference# : <a href="#Form/Subcontract/{0}">{0}</a></b>'.format(self.subcontract)
					frappe.throw(_("Row#{0} : Cannot cancel as the adjusted amount is already invoiced.<br>{1}").format(i.idx,msg), title="Not permitted")

			# Update Subcontract Item
			bi_doc                  	= frappe.get_doc("Subcontract Item", {"bsr_code": i.bsr_code, "parent": self.subcontract})
			# rate                    	= flt(bi_doc.rate) + flt(adjustment_rate)
			bi_doc.adjustment_quantity	= flt(adjustment_quantity)
			bi_doc.adjustment_amount 	= flt(adjustment_amount)
			bi_doc.amount           	= flt(bi_doc.amount) + flt(adjustment_amount)
			bi_doc.unclaimed_quantity 	= flt(bi_doc.unclaimed_quantity) + flt(adjustment_quantity)
			bi_doc.unclaimed_amount   	= flt(bi_doc.unclaimed_amount) + flt(adjustment_amount)
			bi_doc.save(ignore_permissions = True)

		if total_amount:
			# Update Subcontract
			boq_doc = frappe.get_doc("Subcontract", self.subcontract)
			boq_doc.total_amount   = flt(boq_doc.total_amount) + flt(total_amount)
			boq_doc.total_unclaimed_amount = flt(boq_doc.total_unclaimed_amount) + flt(total_unclaimed_amount)
			boq_doc.save(ignore_permissions = True)

	def update_boq_item_in_boq(self, cancel=False):
		for i in self.boq_item:
			adjustment_quantity = -1 * flt(i.adjustment_quantity) if cancel else flt(i.adjustment_quantity)
			doc                  	= frappe.get_doc("BOQ Item", {"bsr_code": i.bsr_code, "parent": i.boq})
			if flt(i.adjustment_quantity) > flt(doc.quantity_after_subcontract):
				frappe.throw("Add Quanity cannot be more than {}".format(doc.quantity_after_subcontract))
			doc.quantity_after_subcontract -= flt(adjustment_quantity)
			doc.save(ignore_permissions = True)

	def update_adjustment_history(self, cancel=False):
		if cancel:
			frappe.db.sql("delete from `tabSubcontract History Item` where parent='{subcontract}' and reference_name = '{reference_name}'".format(subcontract=self.subcontract, reference_name=self.name))

		else:
			doc = frappe.get_doc("Subcontract", self.subcontract)
			row = doc.append("boq_history_item", {})
			row.reference_type          = self.doctype
			row.reference_name          = self.name
			row.reference_date         = self.adjustment_date
			row.initial_amount          = flt(doc.total_amount)
			row.adjustment_amount      	= flt(self.total_amount)
			row.final_amount 			= flt(self.total_amount)+flt(doc.total_amount)
			row.remarks    				= self.remarks
			row.save(ignore_permissions=True)