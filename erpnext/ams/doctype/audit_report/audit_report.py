# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.mapper import get_mapped_doc
from frappe.model.document import Document
from erpnext.custom_workflow import validate_workflow_states, notify_workflow_states

class AuditReport(Document):
	def validate(self):
		self.set_supervisor()
		self.validate_assigned_accountability()
		# validate_workflow_states(self)
		# notify_workflow_states(self)

	def on_submit(self):
		pass
		# self.update_audit_status()
		# self.update_execute_checklist_item()
  
	def on_cancel(self):
		pass
		# self.update_audit_status(1)
		# self.update_execute_checklist_item(1)

	def validate_assigned_accountability(self):
		if not self.direct_accountability and not self.supervisor_accountability:
			return

		for d in self.direct_accountability:
			if not d.employee:
				frappe.throw('Employee is mandatory in Direct Accountability for Para No: <b>{}</b>'.format(d.para_no))
			# if not frappe.db.exists("Employee", d.employee):
			# 	frappe.throw('Employee: <b>{}</b> does not exist in the system.'.format(d.employee))

		for s in self.supervisor_accountability:
			if not s.supervisor:
				frappe.throw('Supervisor is mandatory in Supervisor Accountability for Para No: <b>{}</b>'.format(s.para_no))
			# if not frappe.db.exists("Employee", s.supervisor):
			# 	frappe.throw('Supervisor: <b>{}</b> does not exist in the system.'.format(s.supervisor))
		
	def set_supervisor(self):
		if not self.supervisor_id:
			if frappe.db.exists("Employee", {"user_id":frappe.session.user}):
				doc = frappe.get_doc("Employee", {"user_id":frappe.session.user})
				if doc.reports_to:
					self.supervisor_id = frappe.db.get_value("Employee", doc.reports_to, "user_id")

	# disabled func. for now.
	def update_audit_status(self, cancel=0):
		if frappe.db.exists("Prepare Audit Plan", self.prepare_audit_plan_no):
			pap_doc = frappe.get_doc("Prepare Audit Plan", self.prepare_audit_plan_no)
			eu_doc = frappe.get_doc("Execute Audit", self.execute_audit_no)
			
			if not cancel:
				pap_doc.db_set("status", self.report_status)
				eu_doc.db_set("status", self.report_status)
			else:
				if eu_doc.docstatus == 1:
					pap_doc.db_set("status", 'Audit Execution')
					eu_doc.db_set("status", 'Exit Meeting')
				else:
					ael_doc = frappe.get_doc("Audit Engagement Letter", self.audit_engagement_letter)
					if ael_doc.docstatus == 1:
						pap_doc.db_set("status", 'Engagement Letter')
					else:
						pap_doc.db_set("status", 'Pending')
					eu_doc.db_set("status", 'Pending')
  
	def update_execute_checklist_item(self, cancel=0):
		ea = frappe.get_doc("Execute Audit", self.execute_audit_no)
		initial_report = frappe.get_doc("Audit Report", self.name)

		if not cancel:
			for eaci in ea.get("audit_checklist"):
				for cl in initial_report.get("audit_checklist"):
					if cl.audit_area_checklist == eaci.audit_area_checklist and cl.observation_title == eaci.observation_title:
						eaci.db_set("status",cl.status)
						eaci.db_set("audit_remarks",cl.audit_remarks)
						eaci.db_set("auditee_remarks",cl.auditee_remarks)
		else:
			for eaci in ea.get("audit_checklist"):
				if eaci.audit_remarks or eaci.auditee_remarks:
					eaci.db_set("status",'Open')
					eaci.db_set("audit_remarks",'')
					eaci.db_set("auditee_remarks",'')

	@frappe.whitelist()
	def get_auditor_and_auditee(self):
		auditor_display = auditee_display = 0
		auditors = auditees = []
		for auditor in self.audit_team:
			auditors.append(frappe.db.get_value("Employee", auditor.employee, "user_id"))
		for auditee_emp in self.direct_accountability:
			auditees.append(frappe.db.get_value("Employee", auditee_emp.employee, "user_id"))
		for auditee_sup in self.supervisor_accountability:
				auditees.append(frappe.db.get_value("Employee", auditee_sup.supervisor, "user_id"))
		if frappe.session.user == "Administrator":
			auditor_display = auditee_display = 1
		if frappe.session.user in auditors:
			auditor_display = 1
		if frappe.session.user in auditees:
			auditee_display = 1
		return auditor_display, auditee_display

	@frappe.whitelist()
	def get_audit_checklist(self):
		data = frappe.db.sql("""
			SELECT 
				eaci.audit_area_checklist, eaci.observation_title, eaci.nature_of_irregularity, eaci.status
			FROM 
				`tabExecute Audit` ea 
			INNER JOIN
				`tabExecute Audit Checklist Item` eaci
			ON
				ea.name = eaci.parent
				AND eaci.status != 'Closed'
			WHERE			
				ea.name = '{}' 
			AND
				ea.docstatus = 1 
			ORDER BY eaci.audit_area_checklist
		""".format(self.execute_audit_no), as_dict=True)

		if not data:
			frappe.throw(_('There are no Audit Observation defined for Execute Audit No. <b>{}</b>'.format(self.execute_audit_no)))

		self.set('audit_checklist', [])
		for d in data:
			row = self.append('audit_checklist',{})
			row.update(d)
	
	@frappe.whitelist()
	def get_observation(self):
		data = frappe.db.sql("""
			select 
				audit_area_checklist as checklist, para_no, para_title, observation
			from 
				`tabAudit Initial Report Checklist Item`
			where 
				parent = '{0}'
			order by para_no
		""".format(self.name), as_dict=True)

		if not data:
			frappe.throw('There are no Observation defined for Audit Report: <b>{}</b>'.format(self.name))

		self.set('direct_accountability', [])
		self.set('supervisor_accountability', [])
		for d in data:
			row = self.append('direct_accountability',{})
			row2 = self.append('supervisor_accountability', {})
			row2.update(d)
			row.update(d)

	#To display declaration field/create draft report button based on auditor logged in
	@frappe.whitelist()
	def check_auditor_and_audit_report(self):
		display = audit_report = 0
		for auditor in self.audit_team:
			if frappe.session.user == frappe.db.get_value("Employee",auditor.employee,"user_id"):
				display = 1
		return display

@frappe.whitelist()
def create_follow_up(source_name, target_doc=None):
	doclist = get_mapped_doc("Audit Report", source_name, {
		"Audit Report": {
			"doctype": "Follow Up",
			"field_map": {
				"name": "execute_audit_no",
				# "execute_audit_date": "posting_date",
				"audit_team": "audit_team",
				# "audit_checklist": "audit_checklist",
			}
		},
		"Audit Initial Report DA Item": {
					"doctype": "Follow Up DA Item",
					"field_map": [
						["child_ref", "name"],
					]
				},
		"Direct Accountability Supervisor Item": {
					"doctype": "Direct Accountability Supervisor Item",
					"field_map": [
						["child_ref", "name"],
					]
				},
	}, target_doc)

	return doclist

def get_permission_query_conditions(user):
	if not user:
		user = frappe.session.user
	user_roles = frappe.get_roles(user)

	if user == "Administrator" or "System Manager" in user_roles or "Auditor" in user_roles or "Head Audit" in user_roles:
		return

	return """(
		exists(select 1
			from `tabEmployee` as e
			where e.employee = `tabAudit Initial Report`.supervisor_id
			and e.user_id = '{user}'
   			and `tabAudit Initial Report`.workflow_state in ('Waiting for Auditee Remarks','Approved'))
	)""".format(user=user)
