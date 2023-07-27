# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt
from frappe.model.document import Document

class DetailedMBEntryBOQ(Document):
	def validate(self):
		self.calculate_entry_quantity()
		self.validate_child_ref()

	def validate_child_ref(self):
		if not self.child_ref:
			frappe.throw("Detailed MB Entry BOQ should be created from MB Entry BOQ table.")

	def calculate_entry_quantity(self):
		entry_qty = 0
		for a in self.items:
			entry_qty += a.quantity
		self.entry_quantity = flt(entry_qty,2)

	def on_submit(self):
		self.update_child_ref()
		mb_doc = frappe.get_doc("MB Entry", self.mb_entry)
		mb_doc.calulate_total_amount()

	def update_child_ref(self):
		frappe.db.sql("""
			update `tabMB Entry BOQ` set entry_quantity = {0}, detailed_mb_id = '{1}',
			entry_amount = round({0}*entry_rate,2)
			where name = '{2}'
		""".format(self.entry_quantity, self.name, self.child_ref))


	@frappe.whitelist()
	def fetch_item_details(self):
		if not self.child_ref:
			frappe.throw("Detailed MB Entry BOQ should be created from MB Entry BOQ table.")
		length, breadth, height = frappe.db.get_value("MB Entry BOQ", self.child_ref, "length"), frappe.db.get_value("MB Entry BOQ", self.child_ref, "breath"), frappe.db.get_value("MB Entry BOQ", self.child_ref, "height")
		return length, breadth, height
