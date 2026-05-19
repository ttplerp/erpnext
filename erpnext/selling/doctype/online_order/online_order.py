# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import cint, flt, today
from frappe.model.mapper import get_mapped_doc
from erpnext.custom_utils import create_message

class OnlineOrder(Document):
    def validate(self):
        self.validate_items()

    def validate_items(self):
        total_price = 0
        for a in self.items:
            if a.qty < 1:
                frappe.throw(f"Invalid quantity for {a.item_code}")
            a.price = frappe.db.get_value("Online Shopping Settings Item", {"item_code": a.item_code, "disable": 0}, "selling_price")
            if not a.price:
                frappe.throw(f"Invalid item {a.item_code}")
            if not flt(a.price) > 0:
                frappe.throw(f"Invalid price for {a.item_name}")
            a.total_price = cint(a.qty) * flt(a.price)
            total_price += flt(a.total_price)
        self.total_amount = total_price

    def on_submit(self):
        self.validate_status()

    def on_update_after_submit(self):
        self.validate_status()

    def validate_status(self):
        if self.ready_for_pickup:
            self.db_set("status", "Ready for pickup")
            create_message(self, self.desuup, "Your order is ready for pickup")

@frappe.whitelist()
def create_stock_entry(docname):
    o = frappe.get_doc("Online Order", docname)
    s = frappe.new_doc("Stock Entry")
    s.title = "online ordered by {}".format(o.desuup_name)
    s.branch = o.branch
    s.stock_entry_type = "Material Issue"
    s.posting_date = today()
    s.from_warehouse = o.warehouse

    for i in o.items:
        s.append("items", {
            "item_code": i.item_code,
            "s_warehouse": o.warehouse,
            "qty": i.qty,
            "cost_enter": o.cost_center
        })
    s.docstatus = 1
    s.save(ignore_permissions=True)
    o.db_set("stock_entry", s.name)
    o.db_set("status", "Delivered")

@frappe.whitelist()
def receive_payment(source_name, target_doc=None):
    doclist = get_mapped_doc(
        "Online Order",
        source_name,
        {
            "Online Order": {"doctype": "Online Order Payment", "validation": {"docstatus": "1", "status": "Ordered"}},
            "field_map": {"online_order": "name", "posting_date": today()}
        },
        target_doc,
    )

    return doclist
