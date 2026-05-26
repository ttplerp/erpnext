# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt

class CompleteDeployment(Document):
    def on_submit(self):
        self.update_deployment()
        self.pass_deployment_entry()

    def on_cancel(self):
        self.cancel_deployment_entry()

    def update_deployment(self):
        doc = frappe.get_doc("Desuup Deployment", self.deployment)
        doc.db_set("completed", 1)

    def pass_deployment_entry(self):
        for a in self.items:
            doc = frappe.new_doc("Deployment Entry")
            doc.desuup = a.desuup
            doc.days_attended = a.days_attended
            doc.heart_points = a.heart_points
            doc.pin = a.pin
            doc.desuup_deployment = self.deployment
            doc.complete_deployment = self.name
            doc.submit()

    def cancel_deployment_entry(self):
        frappe.db.sql("delete from `tabDeployment Entry` where complete_deployment = %(complete_deploy)s", {"complete_deploy": self.name})

    @frappe.whitelist()
    def get_applicants(self):
        deploy = frappe.get_doc("Desuup Deployment", self.deployment)

        applicants = dict()
        applicants = frappe.db.sql(""" 
                select  
                name, full_name, phone, email, desuup, cid, gender, batch, (select count(1) from `tabDesuup Attendance` where status = 'Present' and desuup = di.desuup and reference_name = %(dep)s and docstatus = 1) as days_attended 
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
