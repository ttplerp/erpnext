# -*- coding: utf-8 -*-
# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import flt
from frappe import _

class CommonTarget(Document):
	def validate(self):
		self.check_target()

	def check_target(self):  
		
		for i, t in enumerate(self.targets):
			if t.qty_quality == 'Quantity' and flt(t.quantity) <= 0 :
				frappe.throw(
					title=_('Error'),
					msg=_("<b>{}</b> value is not allowed for <b>Quantity</b> in Target Item at Row <b>{}</b>".format(t.quantity,i+1)))

			if t.qty_quality == 'Quality' and flt(t.quality) <= 0 :
				frappe.throw(
					title=_("Error"),
					msg=_("<b>{}</b> value is not allowed for <b>Quality</b> in Target Item at Row <b>{}</b>".format(t.quality,i+1)))

			if flt(t.weightage) > flt(self.max_weightage_for_target) or flt(t.weightage) < flt(self.min_weightage_for_target):
				frappe.throw(
					title=_('Error'),
					msg="Weightage for target must be between <b>{}</b> and <b>{}</b> but you have set <b>{}</b> at row <b>{}</b>".format(self.min_weightage_for_target,self.max_weightage_for_target,t.weightage, i+1))

			if flt(t.timeline) <= 0:
				frappe.throw(
					title=_("Error"),
					msg=_("<b>{}</b> value is not allowed for <b>Timeline</b> in Target Item at Row <b>{}</b>".format(t.timeline,i+1)))
			
			if t.qty_quality == 'Quantity':
				t.quality = None

			if t.qty_quality == 'Quality':
				t.quantity = None