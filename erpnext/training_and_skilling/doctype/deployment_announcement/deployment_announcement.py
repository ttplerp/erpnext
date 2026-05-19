# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import date_diff, getdate
from frappe.model.mapper import get_mapped_doc

class DeploymentAnnouncement(Document):
    def validate(self):
        self.calculate_values()
        self.validate_dates()

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

        if start_date < getdate(self.registration_deadline):
            frappe.throw("Registration deadline should be before start date")

        if start_date < getdate(self.reporting_date):
            frappe.throw("Reporting Date should be before start date")

        if getdate(self.registration_deadline) > getdate(self.reporting_date):
            frappe.throw("Reporting Date should be after the registration deadline")

    def on_submit(self):
        self.update_announcement()

    def on_cancel(self):
        self.update_announcement()

    def update_announcement(self):
        if self.deployment_requisition:
            doc = frappe.get_doc("Deployment Requisition", self.deployment_requisition)
            doc.db_set("announced", 1 if self.docstatus == 1 else 0)


@frappe.whitelist()
def make_deployment(source_name, target_doc=None):
    doclist = get_mapped_doc(
        "Deployment Announcement",
        source_name,
        {
            "Deployment Announcement": {"doctype": "Desuup Deployment", "validation": {"docstatus": "0"}},
            "field_map": {"deployment_announcement": "name", "type_of_event": "event", "category_of_deployment": "category"}
        },
        target_doc,
    )

    return doclist

@frappe.whitelist()
def make_training_selection(source_name, target_doc=None):
    doclist = get_mapped_doc(
        "Deployment Announcement",
        source_name,
        {
            "Deployment Announcement": {"doctype": "Training Selection", "validation": {"docstatus": "1"}},
            "field_map": {"deployment_announcement": "name", "course_start_date": "start_date", "course_end_date": "end_date", "gender_base_selection": "by_gender", "male_slot": "male_desuups", "female_slot": "female_desuups", "slot": "total_desuups"}
        },
        target_doc,
    )

    return doclist

@frappe.whitelist()
def get_courses(doctype, txt, searchfield, start, page_len, filters):
    if not filters.get("cohort"):
        frappe.throw("Select cohort first")
    return frappe.db.sql("""
            select name, course_name, domain, description from `tabCourse`
                    where name in (
                        select course
                        from `tabCohort Item`
                        where parent = '{cohort}'
                    )
                    and ({key} like %(txt)s
                            or course_name like %(txt)s
                            or domain like %(txt)s)
            order by
                    name, domain, course_name
            limit %(start)s, %(page_len)s""".format(**{
                                            'cohort': filters.get("cohort"),
                                            'key': searchfield,
                            }), {
                                            'txt': "%%%s%%" % txt,
                                            '_txt': txt.replace("%", ""),
                                            'start': start,
                                            'page_len': page_len
    })
