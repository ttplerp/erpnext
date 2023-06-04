# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class BlockNo(Document):
	def autoname(self):
		abbr_building_category = frappe.get_value("Building Category", self.building_category, "abbr")

		self.name = "/".join([self.location, abbr_building_category, self.block_no])
	
	def validate(self):
		if not frappe.get_value("Building Category", self.building_category, "abbr"):
			frappe.throw("Abbr required. Missing abbr for Building Category: {}".format(self.building_category))
		""" Validate duplicate entry """
		data=[]
		for d in self.get('block_property_management_item'):
			if d.property_management_type not in data:
				data.append(d.property_management_type)
			else:
				frappe.throw("Duplicate data entry at #Row. {}".format(d.idx))

