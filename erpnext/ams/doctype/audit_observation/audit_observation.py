# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class AuditObservation(Document):
	@frappe.whitelist()
	def get_supervisor_details(self):
		"""Fetches the supervisor details for the audit observation."""
		if self.supervisor_id:
			return frappe.get_doc("Employee", self.supervisor_id)
		else:
			frappe.throw("Employee is not set for this audit observation.")

	@frappe.whitelist()
	def get_supervisor_details(self, employee):
		"""Fetches the supervisor details for the audit observation."""
		if employee:
			return frappe.get_doc("Employee", employee)
		else:
			frappe.throw("Employee is not set for this audit observation.")

def get_permission_query_conditions(user):
    if not user: user = frappe.session.user
    user_roles = frappe.get_roles(user)

    if user == "Administrator":
        return
    if "Audit User" in user_roles:
        return

    return """(
        `tabAudit Observation`.owner = '{user}'
        or
        exists(select 1
                from `tabEmployee`
                where `tabEmployee`.name = `tabAudit Observation`.supervisor_id
                and `tabEmployee`.user_id = '{user}')
        or
        exists(select 1
                from `tabEmployee`, `tabExecute Audit Team Item I` 
                where `tabEmployee`.name = `tabExecute Audit Team Item I`.employee and `tabAudit Observation`.name = `tabExecute Audit Team Item I`.parent
                and `tabEmployee`.user_id = '{user}')
		or
        exists(select 1
                from `tabEmployee`, `tabDirect Accountability Item I` 
                where `tabEmployee`.name = `tabDirect Accountability Item I`.employee and `tabAudit Observation`.name = `tabDirect Accountability Item I`.parent
                and `tabEmployee`.user_id = '{user}')
		or
        exists(select 1
                from `tabEmployee`, `tabDirect Accountability Item I` 
                where `tabEmployee`.name = `tabDirect Accountability Item I`.supervisor and `tabAudit Observation`.name = `tabDirect Accountability Item I`.parent
                and `tabEmployee`.user_id = '{user}')
    )""".format(user=user)