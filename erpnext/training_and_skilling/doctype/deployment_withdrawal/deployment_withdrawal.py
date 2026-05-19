# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import getdate, add_to_date

class DeploymentWithdrawal(Document):
    def validate(self):
        self.validate_info()

    def on_submit(self):
        self.replace_desuup()
        self.update_withdrawn_desuup()

    def validate_info(self):
        # check for desuup
        di_name = frappe.db.get_value("Deployment Item", {"desuup": self.desuup, "parent": self.deployment}, "name")
        if not di_name:
            frappe.throw("The desuup is not part of the deployment")

        # check for date
        deploy = frappe.get_doc("Desuup Deployment", self.deployment)
        if getdate(self.withdrawal_date) > getdate(deploy.end_date) or getdate(self.withdrawal_date) < getdate(deploy.start_date):
            frappe.throw(str(deploy.end_date) + " => " + str(deploy.start_date) + " :: " + str(self.withdrawal_date))
            frappe.throw("Invalid withdrawal date")

        # update status
        frappe.db.sql("update `tabDeployment Item` set status = 'Withdrawal Under Process' where name = %(name)s", {"name": di_name})

    def replace_desuup(self):
        selected = False
        for a in self.items:
            if a.select_desuup:
                selected = True
                depsb = frappe.get_doc("Deployment Standby", a.deployment_standby)
                depsb.db_set("selected_later", 1)

                app = frappe.get_doc("Deployment Application", a.deployment_application)
                app.db_set("status", "Accepted")

                deploy = frappe.get_doc("Desuup Deployment", self.deployment)
                deploy.append("items", {
                        "desuup": a.desuup,
                        "full_name": a.full_name,
                        "cid": a.cid,
                        "gender": a.gender,
                        "phone": a.phone,
                        "email": a.email,
                        "batch": a.batch,
                        "applied_at": a.applied_at,
                        "deployment_application": a.deployment_application,
                        "from_date": self.withdrawal_date,
                        "to_date": deploy.to_date,
                        "status": "Active"
                    })
                deploy.flags.ignore_validate_update_after_submit = True
                deploy.save()
                break
        if not selected:
            frappe.throw("Select a replacement")

    def update_withdrawn_desuup(self):
        di = frappe.get_doc("Deployment Item", {"desuup": self.desuup, "parent": self.deployment})
        di.db_set("to_date", add_to_date(self.withdrawal_date, days=-1))
        di.db_set("status", "Withdrawn")
        
        deploy_app = frappe.get_doc("Deployment Application", di.deployment_application)
        deploy_app.db_set("status", "Withdrawn")
        deploy_app.db_set("withdraw_date", self.withdrawal_date)

    @frappe.whitelist()
    def get_desuups(self):
        deploy = frappe.get_doc("Desuup Deployment", self.deployment)
        ann = frappe.get_doc("Deployment Announcement", deploy.deployment_announcement)

        desuups = dict()
        if ann.by_gender == "No":
            desuups = frappe.db.sql(""" 
                    select  
                    name, full_name, phone, email, desuup, cid, gender, batch, applied_at, deployment_application
                    from `tabDeployment Standby` where selected_later = 0 and docstatus = 1 and parent = %(deploy)s 
                    order by applied_at asc
                """, {"deploy": self.deployment}, as_dict=1)    
        else:
            desup = frappe.get_doc("Desuup", self.desuup)
            if desup.gender == "Male":
                desuups = frappe.db.sql("""
                    select  
                    name, full_name, phone, email, desuup, cid, gender, batch, applied_at, deployment_application
                    from `tabDeployment Standby` where selected_later = 0 and docstatus = 1 and parent = %(deploy)s and gender = 'Male' 
                    order by applied_at asc
                """, {"deploy": self.deployment}, as_dict=1)    
            else:
                desuups = frappe.db.sql("""
                    select  
                    name, full_name, phone, email, desuup, cid, gender, batch, applied_at, deployment_application
                    from `tabDeployment Standby` where selected_later = 0 and docstatus = 1 and parent = %(deploy)s and gender = 'Female' 
                    order by applied_at asc
                """, {"deploy": self.deployment}, as_dict=1)    
        self.set('items', [])

        for d in desuups:
            d.deployment_standby = d.name
            d.name = None
            row = self.append('items', {})
            row.update(d)
