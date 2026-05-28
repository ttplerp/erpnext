# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from erpnext.custom_utils import queue_message, create_message

class DressRequisition(Document):
    def validate(self):
        self.check_duplicate()

    def check_duplicate(self):
        if frappe.db.exists("Dress Requisition", {"status": "Applied", "desuup": self.desuup, "name": ["!=", self.name]}):
            frappe.throw("You have already applied for dress")

    def on_update_after_submit(self):
        if self.status == "Rejected":
            queue_message(self, self.desuup, "Your dress requisition has been Rejected")
        elif self.status == "Approved":
            queue_message(self, self.desuup, "Your dress requisition has been Approved")
        else:
            pass
