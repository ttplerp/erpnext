# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from erpnext.custom_workflow import validate_workflow_states, notify_workflow_states
from frappe import _

class AuditEngagementLetter(Document):
	def validate(self):
		validate_workflow_states(self)
		notify_workflow_states(self)
   
	def on_submit(self):
		self.update_engagement_letter_no()
  
	def on_cancel(self):
		self.update_engagement_letter_no(1)
 
	def update_engagement_letter_no(self, cancel=0):
		pap_doc = frappe.get_doc("Prepare Audit Plan", self.prepare_audit_plan_no)
		if not cancel:
			pap_doc.db_set("audit_engagement_letter", self.name)
			pap_doc.db_set("status", 'Engagement Letter')
		else:
			pap_doc.db_set("audit_engagement_letter", '')
			pap_doc.db_set("status", 'Pending')
  
	# Get audit tean from Prepare Audit Plan
	def get_audit_team(self):
		data = frappe.db.sql("""
			SELECT 
				papi.employee,
				papi.employee_name,
				papi.designation,
				papi.audit_role
			FROM 
				`tabPrepare Audit Plan` pap 
			INNER JOIN
				`tabPAP Audit Team Item` papi
			ON
				pap.name = papi.parent			
			WHERE			
				pap.name = '{}' 
			AND
				pap.docstatus = 1 
			ORDER BY papi.idx
		""".format(self.prepare_audit_plan_no), as_dict=True)

		if not data:
			frappe.throw(_('There are no Audit Team defined for Prepare Audit Plan No. <b>{}</b>'.format(self.prepare_audit_plan_no)))

		self.set('audit_team', [])
		for d in data:
			row = self.append('audit_team',{})
			row.update(d)

def get_permission_query_conditions(user):
    if not user:
        user = frappe.session.user
    user_roles = frappe.get_roles(user)

    if user == "Administrator" or "System Manager" in user_roles or "Auditor" in user_roles or "Head Audit" in user_roles:
        return

    return """(
		exists(select 1
			from `tabEmployee` as e
			where e.employee = `tabAudit Engagement Letter`.supervisor_id
			and e.user_id = '{user}'
		)
	)""".format(user=user)
