# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from datetime import date
from frappe.utils import nowdate,date_diff
from frappe.model.document import Document
from frappe.utils import add_to_date, get_last_day, flt, getdate, cint,nowdate
from frappe import _
from frappe.model.mapper import get_mapped_doc
from erpnext.rental_management.doctype.api_setting.api_setting import get_cid_detail, get_civil_servant_detail
class HousingClearance(Document):
	def validate(self):
		self.check_id_exist()
		if not self.is_tenant:
			self.application_approval_date = nowdate()
		if self.docstatus == 1:
			self.notify()

	def check_id_exist(self):
		for a in frappe.db.sql("""
					 		select name, application_status, application_date, docstatus
					 		from `tabHousing Clearance`
					 		where name!='{}'
					 		and cid='{}'
						   and docstatus != 2
						 """.format(self.name, self.cid), as_dict=True):
			if a.application_status == "Pending":
				frappe.throw("Your Housing Clearance Application <b>{}</b> is still Pending".format(a.name))

			if a.application_status == "Approved" and a.docstatus==1:
				if self.get_numbers_of_day(a.application_date) < 90:
					frappe.throw("Your Housing Clearance Application <b>{}</b> is Not Expired".format(a.name))
		
		self.update_detail()
		
  
	def get_numbers_of_day(self, application_date): # return the number of days 
		current_date = nowdate()
		num_day = date_diff(current_date, application_date)
		# frappe.errprint(num_day)
		return num_day

	def update_detail(self): # updates the  clearance details
		if len(str(self.cid)) == 11:
			if self.cid:
				if frappe.db.exists("Tenant Information", {"tenant_cid":self.cid}):
					tenant_id = frappe.db.sql("""select name 
												from `tabTenant Information`
												where tenant_cid='{}'
												order by allocated_date desc
												limit 1
											""".format(self.cid))[0][0]
					self.is_tenant = 1
					self.tenant = tenant_id
				else:
					self.application_status = "Approved"
					self.is_tenant = 0
					self.docstatus = 1
					
		else:
			frappe.throw("Invalid Length of Cid")
	def on_submit(self):
		
		if self.application_status == "Pending":
			frappe.throw("Not allow to submit the application with <b>Pending</b> Status")
		'''
		if self.tenant_status and self.tenant_status != "Surrendered" and self.application_status == "Approved":
			frappe.throw("Not allow to Approve the application as the Tenant Status is not <b>Surrendered</b>")
		'''
	
		self.application_approval_date = nowdate()
		self.notify()
  
	def get_args(self):
		parent_doc = frappe.get_doc(self.doctype, self.name)
		args = parent_doc.as_dict()
		return args

	def notify(self):
		# args = self.get_args()
		# template = frappe.db.get_single_value('HR Settings', 'housing_clearance_approver_notification')
		# if not template:
		# 	frappe.msgprint(_("Please set default template for Housing Clearance Approver Notification in HR Settings."))
		# 	return
		# email_template = frappe.get_doc("Email Template", template)
		# message = frappe.render_template(email_template.response, args)
		message  = f"The Housing Clearance Application {self.name}  is approved. Please check Your Attachment."
		# frappe.msgprint(str(message))
		recipients = self.email
		# subject = email_template.subject
		subject = "Housing Clearance Approver Notification"
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
	def get_attachment(self):
		"""check print settings are attach the pdf"""
		print_settings = frappe.get_doc("Print Settings", "Print Settings")
		return [
			{
				"print_format_attachment": 1,
				"doctype": self.doctype,
				"name": self.name,
				"print_format": "Housing Clearance Certificate",
				"print_letterhead": print_settings.with_letterhead,
				"lang": "en",
			}
		]
    