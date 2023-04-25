# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document

class EquipmentModel(Document):
	def validate(self):
		if not self.description:
			self.description = self.model
