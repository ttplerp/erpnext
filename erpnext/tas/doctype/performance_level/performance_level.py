# -*- coding: utf-8 -*-
# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import cint
from frappe.model.document import Document

class PerformanceLevel(Document):
	def validate(self):
		self.validate_root_level()
		self.validate_parent_level()

	def validate_root_level(self):
		if cint(self.is_root_level) and self.parent_level:
			frappe.throw(_("<b>Parent Level</b> is not permitted for Root Level"))

		if cint(self.is_root_level) and frappe.db.exists("Performance Level", {"is_root_level": 1, "name": ("!=",self.name)}):
			frappe.throw(_("There is another root level already exists"))

	def validate_parent_level(self):
		if self.name == self.parent_level:
			frappe.throw(_("<b>Parent Level</b> cannot be same as <b>Performance Level</b>"))
