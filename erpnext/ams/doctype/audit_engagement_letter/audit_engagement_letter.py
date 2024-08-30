# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from erpnext.custom_workflow import validate_workflow_states, notify_workflow_states
from frappe import _

class AuditEngagementLetter(Document):
	def validate(self):
		pass
		# validate_workflow_states(self)
		# notify_workflow_states(self)
   
	def on_submit(self):
		self.update_engagement_letter_no()
		self.notify_auditors()
  
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

	def get_auditors(self):
		receipients = []
		for member in self.audit_team:
			if member.auditor_email:
				receipients.append(member.auditor_email)
			else:
				frappe.throw("Please set Company Email for auditor {} in Employee Master".format(item.employee))
		return receipients

	def notify_auditors(self):
		parent_doc = frappe.get_doc(self.doctype, self.name)
		args = parent_doc.as_dict()
		receipients = []
		receipients = self.get_auditors()
		template = frappe.db.get_single_value('Audit Settings', 'audit_engagement_auditor_notification_template')
		if not template:
			frappe.msgprint(_("Please set default template for Audit Engagement Auditor Notification in Audit Settings."))
			return 
		email_template = frappe.get_doc("Email Template", template)
		message = frappe.render_template(email_template.response, args)
		msg = self.notify({
			# for post in messages
			"message": message,
			"message_to": receipients,
			# for email
			"subject": email_template.subject
		},1)
		# if msg != "Failed":
		# 	self.db_set("mail_sent",1)
		frappe.msgprint(msg)
	@frappe.whitelist()
	def notify_supervisor(self):
		parent_doc = frappe.get_doc(self.doctype, self.name)
		args = parent_doc.as_dict()
		supervisor_email = frappe.db.get_value("Employee", self.supervisor_id, "user_id")
		receipients = [supervisor_email]
		template = frappe.db.get_single_value('Audit Settings', 'audit_engagement_supervisor_notification_template')
		if not template:
			frappe.msgprint(_("Please set default template for Audit Engagement Supervisor Notification in Audit Settings."))
			return 
		email_template = frappe.get_doc("Email Template", template)
		message = frappe.render_template(email_template.response, args)
		msg = self.notify({
			# for post in messages
			"message": message,
			"message_to": receipients,
			# for email
			"subject": email_template.subject
		},1)
		# if msg != "Failed":
		# 	self.db_set("mail_sent",1)
		frappe.msgprint(msg)

	def notify(self, args, approver = 0):
		args = frappe._dict(args)
		# args -> message, message_to, subject
		contact = args.message_to
		if not isinstance(contact, list):
			if not args.notify == "employee":
				contact = frappe.get_doc('User', contact).email or contact

		sender      	    = dict()
		sender['email']     = frappe.get_doc('User', frappe.session.user).email
		sender['full_name'] = frappe.utils.get_fullname(sender['email'])

		try:
			frappe.sendmail(
				recipients = contact,
				sender = sender['email'],
				subject = args.subject,
				message = args.message,
			)
			if approver == 0:
				frappe.msgprint(_("Email sent to {0}").format(contact))
			else:
				return _("Email sent to {0}").format(contact)
		except frappe.OutgoingEmailError:
			pass

	# Get audit tean from Prepare Audit Plan
	@frappe.whitelist()
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
