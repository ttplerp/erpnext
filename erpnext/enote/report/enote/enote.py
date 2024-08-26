# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
from frappe.model.naming import make_autoname
from frappe.utils import nowdate

class eNote(Document):
	
	def on_submit(self):
		self.enote_format = make_autoname(str(self.enote_series)+".YYYY./.#####")
		frappe.db.set_value("eNote", self.name, "enote_format", self.enote_format)
		self.send_notification()
		# notify_workflow_states(self)
  
	def validate(self):	
		action = frappe.request.form.get('action')
		if action and action not in ("Save","Apply") and self.reviewer_required:
			status = 1
			for i in self.reviewers: 
				if i.status != "Reviewed": 
					status = 0
					break
			if status == 0:
				frappe.throw(str('Review Not Completed'))
			
		self.save_forward_to()
		self.workflow_action()
		# if we allow on action approve, it going double email to doc owner. 
		# one form here and another from on_submit().
		# if we allow from here, workflow state is still stays in pending which is wrong.  
		# again while reloading the doc, after saving remarks has impact as well. it should run
		# only in below action.
		if frappe.request.form.get('action') in ("Forward","Apply","Reject"):
			self.send_notification()
			# notify_workflow_states(self)   


	def save_forward_to(self):
		if not self.forward_to:
			if frappe.db.exists("Employee", {"user_id":frappe.session.user}):
				doc = frappe.get_doc("Employee", {"user_id":frappe.session.user})
				if doc.reports_to:
					self.forward_to = frappe.db.get_value("Employee", doc.reports_to, "user_id")
		
		self.forward_to = frappe.session.user if not self.forward_to else self.forward_to
	def before_update_after_submit(self):
		self.notify_copy_to()

	def workflow_action(self):  
		# Get the action of the button
		action = frappe.request.form.get('action')   
		#Allow only the permitted user to make changes
		self.permitted_user = frappe.session.user if not self.permitted_user else self.permitted_user

		if self.get_db_value("workflow_state") != "Waiting For Reviewer":
			if self.permitted_user != frappe.session.user:
				frappe.throw(" Only <b>{}</b> is allowed to make changes and perform actions to this Note".format(self.permitted_user))
		
		message = None
		if action in ("Forward","Apply"):
			if not self.forward_to:
				frappe.throw("<b>Forward To</b> value is missing. Please select a user to Forward")
			#check if forward_to field is valid
			if self.forward_to == frappe.session.user:
				frappe.throw(_("You are not allowed to <b>Forward To</b> yourself. Change the <b>Forward To</b> Field value."))
			#Save the action in remark child table
			self.upsert_remark(action)

			message = "eNote Document Successfully Forwarded to {}".format(self.forward_to)
			#Update the permitted User with next forwarded user 
			self.permitted_user = self.forward_to
		
		if action in ("Approve","Reject"):
			if action == "Reject":
				#check if forward_to field is valid
				if self.forward_to == frappe.session.user or not self.forward_to:
					self.forward_to = self.owner
				
				#Update the permitted User with next forwarded user 
				self.permitted_user = self.forward_to

				check_remark = frappe.db.sql("""
					select name 
					from `tabNote Remark`
					where parent='{}'
					and user='{}'
					and (action is NULL or action="")
				""".format(self.name, frappe.session.user), as_dict=True)
			
				if not check_remark:
					frappe.throw("Please write a remarks to <b>{}</b> the document".format(action))
			# to record the approve action witout remarks
			# if action == "Approve":
			self.upsert_remark(action)

			message = "eNote Document {}".format("Approved" if action == "Approve" else "Rejected")
		
		#Send email notification and print message 
		if message:
			frappe.msgprint("{}".format(message))	
			
	def get_args(self):
		parent_doc = frappe.get_doc(self.doctype, self.name)
		args = parent_doc.as_dict()
		return args

	def send_notification(self):
		action = frappe.request.form.get('action')  
		if self.workflow_state == "Draft" or action == "Save":
			return
		elif self.workflow_state in ("Approved", "Rejected", "Cancelled"):
			self.notify_employee()

		elif self.workflow_state == "Pending" and frappe.session.user != self.forward_to:
			self.notify_approval()

		elif self.workflow_state == "Waiting For Reviewer":
			self.notify_reviewer()

	def notify_reviewer(self):
		self.doc = self
		parent_doc = frappe.get_doc(self.doc.doctype, self.doc.name)
		args = parent_doc.as_dict()
		args.update({
			"workflow_state": self.doc.workflow_state
		})
		template = frappe.db.get_single_value('HR Settings', 'enote_reviewer_notification')
		if not template:
			frappe.msgprint(_("Please set default template for eNote Reviewer Notification in HR Settings."))
			return

		email_template = frappe.get_doc("Email Template", template)
		message = frappe.render_template(email_template.response, args)
		recipients = self.doc.owner
		subject = email_template.subject
		self.send_mail(recipients,message, subject)

	def notify_employee(self):
		self.doc = self
		parent_doc = frappe.get_doc(self.doc.doctype, self.doc.name)
		args = parent_doc.as_dict()
		args.update({
			"workflow_state": self.doc.workflow_state
		})
		template = frappe.db.get_single_value('HR Settings', 'enote_status_notification')
		if not template:
			frappe.msgprint(_("Please set default template for eNote Status Notification in HR Settings."))
			return

		email_template = frappe.get_doc("Email Template", template)
		message = frappe.render_template(email_template.response, args)
		recipients = self.doc.owner
		subject = email_template.subject
		self.send_mail(recipients,message, subject)

	def notify_copy_to(self):
		parent_doc = frappe.get_doc(self.doctype, self.name)
		args = parent_doc.as_dict()
		if len(self.copied) > 0:
			template = frappe.db.get_single_value('HR Settings', 'enote_copyto_notification')
			if not template:
				frappe.msgprint(_("Please set default template for eNote Copy To in HR Settings."))
				return
			email_template = frappe.get_doc("Email Template", template)
			message = frappe.render_template(email_template.response, args)
			subject = email_template.subject   
			for copy in self.copied:
				recipients = copy.user_id
				self.send_mail(recipients,message,subject)

	def notify_approval(self):
		args = self.get_args()
		template = frappe.db.get_single_value('HR Settings', 'enote_approval_notification')
		if not template:
			frappe.msgprint(_("Please set default template for eNote Approval Notification in HR Settings."))
			return

		email_template = frappe.get_doc("Email Template", template)
		message = frappe.render_template(email_template.response, args)
		recipients = self.forward_to
		subject = email_template.subject
		self.send_mail(recipients,message, subject)
  
	def get_attachment(self):
		"""check print settings are attach the pdf"""
		print_settings = frappe.get_doc("Print Settings", "Print Settings")
		return [
			{
				"print_format_attachment": 1,
				"doctype": self.doctype,
				"name": self.name,
				"print_format": "eNote",
				"print_letterhead": print_settings.with_letterhead,
				"lang": "en",
			}
		]
	
	def upsert_remark(self, action):
		if frappe.db.exists("Employee", {"user_id":frappe.session.user}):
			doc = frappe.get_doc("Employee", {"user_id":frappe.session.user})
			employee = doc.name
			employee_name = doc.employee_name
			designation = doc.designation
		else:
			employee = None
			employee_name = frappe.session.full_name
			designation=None

		db_check = frappe.db.sql("""
			select name 
			from `tabNote Remark`
			where parent='{}'
			and user='{}'
			and (action is NULL or action="")
		""".format(self.name, frappe.session.user), as_dict=True)

		if not db_check:
			self.append("remark",{
				"employee":employee,
				"employee_name": employee_name,
				"user": frappe.session.user,
				"designation": designation,
				"action":action,
				"forward_to": self.forward_to,
				"content": self.content,
				"remark_date": nowdate(),
			})
		else:
			for a in self.get("remark"):
				if a.name == db_check[0].name:
					a.action = action
					a.forward_to = self.forward_to
					a.content = self.content

	@frappe.whitelist()
	def restore_content(self,child_id):
		doc = frappe.get_doc("eNote", self.name)
		doc.content = frappe.db.get_value("Note Remark", child_id, "content")
		doc.save()

	@frappe.whitelist()
	def update_status(self):
		doc = frappe.get_doc("eNote", self.name)
		query = "SELECT name from `tabeNote Reviewer` Where user_id == '{}'".format(frappe.session.user)
		sql = frappe.db.sql(query)

		doc = frappe.db.get_doc("eNote Reviewer", sql[0].name)
		doc.status = "Reviewed"
		doc.save()

	@frappe.whitelist()
	def save_remark(self, remark, reviewers=None):
		if frappe.db.exists("Employee", {"user_id":frappe.session.user}):
			doc = frappe.get_doc("Employee", {"user_id":frappe.session.user})
			employee = doc.name
			employee_name = doc.employee_name
			designation = doc.designation
		else:
			employee = None
			employee_name = frappe.session.full_name
			designation=None
		db_check = frappe.db.sql("""
			select name 
			from `tabNote Remark`
			where parent='{}'
			and user='{}'
			and (action is NULL or action="")
		""".format(self.name, frappe.session.user), as_dict=True)
		if not db_check:
			doc1 = frappe.get_doc("eNote", self.name)
			doc1.append("remark",{
				"employee":employee,
				"employee_name": employee_name,
				"user": frappe.session.user,
				"designation": designation,
				"remark": remark,
				"remark_date": nowdate(),
			})
			doc1.save()
		else:
			doc_name = frappe.get_doc("Note Remark", db_check[0].name)
			doc_name.remark = remark,
			doc_name.remark_date = nowdate()
			doc_name.save()

		if reviewers:
			frappe.db.set_value("Note Remark", {'user': frappe.session.user}, "action", "Review")
			frappe.db.set_value("eNote Reviewer", {'user_id': frappe.session.user}, "status", "Reviewed")
			query = """SELECT * FROM `tabeNote Reviewer` WHERE parent = '{0}'""".format(self.name)
			data = frappe.db.sql(query, as_dict=1)
			status = 1
			if data:
				for i in data:
					if i.status != "Reviewed":
						status = 0
						break
			if status == 1:
				# doc = frappe.get_doc('eNote', self.name) 
				# doc.workflow_state = "Pending"
				# doc.save()
				# frappe.db.commit()
				frappe.db.set_value("eNote", {'name': self.name}, "workflow_state", "Pending")

   
	def send_mail(self, recipients, message, subject):
		attachments = self.get_attachment()
		try:
			frappe.sendmail(
					recipients=recipients,
					subject=_(subject),
					message= _(message),
					attachments=attachments,
				)
		except:
			pass	

def get_permission_query_conditions(user):
    if not user: user = frappe.session.user
    user_roles = frappe.get_roles(user)

	# reviewers  = frappe.db.sql("SELECT user_id FROM `tabeNote Reviewer")

    if user == "Administrator":
        return
    if "HR User" in user_roles or "HR Manager" in user_roles:
        return
    return """(
        `tabeNote`.owner = '{user}' or
		IF (
				(`tabeNote`.reviewer_required = '1' and `tabeNote`.workflow_state != 'Waiting For Reviewer') or `tabeNote`.reviewer_required = '0',  
				`tabeNote`.permitted_user = '{user}',
				exists(select 1
					from `tabEmployee` e, `tabeNote Reviewer` nr
					where e.user_id = '{user}' and '{user}' = nr.user_id and nr.parent = `tabeNote`.name)
			)
		or
        exists(select 1
			from `tabEmployee` e, `tabNote Copy` nc
			where e.user_id = '{user}' and '{user}' = nc.user_id and nc.parent = `tabeNote`.name)
   		)
		""".format(user=user)
# `tabeNote`.permitted_user = '{user}' or
# or
# 		exists(select 1
# 			from `tabEmployee` e, `tabeNote Reviewer` nr
# 			where e.user_id = '{user}' and '{user}' = nr.user_id and nr.parent = `tabeNote`.name)
   
   
   
   
