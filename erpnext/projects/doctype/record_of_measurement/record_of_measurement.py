# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt
from frappe.model.document import Document

class RecordOfMeasurement(Document):
	def validate(self):
		self.calculate_entry_quantity()
		self.validate_child_ref()

	def validate_child_ref(self):
		if not self.child_ref:
			frappe.throw("Record Of Measurement should be created from BOQ table.")

	def calculate_entry_quantity(self):
		entry_qty = 0
		amount = 0
		for a in self.items:
			entry_qty += a.quantity
			amount += a.amount
		self.entry_quantity = flt(entry_qty,2)
		self.amount = flt(amount,2)


	@frappe.whitelist()
	def fetch_item_details(self):
		if not self.child_ref:
			frappe.throw("Detailed MB Entry BOQ should be created from MB Entry BOQ table.")
		length, breadth, height = frappe.db.get_value("BOQ Item", self.child_ref, "length"), frappe.db.get_value("BOQ Item", self.child_ref, "breath"), frappe.db.get_value("BOQ Item", self.child_ref, "height")
		return length, breadth, height
