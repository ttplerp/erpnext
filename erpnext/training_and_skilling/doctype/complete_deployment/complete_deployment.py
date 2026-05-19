# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt

class CompleteDeployment(Document):
    def validate(self):
        self.update_deployment()

    def on_submit(self):
        pass 

    def update_deployment(self):
        doc = frappe.get_doc("Desuup Deployment", self.deployment)
        doc.db_set("completed", 1)

    @frappe.whitelist()
    def get_applicants(self):
        deploy = frappe.get_doc("Desuup Deployment", self.deployment)

        applicants = dict()
        applicants = frappe.db.sql(""" 
                select  
                name, full_name, phone, email, desuup, cid, gender, batch, (select count(1) from `tabDesuup Attendance` where status = 'Present' and desuup = di.desuup and reference_name = %(dep)s) as days_attended 
                from `tabDeployment Item` di where docstatus = 1 and parent = %(dep)s 
            """, {"dep": self.deployment}, as_dict=1)    

        pin = frappe.db.get_value("Type of Event", self.event, "pin")
        heart = frappe.db.get_value("Category of Deployment", self.category, "heart_point")

        self.set('items', [])

        for d in applicants:
            d.pin = pin
            d.heart_points = flt(heart) * flt(d.days_attended)
            d.name = None
            row = self.append('items', {})
            row.update(d)
