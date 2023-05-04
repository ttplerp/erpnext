# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class TownCategory(Document):
	def validate(self):
		if not self.description:
			self.description = self.town_category

