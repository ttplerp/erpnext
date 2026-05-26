# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt, cint

class DeploymentApplication(Document):
    def validate(self):
        self.validate_data()
        self.check_conditions()
        self.populate_data()

    def validate_data(self):
        if not self.deployment_announcement:
            frappe.throw("Deployment Announcement is mandatory")
        if not self.desuup:
            frappe.throw("Desuup is mandatory")
        if self.done_manually:
            if self.status in ("Accepted", "Standby"):
                frappe.throw("Can not set status to Accepted/Standby manually")
        for a in frappe.db.sql("""
            SELECT a.name, d.event, d.category 
            FROM `tabDeployment Application` a
            JOIN `tabDeployment Announcement` d ON a.deployment_announcement = d.name
            WHERE a.desuup = %(desuup)s
              AND %(start_date)s <= d.end_date AND 
                  %(end_date)s >= d.start_date AND a.status IN ('Accepted')
            LIMIT 1;""", {"desuup": self.desuup, "start_date": self.start_date, "end_date": self.end_date}, as_dict=1):
            frappe.throw("You are already enrolled for " + a.event + " which has overlapping dates")


    def populate_data(self):
        desup = frappe.get_doc("Desuup", self.desuup)
        self.desuup_name = desup.desuup_name
        self.gender = desup.gender
        self.mobile_number = desup.mobile_number
        self.email_id = desup.email_id

    def check_conditions(self):
        ann = frappe.get_doc("Deployment Announcement", self.deployment_announcement)
        desup = frappe.get_doc("Desuup", self.desuup)

        # Check gender
        if ann.by_gender == "Yes":
            if desup.gender == "Male" and ann.male_desuups < 1:
                frappe.throw("Only female desuups can apply for this position")
            elif desup.gender == "Female" and ann.female_desuups < 1:
                frappe.throw("Only male desuups can apply for this position")

        # Check dzongkhag
        by_dzongkhag = frappe.db.sql("select dzongkhag from `tabDeployment Announcement Dzongkhag` where parent = %(deploy)s", {"deploy": ann.name}, as_dict=1)
        if by_dzongkhag:
            allowed_dzongkhags = [d["dzongkhag"] for d in by_dzongkhag]
            if not any(dzo == desup.present_dzongkhag for dzo in allowed_dzongkhags):
                frappe.throw("Only desuups residing in {} can apply".format(", ".join(allowed_dzongkhags)))

        # Check batch
        by_batch = frappe.db.sql("select batch from `tabDeployment Announcement Batch` where parent = %(deploy)s", {"deploy": ann.name}, as_dict=1)
        if by_batch:
            allowed_batches = [d["batch"] for d in by_batch]
            if not any(batch == desup.batch_number for batch in allowed_batches):
                frappe.throw("Only desuups from batch {} can apply".format(", ".join(allowed_batches)))

        # Check employment status
        if ann.by_employment_status:
            if ann.by_employment_status != desup.employment_type:
                frappe.throw("Only desuups who are {} can apply".format(ann.by_employment_status))

        # Check qualification
        if ann.by_qualification:
            qualified = false
            for q in self.desuup_qualification_table:
                if ann.by_qualification == q.level:
                    qualified = true
                    break
            if not qualified:
                frappe.throw("Only desuups {} are allowed to apply".format(ann.by_qualification))

        # check for duplicate applications
        if frappe.db.get_value("Deployment Application", {"desuup": self.desuup, "name": ["!=", self.name], "deployment_announcement": self.deployment_announcement}, "name"):
            frappe.throw("Application already exists")


