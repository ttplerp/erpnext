# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class Questionaire(Document):
    def validate(self):
        if self.to_date < self.from_date:
            frappe.throw("To date can not be before from date")
