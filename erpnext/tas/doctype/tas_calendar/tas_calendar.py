# -*- coding: utf-8 -*-
# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc

class TASCalendar(Document):
	def validate(self):		  
		self.validate_dates()
		self.validate_weightage()
			
	def validate_dates(self):
		if self.target_start_date > self.target_end_date:
			frappe.throw(_("Target start date can not be greater than target end date"))

		if self.review_start_date < self.target_end_date:
			frappe.throw(_("Review start date can not be greater than target end date"))

		if self.review_start_date > self.review_end_date:
			frappe.throw(_("Review start date can not be greater than review end date"))

		if self.evaluation_start_date < self.review_end_date:
			frappe.throw(_("Evaluation start date can not be greater than review end date"))   

		if self.evaluation_start_date > self.evaluation_end_date:
			frappe.throw(_("Evaluation start date can not be greater than evaluation end date"))

	def validate_weightage(self):
		if flt(self.financial_target_weightage) < 0:
			frappe.throw(_("<b>Financial Target Weightage</b> should be greater than or equal to 0"), title="Error")
		elif flt(self.non_financial_target_weightage) < 0:
			frappe.throw(_("<b>Non-Financial Target Weightage</b> should be greater than or equal to 0"), title="Error")
		elif flt(self.common_target_weightage) < 0:
			frappe.throw(_("<b>Common Target Weightage</b> should be greater than or equal to 0"), title="Error")

		if(flt(self.financial_target_weightage)+flt(self.non_financial_target_weightage)+flt(self.common_target_weightage)) != 100:
			frappe.throw(_("Total target weightage should be equal to 100"))

@frappe.whitelist()
def create_tas_extension(source_name, target_doc=None):
	doclist = get_mapped_doc("TAS Calendar", source_name, {
		"TAS Calendar": {
			"doctype": "TAS Extension",
			"field_map": {
                "tas_calendar": "name"
            }
		},
	}, target_doc)

	return doclist