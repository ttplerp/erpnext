# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from erpnext.custom_utils import get_branch_cc, get_cc_customer, sendmail
from frappe.utils import flt
from frappe import _, qb, throw, msgprint
from frappe.utils import date_diff, get_last_day, nowdate, flt

class EquipmentRequest(Document):
	def validate(self):
		self.calculate_percent()
		self.check_rejection_msg()	
		
	def calculate_percent(self):
		total_item = len(self.items)
		per_item = flt(flt(100) / flt(total_item), 2)
		for a in self.items:
			a.percent_share = per_item 

	def on_update_after_submit(self):
		self.check_rejection_msg()
		message = ''
		subject = "Equipment Request Notification"
		recipent = self.owner

		if self.approval_status == 'Available':
			message = "The Equipment Request No: '{0}' is Approved".format(self.name)

		if self.approval_status == 'Unavailable':
			message = "The Equipment Request No: '{0}' is Rejected '{1}'".format(self.name, self.message)

		if self.approval_status == 'Partially Available':
			msg = ''	
			for i in self.items:
				if not i.approved_qty:
					frappe.throw("Approved Qty Is Mandiatory")
				if i.approved_qty > i.qty:
					frappe.throw(" Approved Qty Cannot Be Greater Than Requested Qty")
				msg1 = "({0}: No. Requested: {1}, No. Approved: {2})".format(i.equipment_type, i.qty, i.approved_qty)
				msg = ','.join([msg1])
			message = "The Equipment Request No: '{0}' is Partially Approved as follows: \n {2}".format(self.name, self.approval_status, msg)
		
		frappe.msgprint(message)
		sendmail(recipent, subject, message)

	def check_rejection_msg(self):
		if self.approval_status == 'Unavailable' and self.message == None:
			frappe.throw("Rejection Reason is Mandatory")
	
	@frappe.whitelist()
	def make_hire_form(self):
		for d in self.items:
			from_date = d.from_date
			to_date = d.to_date
			tot_hr = d.total_hours
			location = d.place
			e_type = d.equipment_type

		ehf = frappe.new_doc("Equipment Hiring Form")
		ehf.flags.ignore_permissions=1
		ehf.flags.ignore_mandatory=1
		ehf.branch = self.branch
		ehf.cost_center = self.cost_center
		ehf.request_date = nowdate()
		ehf.start_date = from_date
		ehf.end_date = to_date
		ehf.target_hour = tot_hr 

		ehf.set('request_items',[])
		ehf.append("request_items", {
			"equipment_type": e_type,
			"from_date": from_date,
			"to_date": to_date,
			"number_of_hours": tot_hr,
			"location": location,
			"er_reference": self.name,
			"location": location,
			"number_of_days": flt(date_diff(to_date, from_date))
		})

		ehf.save(ignore_permissions=True)
		self.db_set("ehf", ehf.name)
		return ehf.as_dict()


