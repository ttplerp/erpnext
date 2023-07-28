# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class FlatNo(Document):
	def autoname(self):
		# abbr_building_category = frappe.get_value("Building Category", self.building_category, "abbr")

		self.name = "/".join([self.block_no, self.flat_no])

	# def validate(self):
	# 	if not frappe.get_value("Building Category", self.building_category, "abbr"):
	# 		frappe.throw("Abbr required. Missing abbr for Building Category: {}".format(self.building_category))
