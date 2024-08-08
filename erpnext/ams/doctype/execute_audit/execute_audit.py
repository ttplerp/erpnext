# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
from ast import Pass
import frappe
from frappe import _
from frappe.utils import flt,nowdate
from frappe.model.mapper import get_mapped_doc
from frappe.model.document import Document
from erpnext.custom_workflow import validate_workflow_states, notify_workflow_states

class ExecuteAudit(Document):
	def validate(self):
		pass
		# if self.workflow_state == 'Assigned':
		# 	self.validate_accountability_assigner()
		# validate_workflow_states(self)
		# notify_workflow_states(self)

	def on_submit(self):
		self.update_status()
  
	def on_cancel(self):
		self.update_status(1)

	@frappe.whitelist()
	def validate_accountability_assigner(self):
		if frappe.session.user != self.supervisor_email:
			frappe.throw("Only <b>{}</b> can Assign Direct Accountability for this request".format(self.supervisor_name))
			
	def update_status(self, cancel=0):
		pap = frappe.get_doc("Prepare Audit Plan", self.prepare_audit_plan_no)
		execute_audit = frappe.get_doc("Execute Audit", self.name)
		if not cancel:
			pap.db_set("status", 'Audit Execution')
			execute_audit.db_set("status", 'Exit Meeting')
			for cl in execute_audit.get("audit_checklist"):
				if cl.nature_of_irregularity in ('For Information','Found in order','Resolved'):
					cl.db_set("status", 'Closed')
		else:
			pap.db_set("status", 'Engagement Letter')
			execute_audit.db_set("status", 'Pending')
			for cl in execute_audit.get("audit_checklist"):
				if cl.nature_of_irregularity in ('Observation','Unresolved','Un-Reconciled'):
					cl.db_set("status", 'Open')

	@frappe.whitelist()
	def get_audit_team(self):
		data = frappe.db.sql("""
			SELECT 
				papi.employee, papi.employee_name, papi.designation, papi.audit_role
			FROM 
				`tabPrepare Audit Plan` pap 
			INNER JOIN
				`tabPAP Audit Team Item` papi
			ON
				pap.name = papi.parent
			WHERE			
				pap.name = '{}' AND pap.docstatus = 1 
			ORDER BY papi.idx
		""".format(self.prepare_audit_plan_no), as_dict=True)

		if not data:
			frappe.throw(_('There are no Audit Team defined for Prepare Audit Plan No. <b>{}</b>'.format(self.prepare_audit_plan_no)))

		self.set('audit_team', [])
		for d in data:
			row = self.append('audit_team',{})
			row.update(d)
	
	@frappe.whitelist()
	def get_checklist(self):
		data = frappe.db.sql("""
			SELECT 
				papi.audit_area_checklist, 'Open' status
			FROM 
				`tabPrepare Audit Plan` pap 
			INNER JOIN
				`tabPAP Checklist Item` papi
			ON
				pap.name = papi.parent
			WHERE
				pap.name = '{}' AND pap.docstatus = 1 
			ORDER BY papi.audit_area_checklist
		""".format(self.prepare_audit_plan_no), as_dict=True)

		if not data:
			frappe.throw(_('There are no Checklist defined for Prepare Audit Plan No. <b>{}</b>'.format(self.prepare_audit_plan_no)))

		self.set('audit_checklist', [])
		for d in data:
			row = self.append('audit_checklist',{})
			row.update(d)

	@frappe.whitelist()
	def get_observation(self):
		data = frappe.db.sql("""
			select 
				audit_area_checklist as checklist, observation_title, observation
			from 
				`tabExecute Audit Checklist Item`
			where 
				parent = '{0}' and nature_of_irregularity not in ('For Information','Found in order','Resolved')
			order by audit_area_checklist
		""".format(self.name), as_dict=True)

		if not data:
			frappe.throw(_('There are no Observation defined for Execute Audit: <b>{}</b>'.format(self.name)))

		self.set('direct_accountability', [])
		for d in data:
			row = self.append('direct_accountability',{})
			row.update(d)		
   
@frappe.whitelist()
def create_initial_report(source_name, target_doc=None):
	doclist = get_mapped_doc("Execute Audit", source_name, {
		"Execute Audit": {
			"doctype": "Audit Initial Report",
			"field_map": {
				"execute_audit_no": "name",
				"execute_audit_date": "posting_date",
				"audit_team": "audit_team",
				"direct_accountability": "direct_accountability"
			}
		},
	}, target_doc)

	return doclist

def get_permission_query_conditions(user):
	if not user: user = frappe.session.user
	user_roles = frappe.get_roles(user)

	if user == "Administrator" or "System Manager" in user_roles or "Auditor" in user_roles:
		return

	return """(
		`tabExecute Audit`.owner = '{user}'
		or
		exists(select 1
			from `tabEmployee`
			where `tabEmployee`.name = `tabExecute Audit`.supervisor_id
			and `tabEmployee`.user_id = '{user}')
		)""".format(user=user)
