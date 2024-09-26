# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class TravelRoute(Document):
	def autoname(self):
		if self.travel_from and self.travel_to:
			self.name = f"{self.travel_from}-{self.travel_to}"