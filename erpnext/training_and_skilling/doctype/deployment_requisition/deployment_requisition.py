# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import date_diff, getdate
from frappe.model.mapper import get_mapped_doc
from erpnext.custom_utils import queue_sms

class DeploymentRequisition(Document):
    def validate(self):
        self.check_status()
        self.calculate_values()
        self.validate_dates()

    def check_status(self):
        if not self.workflow_state:
            self.workflow_state = "Pending"
        if self.workflow_state in ("Rejected", "Approved"):
            message = "Your application for desuup requirement has been approved"
            if self.workflow_state == "Rejected":
                if self.rejection_reason == "":
                    frappe.throw("Rejection reason is mandatory")
                message = "Your application for desuup requirement has been rejected for " + self.rejection_reason
            queue_sms(self.contactnumber, message)

    def calculate_values(self):
        if getdate(self.end_date) < getdate(self.start_date):
            frappe.throw("End date should be after start date")
        self.duration = date_diff(self.end_date, self.start_date) + 1

        if self.by_gender == "Yes":
            self.total_desuups = self.male_desuups + self.female_desuups
        else:
            self.male_desuups = 0
            self.female_desuups = 0

        if self.total_desuups < 1:
            frappe.throw("Total desuup requirement should be more than 0")

    def validate_dates(self):
        start_date = getdate(self.start_date)

        if start_date < getdate(self.reporting_date):
            frappe.throw("Reporting Date should be before start date")

    def before_submit(self):
        self.check_status()

@frappe.whitelist()
def make_announcement(source_name, target_doc=None):
	doclist = get_mapped_doc(
		"Deployment Requisition",
		source_name,
		{
            "Deployment Requisition": {"doctype": "Deployment Announcement", "validation": {"docstatus": "1", "announced": "0"}},
            "field_map": {"deployment_requisition": "name"}
		},
		target_doc,
	)

	return doclist
