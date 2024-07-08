# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

class TraineeAddition(Document):
	def validate(self):
		self.old_state = self.get_db_value("workflow_state")
		self.new_state = self.workflow_state
		self.validate_tm()
		self.notify_pmt_lo(self.old_state, self.new_state)

	def validate_tm(self):
		doc = frappe.get_doc("Training Management",self.training_management)
		if doc.status not in ["Approved", "On Going"] and doc.docstatus != 0:
			frappe.throw("Training Management {} should be {} or {} and the document should not be submitted or cancelled")

	def on_submit(self):
		doc = frappe.get_doc("Training Management",self.training_management)
		for i in self.get("item"):
			doc.append("trainee_details", {
								"desuup_id": i.did,
								"desuup_cid": i.cid,
								"desuup_name": i.desuup_name,
								"mobile": i.mobile_no
			})
		doc.save()
	
	def notify_pmt_lo(self, old_state, new_state):
		receipients = []
		args = self.as_dict()
		emails = []
		if self.new_state == "Waiting For Verifier" and self.old_state == "Draft":
			emails = frappe.db.sql(""" select email from `tabProgramme Management Team` 
							where parent='{}' """.format(self.programme_classification), as_dict=1)
		if self.new_state == "Approved" and self.old_state != "Approved":
			emails = frappe.db.sql(""" select email from `tabLaison Officer` 
							where parent='{}' """.format(self.training_center), as_dict=1)
		
		if self.new_state=="Waiting Approval" and self.old_state != "Waiting Approval":
			emails = frappe.db.sql("""select parent as email from `tabHas Role` 
								where role="Data Manager" and parenttype="User";
							""", as_dict=1)

		if emails:
			receipients = [a['email'] for a in emails]

		if receipients:
			email_template = frappe.get_doc("Email Template", "Add Trainees")
			message = frappe.render_template(email_template.response, args)
			self.notify({
				# for post in messages
				"message": message,
				"message_to": receipients,
				# for email
				"subject": email_template.subject
			})

	def notify(self, args):
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
			frappe.msgprint(_("Email sent to {0}").format(contact))
		except frappe.OutgoingEmailError:
			pass

def get_permission_query_conditions(user):
	if not user: user = frappe.session.user
	user_roles = frappe.get_roles(user)
	if "Training User" in user_roles or "Training Manager" in user_roles or "System Manager" in user_roles or "Data Manager" in user_roles:
		return
	elif "Laison Officer User" in user_roles:
		return """(
			exists(select 1
				from `tabTraining Center` as t, `tabLaison Officer` as l
				where t.name = l.parent 
				and t.name = `tabTrainee Addition`.training_center
				and l.user = '{user}')
		)""".format(user=user)
	elif "PMT" in user_roles:
		return """)()
			exists(select 1
				from `tabProgramme Classification` as p, `tabProgramme Management Team` as t
				where p.name=t.parent
				and p.name = `tabTrainee Addition`.programme_classification
				and t.user = '{user}')
		)""".format(user=user)

def has_record_permission(doc, user):
	if not user: user = frappe.session.user
	user_roles = frappe.get_roles(user)

	if "Training User" in user_roles or "Training Manager" in user_roles or "System Manager" in user_roles or "Data Manager" in user_roles:
		return True
	else:
		if frappe.db.exists("Laison Officer", {"parent":doc.training_center, "user": user}):
			return True
		elif frappe.db.exists("Programme Management Team", {"parent":doc.programme_classification, "user": user}):
			return True
		else:
			return False 

