# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class DressRequisition(Document):
    def validate(self):
        self.check_duplicate()

    def check_duplicate(self):
        if frappe.db.exists("Dress Requisition", {"status": "Applied", "desuup": self.desuup, "name": ["!=", self.name]}):
            frappe.throw("You have already applied for dress")
