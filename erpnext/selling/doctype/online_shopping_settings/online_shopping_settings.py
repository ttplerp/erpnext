# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt

class OnlineShoppingSettings(Document):
    def validate(self):
        self.validate_items()

    def validate_items(self):
        seen = set()
        for a in self.items:
            if a.item_code in seen:
                frappe.throw(f"Item Code {a.item_code} is defined more than once")
            seen.add(a.item_code)
            if not flt(a.selling_price) > 0:
                frappe.throw(f"Invalid selling price for item {a.item_code} on row {a.idx}")
