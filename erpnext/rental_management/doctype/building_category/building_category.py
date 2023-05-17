# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class BuildingCategory(Document):
	def validate(self):
		abbr_building_category = "".join(c[0] for c in self.building_category.split()).upper()
		abbr_building_category.strip()

		if not self.abbr:
			self.abbr = abbr_building_category
