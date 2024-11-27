# -*- coding: utf-8 -*-
# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document

class TASExtension(Document):
	def validate(self):
		self.validate_dates()

	def on_submit(self):
		self.update_tas_calendar()

	def update_tas_calendar(self):
		doc = frappe.get_doc("TAS Calendar", self.tas_calendar)
		doc.target_start_date = self.target_start_date
		doc.target_end_date = self.target_end_date
		doc.review_start_date = self.review_start_date
		doc.review_end_date = self.review_end_date
		doc.evaluation_start_date = self.evaluation_start_date
		doc.evaluation_end_date = self.evaluation_end_date
		doc.remarks = self.remarks
		doc.save(ignore_permissions=True)
		
	def validate_dates(self):
		if self.target_start_date > self.target_end_date:
			frappe.throw(_("<b>Target Start Date</b> cannot be greater than <b>Target End Date</b>"))
			
		if self.review_start_date < self.target_end_date:
			frappe.throw(_("<b>Review Start Date</b> cannot be greater than <b>Target end date</b>"))
			
		if self.review_start_date > self.review_end_date:
			frappe.throw(_("<b>Review Start Date cannot be greater than <b>Review End Date</b>"))
			
		if self.evaluation_start_date < self.review_end_date:
			frappe.throw(_("<b>Evaluation Start Date</b> cannot be greater than <b>Review End Date</b>"))
			
		if self.evaluation_start_date > self.evaluation_end_date:
			frappe.throw(_("<b>Evaluation Start Date</b> cannot be greater than <b>Evaluation End Date</b>"))
