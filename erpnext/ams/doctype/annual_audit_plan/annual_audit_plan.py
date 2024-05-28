# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc

class AnnualAuditPlan(Document):
	def validate(self):
		self.validate_dates()
	 
	def validate_dates(self):
		if self.q1_start_date > self.q1_end_date:
			frappe.throw(_("Quarter 1 start date can not be greater than Quarter 1 end date"))

		if self.q2_start_date > self.q2_end_date:
			frappe.throw(_("Quarter 2 start date can not be greater than Quarter 2 end date"))

		if self.q3_start_date > self.q3_end_date:
			frappe.throw(_("Quarter 3 start date can not be greater than Quarter 3 end date"))

		if self.q4_start_date > self.q4_end_date:
			frappe.throw(_("Quarter 4 start date can not be greater than Quarter 4 end date"))

# @frappe.whitelist()
# def create_aap_extension(source_name, target_doc=None):
# 	doclist = get_mapped_doc("Annual Audit Plan", source_name, {
# 		"Annual Audit Plan": {
# 			"doctype": "Annual Audit Plan Extension",
# 			"field_map": {
#                 "annual_audit_plan": "name"
#             }
# 		},
# 	}, target_doc)

# 	return doclist
