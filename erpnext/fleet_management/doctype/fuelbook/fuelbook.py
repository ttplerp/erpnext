# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

class Fuelbook(Document):
	def validate(self):
		self.validate_data()

	def validate_data(self):
		if self.expense_limit <= 0:
			frappe.throw("Please set expense limit more than 0")
