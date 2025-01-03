'''
--------------------------------------------------------------------------------------------------------------------------
Version		  Author		  				CreatedOn		ModifiedOn		 	Remarks
------------ --------------- ------------------ -------------------  -----------------------------------------------------
1.0		      Dawa Nyuehtyue Tshering		2024/11/15		2024/11/15			Original Version
--------------------------------------------------------------------------------------------------------------------------			
'''

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, time_diff_in_hours, get_datetime, getdate, cint, get_datetime_str
from frappe.model.mapper import get_mapped_doc

class MBEntry(Document):
	def validate(self):
		self.set_status()
		self.default_validations()
		self.set_defaults()
		self.calculate_total_amount()
		self.vilidate_milestone_based()
		self.remove_not_selected_bsr()
				
	def on_submit(self):
		self.validate_boq_items()
		self.update_unclaimed_amount()
		self.update_boq_booked_amount()

	def before_cancel(self):
		self.set_status()

	def on_cancel(self):
		self.update_unclaimed_amount(cancel=True)
		self.update_boq_booked_amount(cancel=True)
			
	def set_status(self):
		self.status = {
				"0": "Draft",
				"1": "Uninvoiced",
				"2": "Cancelled"
		}[str(self.docstatus or 0)]
	
	def vilidate_milestone_based(self):
		if self.claim_percent:
			for a in self.items:
				a.entry_quantity 	= (self.claim_percent/100) * a.act_quantity
				a.entry_amount 		= (self.claim_percent/100) * a.act_quantity * a.entry_rate 

	def default_validations(self):
		for rec in self.items:
			if rec.is_selected == 0 or not rec.is_selected:
				frappe.db.sql("""delete from `tabMB Entry BOQ` where name = '{}'""".format(str(rec.name)))

			# entry_amount = round(rec.entry_quantity, 2)*round(rec.entry_rate, 2)
			if flt(rec.entry_quantity) > flt(rec.act_quantity):
				frappe.throw(_("Row{0}: Entry Quantity cannot be greater than Balance Quantity").format(rec.idx))
			elif flt(rec.entry_amount) > flt(rec.act_amount):
				frappe.throw(_("Row{0}: Entry Amount cannot be greater than Balance Amount").format(rec.idx))
			elif flt(rec.entry_quantity) < 0 or flt(rec.entry_amount) < 0:
				frappe.throw(_("Row{0}: Value cannot be in negative").format(rec.idx))

	def remove_not_selected_bsr(self):
		to_remove = []
		for d in self.get("items"):
			if not d.is_selected:
				to_remove.append(d)
		[self.remove(d) for d in to_remove]
			   
	def set_defaults(self):
		if self.project:
			base_project		= frappe.get_doc("Project", self.project)
			self.company		= base_project.company
			self.customer		= base_project.customer
			self.branch		   	= base_project.branch
			self.cost_center	= base_project.cost_center

		if base_project.status in ('Completed','Cancelled'):
			frappe.throw(_("Operation not permitted on already {0} Project.").format(base_project.status),title="MB Entry: Invalid Operation")
				
		if self.boq:
			base_boq			= frappe.get_doc("BOQ", self.boq)
			self.cost_center	= base_boq.cost_center
			self.branch		    = base_boq.branch
			self.boq_type		= base_boq.boq_type
			
	def validate_boq_items(self):
		source_table = "Subcontract" if self.subcontract else "BOQ"
		source = self.subcontract if self.subcontract else self.boq
		
		for rec in self.items:
			if rec.is_selected == 1 and flt(rec.entry_amount) > 0:
				item_result = frappe.db.sql("""select
													ifnull(t2.unclaimed_quantity, 0) as unclaimed_quantity,
													ifnull(t2.unclaimed_amount, 0) as unclaimed_amount
												from
													`tab{1}` t1, `tab{1} Item` t2
												where t1.name = '{2}'
														and t1.name = t2.parent
														and t2.bsr_code = '{0}'
														and t2.boq = '{3}'
														and t1.docstatus = 1
												""".format(rec.bsr_code, source_table, source, rec.boq), as_dict=True)
				
				if item_result:
					item = item_result[0]
					if (flt(rec.entry_quantity) > flt(item.unclaimed_quantity)) or \
					(flt(rec.entry_amount) > flt(item.unclaimed_amount)):
						frappe.throw(_('Row {0}: Insufficient Balance. Please refer to {1}# <a href="#Form/{1}/{2}">{2}</a>').format(
							rec.idx, source_table, source))
				else:
					frappe.throw(_('Row {0}: No balance found for BSR Code {1} in {2}# <a href="#Form/{2}/{3}">{3}</a>').format(
						rec.idx, rec.bsr_code, source_table, source))

	def update_boq_booked_amount(self, cancel=False):
		total_amount = -1*flt(self.total_entry_amount) if cancel else flt(self.total_entry_amount)
		if self.subcontract:
			doc = frappe.get_doc("Subcontract", self.subcontract)
			doc.total_booked_amount += flt(total_amount)
		else:
			doc = frappe.get_doc("BOQ", self.boq)
			doc.total_booked_amount += flt(total_amount)
		doc.save(ignore_permissions=True)
	
	def calculate_total_amount(self):
		total_amount = 0.0
		for d in self.items:
			if d.is_selected:
				total_amount += d.entry_amount
		self.total_entry_amount = total_amount
		self.total_balance_amount = total_amount

	def update_unclaimed_amount(self, cancel=False):
		parent_table = "Subcontract" if self.subcontract else "BOQ"
		child_table  = "Subcontract Item" if self.subcontract else "BOQ Item"
		parent_doc = frappe.get_doc(parent_table, self.subcontract if self.subcontract else self.boq)
		if cancel:
			for item in self.get("items"):
				if item.is_selected and item.bsr_code:
					child_doc = frappe.get_doc(child_table, {'bsr_code': item.bsr_code, 'parent': parent_doc.name})
					child_doc.unclaimed_quantity	+= flt(item.entry_quantity)
					child_doc.unclaimed_amount 		+= flt(item.entry_amount)
					child_doc.booked_quantity 		-= flt(item.entry_quantity)
					child_doc.booked_amount 		-= flt(item.entry_amount)
					child_doc.save(ignore_permissions=True)
		else:			
			for item in self.get("items"):
				if item.is_selected and item.bsr_code:
					child_doc = frappe.get_doc(child_table, {'bsr_code': item.bsr_code, 'parent': parent_doc.name})
					child_doc.unclaimed_quantity	-= flt(item.entry_quantity)
					child_doc.unclaimed_amount 	 	-= flt(item.entry_amount)
					child_doc.booked_quantity 		+= flt(item.entry_quantity)
					child_doc.booked_amount 		+= flt(item.entry_amount)
					child_doc.save(ignore_permissions=True)
			

@frappe.whitelist()
def make_details(source_name, target_doc=None, args=None):
	from frappe.model.mapper import get_mapped_doc

	def post_process(source, target):
		target.child_ref = frappe.flags.args.child_ref
		target.item_name = frappe.flags.args.item_name
		target.uom = frappe.flags.args.uom
		# set_missing_values(source, target_doc)

	# def select_item(d):
	#	 filtered_items = args.get("filtered_children", [])
	#	 child_filter = d.name in filtered_items if filtered_items else True

	#	 return d.ordered_qty < d.stock_qty and child_filter

	doclist = get_mapped_doc(
		"MB Entry",
		source_name,
		{
			"MB Entry": {
				"doctype": "Detailed MB Entry BOQ",
			}
		},
		target_doc,
		post_process,
	)

	return doclist

@frappe.whitelist()
def make_mb_invoice(source_name, target_doc=None):
	def update_master(source_doc, target_doc, source_partent):
		#target_doc.project = source_doc.project
		target_doc.invoice_title = str(target_doc.project) + "(Project Invoice)"
		target_doc.reference_doctype = "MB Entry"
		target_doc.reference_name	= source_doc.name

	def update_reference(source_doc, target_doc, source_parent):
		pass
			
	doclist = get_mapped_doc("MB Entry", source_name, {
		"MB Entry": {
						"doctype": "Project Invoice",
						"field_map":{
								"project": "project",
								"branch": "branch",
								"customer": "customer"
						},
						"postprocess": update_master
				},
	}, target_doc)
	return doclist		
