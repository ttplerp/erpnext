# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class Region(Document):
	pass

	@frappe.whitelist()
	def get_branch(self):
		self.set('items',[])
		for item in frappe.get_list("Branch",fields=['branch','cost_center']):
			self.append('items',{"branch":item.branch,"cost_center":item.cost_center})