# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import flt,nowdate,formatdate
from frappe import _
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc

class PrepareAuditPlan(Document):
	def validate(self):
		self.validate_audit_team()
		self.validate_audit_role()
		self.validate_type_frequency()

	#To check duplicate audit team
	@frappe.whitelist()
	def validate_audit_team(self):
		audit_team = {}
		for i in self.get("audit_team"):
			if i.employee in audit_team:
				frappe.throw(_("Row#{}: Duplicate entry for Employee {} in Audit Team").format(i.idx,i.employee))
			audit_team[i.employee] = i
   
	#To check duplicate audit role
	@frappe.whitelist()
	def validate_audit_role(self):
		audit_team = {}
		for i in self.get("audit_team"):
			if i.audit_role in audit_team and i.audit_role != 'Auditor':
				frappe.throw(_("Row#{}: Only one <b>{}</b> role in Audit Team is allowed").format(i.idx,i.audit_role))
			audit_team[i.audit_role] = i
	
	#To check if there's any duplicate in audit checklist
	def validate_audit_checklist(self):
		audit_checklist = {}
		for i in self.get("audit_checklist"):
			if i.audit_area_checklist in audit_checklist:
				frappe.throw(_("Row#{}: Duplication of {} cannot be accepted in Audit Area Checklist").format(i.idx,i.audit_area_checklist))
			audit_checklist[i.audit_area_checklist] = i
	
	def validate_type_frequency(self):       
		if self.type == 'Regular Audit' and self.frequency == 'Ad-hoc':			
			frappe.throw(_('You are not allow to select <b>Ad-hoc</b> as Frequecy for <b>Regular Audit</b>!!!'))
    
		if self.type == 'Ad-hoc Audit' and self.frequency != 'Ad-hoc':			
			frappe.throw(_('Select <b>Ad-hoc</b> as Frequecy for <b>Ad-hoc Audit</b>!!!'))
    
	# get Audit Checklist based on branch/HO
	@frappe.whitelist()
	def get_audit_checklist(self):
		query = """
				SELECT ac.name as audit_area_checklist, ac.audit_criteria, ac.type_of_audit
				FROM 
					`tabAudit Checklist` ac 
				WHERE	
					ac.is_for_ho = '{}' OR ac.is_for_both = 1 and ac.is_disabled != 1
				ORDER BY 
					ac.type_of_audit
			""".format(self.is_ho_branch)
		data = frappe.db.sql(query, as_dict=True)

		if not data:
			frappe.throw(_('No Checklist found'))
			
		self.set('audit_checklist', [])
		for d in data:
			row = self.append('audit_checklist', {})
			row.update(d)

@frappe.whitelist()
def create_engagement(source_name, target_doc=None):
	doclist = get_mapped_doc("Prepare Audit Plan", source_name, {
		"Prepare Audit Plan": {
			"doctype": "Audit Engagement Letter",
			"field_map": {
				"prepare_audit_plan_no": "name",
				"reference_date": "creation_date"
			}
		},
	}, target_doc)

	return doclist

@frappe.whitelist()
def create_execute_audit(source_name, target_doc=None):
	def set_missing_values(source, target):
		target.status = "Pending"

	doclist = get_mapped_doc("Prepare Audit Plan", source_name, {
		"Prepare Audit Plan": {
			"doctype": "Execute Audit",
			"field_map": {
				"prepare_audit_plan_no": "name",
				"positing_date": "creation_date"
			}
		},
	}, target_doc, set_missing_values)

	return doclist

def get_permission_query_conditions(user):
    if not user:
        user = frappe.session.user
    user_roles = frappe.get_roles(user)

    if user == "Administrator" or "System Manager" in user_roles or "Auditor" in user_roles:
        return

    return """(
		exists(select 1
			from `tabEmployee` as e, `tabAudit Engagement Letter` as a
			where e.employee = `tabPrepare Audit Plan`.supervisor_id
			and e.user_id = '{user}'
   			and `tabPrepare Audit Plan`.audit_engagement_letter = a.name)
	)""".format(user=user)
			