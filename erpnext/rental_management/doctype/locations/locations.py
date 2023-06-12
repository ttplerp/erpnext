# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt

class Locations(Document):
	def validate(self):
		if not self.description:
			self.description = self.location
		""" Validate duplicate entry """
		data=[]
		for d in self.get('property_management_item'):
			if d.property_management_type not in data:
				data.append(d.property_management_type)
			else:
				frappe.throw("Duplicate data entry at #Row. {}".format(d.idx))

		prop_mgt_amt = 0
		for a in self.get('property_management_item'):
			if a.is_percent == 1:
				a.amount = 0
			else:
				a.percent = 0
			
			prop_mgt_amt += flt(a.amount)
		self.total_property_management_amount = prop_mgt_amt
