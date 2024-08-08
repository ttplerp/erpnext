# -*- coding: utf-8 -*-
# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.naming import make_autoname

class CourtTrackingSystem(Document):

	def on_submit(self):
		pass
		# self.notify_users()

	def autoname(self):
		type = ""
		if self.case_type == "NPL Recovery Cases":
			type = "CASE/RC/"
		elif self.case_type == "Counter Litigation":
			type = "CASE/CL/"
		elif self.case_type == "Criminal & ACC Cases":
			type = "CASE/CC/"
		self.name = make_autoname(str(type)+".YYYY./.#####")

	def notify_users(self):
		args = self.get_args()
		template = frappe.db.get_single_value('HR Settings', 'criminal_and_acc_cases')
		
		if self.case_type in ("Counter Litigation","NPL Recovery Cases"):
			template = frappe.db.get_single_value('HR Settings', 'npl_recovery_cases_and_counter_litigation_notification')
		
		if not template:
			frappe.msgprint(_("Please set default template for Court Tracking Templates in HR settings."))
			return

		email_template = frappe.get_doc("Email Template", template)
		message = frappe.render_template(email_template.response, args)
		#frappe.msgprint(str(message))
		recipients = self.owner
		subject = email_template.subject
		self.send_mail(recipients,message, subject)

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
	def get_args(self):
		parent_doc = frappe.get_doc(self.doctype, self.name)
		args = parent_doc.as_dict()
		return args
	
	def get_attachment(self):
		"""check print settings are attach the pdf"""
		print_settings = frappe.get_doc("Print Settings", "Print Settings")
		return [
			{
				"print_format_attachment": 1,
				"doctype": self.doctype,
				"name": self.name,
				"print_format": "Court Tracking System",
				"print_letterhead": print_settings.with_letterhead,
				"lang": "en",
			}
		]
	
	def before_update_after_submit(self):
		frappe.msgprint(str(self))
		# send email on change of status
@frappe.whitelist()
def get_loan_product(doctype, txt, searchfield, start, page_len, filters):
	query = """
		SELECT 
			loan_product
		FROM 
			`tabLoan Products`
		WHERE parent_product = '{0}' and is_sub_group = '0'
	""".format(filters.get('parent_product'))
	return frappe.db.sql(query)
