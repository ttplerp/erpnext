# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt
from frappe.model.document import Document

class ProjectEquipmentEngagement(Document):
	def validate(self):
		self.validate_items()

	def validate_items(self):
		total_amount = 0.0
		for d in self.items:
			if not d.rate:
				frappe.throw("Please set Rate/Hr in {}".format(frappe.get_desk_link("Equipment", d.equipment)))
			total_amount += flt(d.amount)
		self.total_amount = flt(total_amount)
