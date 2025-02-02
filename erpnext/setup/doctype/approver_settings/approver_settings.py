# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

class ApproverSettings(Document):
	def validate(self):
		if self.supervisors:
			branches = set()
			for d in self.supervisors:
				if d.branch in branches:
					frappe.throw(f"Branch {d.branch} is already selected. Please select a unique branch.")
				branches.add(d.branch)

		if self.managers:
			branches = set()
			for d in self.managers:
				if d.branch in branches:
					frappe.throw(f"Branch {d.branch} is already selected. Please select a unique branch.")
				branches.add(d.branch)
