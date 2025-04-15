# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class NonCapitalizedAsset(Document):
	def validate(self):
		self.validate_issued_to()

	def validate_issued_to(self):
		if not self.custodian and not self.location:
			frappe.throw("Set either {} or {}.".format(frappe.bold("Custodian"), frappe.bold("Location")))
