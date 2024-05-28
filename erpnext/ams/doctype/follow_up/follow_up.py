# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
from wsgiref import validate
import frappe
from frappe import _
from frappe.utils import flt,nowdate
from frappe.model.mapper import get_mapped_doc
from frappe.model.document import Document
from erpnext.custom_utils import sendmail

class FollowUp(Document):		
	def on_submit(self):
		self.update_execute_audit_status()
		self.update_execute_checklist_item()
		self.notify_audit_and_auditee()
  
	def on_cancel(self):
		self.update_execute_audit_status(1)
		self.update_execute_checklist_item(1)
 
	def on_update_after_submit(self):
		self.on_update_checklist_item()
		self.notify_audit_and_auditee()

	def update_execute_audit_status(self, cancel=0):
		pap_doc = frappe.get_doc("Prepare Audit Plan", self.prepare_audit_plan_no)
		eu_doc = frappe.get_doc("Execute Audit", self.execute_audit_no)
		
		if not cancel:
			pap_doc.db_set("status",'Follow Up')
			eu_doc.db_set("status", 'Follow Up')
		else:
			initial_doc = frappe.get_doc("Audit Initial Report", {"execute_audit_no": self.execute_audit_no})
			if initial_doc.docstatus == 1:
				pap_doc.db_set("status", 'Initial Report')
				eu_doc.db_set("status", 'Initial Report')
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
  
	def on_update_checklist_item(self):
		ea = frappe.get_doc("Execute Audit", self.execute_audit_no)
		follow_up = frappe.get_doc("Follow Up", self.name)
  
		for eaci in ea.get("audit_checklist"):
			for cl in follow_up.get("audit_observations"):
				if cl.audit_area_checklist == eaci.audit_area_checklist and cl.observation_title == eaci.observation_title:
					if eaci.status == 'Follow Up':
						eaci.db_set("status",'Replied')
					if cl.status == "Reply":						
						cl.db_set("status",'Replied')

	def update_execute_checklist_item(self, cancel=0):
		ea = frappe.get_doc("Execute Audit", self.execute_audit_no)
		follow_up = frappe.get_doc("Follow Up", self.name)

		for eaci in ea.get("audit_checklist"):
			for cl in follow_up.get("audit_observations"):
				if cl.audit_area_checklist == eaci.audit_area_checklist and cl.observation_title == eaci.observation_title:		
					if not cancel:
						if eaci.status == 'Open' and cl.audit_remarks:
							eaci.db_set("status", 'Follow Up')
							cl.db_set("status", 'Reply')						
					else:
						eaci.db_set("status", 'Open')
						cl.db_set("status", 'Follow Up')
				
	def notify_audit_and_auditee(self):
		now_date = nowdate()
		query = """
			select 
				fuci.audit_area_checklist, fuci.observation_title, fuci.nature_of_irregularity, fuci.status, fuci.audit_remarks, fuci.auditee_remarks
			from `tabFollow Up` fu, `tabFollow Up Checklist Item` fuci where fu.name=fuci.parent and fu.name = '{}' and fu.docstatus=1
		""".format(self.name)
		data = frappe.db.sql(query, as_dict=True)

		if frappe.session.user == self.owner:
			subject = 'Audit Follow Up'
			msg = ''' 
					<p>Follow Up ID: {}</p>
					<table border=1 style='border-collapse: collapse;'>
						<tr>
							<th>Audit Area Checklist</th>
							<th>Observation Title</th>
							<th>Nature of Irregularity</th>
							<th>Status</th>
							<th>Audit Remarks</th>
							<th>Auditee Remarks</th>
						</tr>
					'''.format(self.name)
			for d in data:
				msg += '''
					<tr>
						<td>{}</td>
						<td>{}</td>
						<td>{}</td>
						<td>{}</td>
						<td>{}</td>
						<td>{}</td>
						</tr>
					'''.format(d.audit_area_checklist, d.observation_title , d.nature_of_irregularity, d.status, d.audit_remarks , d.auditee_remarks) 
			msg += '</table>'
			recipent = self.supervisor_email
			
			if data:
				sendmail(recipent,subject,msg)

		elif frappe.session.user == self.supervisor_email:
			subject = 'Audit Follow Up Reply'
			msg = ''' 
					<p>Follow Up ID: {}</p>
					<table border=1 style='border-collapse: collapse;'>
						<tr>
							<th>Audit Area Checklist</th>
							<th>Observation Title</th>
							<th>Nature of Irregularity</th>
							<th>Status</th>
							<th>Audit Remarks</th>
							<th>Auditee Remarks</th>
						</tr>
					'''.format(self.name)
			for d in data:
				msg += '''
					<tr>
						<td>{}</td>
						<td>{}</td>
						<td>{}</td>
						<td>{}</td>
						<td>{}</td>
						<td>{}</td>
						</tr>
					'''.format(d.audit_area_checklist, d.observation_title , d.nature_of_irregularity, d.status, d.audit_remarks , d.auditee_remarks) 
			msg += '</table>'
			recipent = self.owner
			
			if data:
				sendmail(recipent,subject,msg)

	def get_observations(self):
		data = frappe.db.sql("""
			SELECT 
				eaci.audit_area_checklist, eaci.observation_title, eaci.nature_of_irregularity, 'Follow Up' status
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
			ORDER BY eaci.idx
		""".format(self.execute_audit_no), as_dict=True)

		if not data:
			frappe.throw(_('There are no Audit Observation defined for Execute Audit No. <b>{}</b>'.format(self.execute_audit_no)))

		self.set('audit_observations', [])
		for d in data:
			row = self.append('audit_observations',{})
			row.update(d)


	def get_direct_accountability(self):
		old_doc = frappe.get_doc("Execute Audit", self.execute_audit_no)
		self.set('direct_accountability', [])
		for a in old_doc.get("audit_checklist"):
			for b in old_doc.get("direct_accountability"):
				if a.audit_area_checklist == b.checklist and a.observation_title == b.observation_title:
					if a.status != "Closed":
						row = self.append('direct_accountability',{})
						row.checklist  = b.checklist
						row.observation_title  = b.observation_title
						row.observation  = b.observation
						row.employee  = b.employee
						row.employee_name  = b.employee_name
						row.designation  = b.designation

@frappe.whitelist()
def create_close_follow_up(source_name, target_doc=None):
	doclist = get_mapped_doc("Follow Up", source_name, {
		"Follow Up": {
			"doctype": "Close Follow Up",
			"field_map": {
				"follow_up_no": "name",
			}
		},
	}, target_doc)

	return doclist

def get_permission_query_conditions(user):
	if not user:
		user = frappe.session.user
	user_roles = frappe.get_roles(user)

	if user == "Administrator" or "System Manager" in user_roles or "Auditor" in user_roles:
		return

	return """(
		exists(select 1
			from `tabEmployee` as e
			where e.employee = `tabFollow Up`.supervisor_id
			and e.user_id = '{user}')
		or
		exists(select 1
			from `tabEmployee` as e, `tabFollow Up DA Item` as f
			where f.parent = `tabFollow Up`.name
   			and e.employee = f.employee
			and e.user_id = '{user}')
	)""".format(user=user)

