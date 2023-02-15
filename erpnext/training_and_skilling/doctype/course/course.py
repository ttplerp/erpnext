# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class Course(Document):
	def validate(self):
		pass
		'''
		if frappe.db.exists("Course", self.course_name):
			self.course_name = str(self.course_name) + " - " +str("1")
		'''
