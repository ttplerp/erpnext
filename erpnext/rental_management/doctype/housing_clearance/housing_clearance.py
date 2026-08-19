# # Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# # For license information, please see license.txt

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
		if self.applicant_type=="Bhutanese":
			# frappe.throw(self.applicant_type)
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
						
			else :
				frappe.throw("Invalid Length of Cid")
		else:
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
# # Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# # For license information, please see license.txt

# import importlib
# import frappe

# from datetime import date
# from frappe.utils import nowdate, date_diff
# from frappe.model.document import Document
# from frappe.utils import add_to_date, get_last_day, flt, getdate, cint, nowdate
# from frappe import _
# from frappe.model.mapper import get_mapped_doc


# class HousingClearance(Document):

# 	def validate(self):
# 		# ==========================================================
# 		# NEW:
# 		# Check that the Applicant Name belongs to the entered CID.
# 		# This runs before the existing Housing Clearance validations.
# 		# ==========================================================
# 		self.validate_cid_and_application_name()

# 		# EXISTING CODE
# 		self.check_id_exist()

# 		if not self.is_tenant:
# 			self.application_approval_date = nowdate()

# 		if self.docstatus == 1:
# 			self.notify()


# 	# ==============================================================
# 	# NEW FUNCTION 1:
# 	# Validate CID and Applicant Name
# 	# ==============================================================
# 	def validate_cid_and_application_name(self):
# 		"""
# 		Check whether the entered Applicant Name belongs to the CID.

# 		This validation is applied only to Bhutanese applicants.
# 		"""

# 		if self.applicant_type != "Bhutanese":
# 			return

# 		if not self.cid:
# 			frappe.throw(
# 				_("Citizen ID No is required.")
# 			)

# 		cid = str(self.cid).strip()

# 		# Save the CID without accidental spaces.
# 		self.cid = cid

# 		if not cid.isdigit():
# 			frappe.throw(
# 				_("Citizen ID No must contain numbers only."),
# 				title=_("Invalid CID")
# 			)

# 		if len(cid) != 11:
# 			frappe.throw(
# 				_("Citizen ID No must contain exactly 11 digits."),
# 				title=_("Invalid CID")
# 			)

# 		# Get the correct applicant name from an authoritative source.
# 		official_name = self.get_official_name_from_cid(cid)

# 		if not official_name:
# 			frappe.throw(
# 				_(
# 					"Unable to verify the Applicant Name for CID {0}.<br><br>"
# 					"No matching citizen name was found from the CID service "
# 					"or Tenant Information."
# 				).format(
# 					frappe.bold(cid)
# 				),
# 				title=_("Applicant Name Verification Failed")
# 			)

# 		entered_name = str(self.application_name or "").strip()

# 		# If Applicant Name is blank, automatically insert the official name.
# 		if not entered_name:
# 			self.application_name = official_name
# 			return

# 		# Compare entered name and official name.
# 		if self.normalize_person_name(entered_name) != self.normalize_person_name(
# 			official_name
# 		):
# 			previous_name = entered_name

# 			# Automatically correct the Applicant Name.
# 			self.application_name = official_name

# 			frappe.msgprint(
# 				_(
# 					"The Applicant Name did not match the entered CID "
# 					"and has been corrected.<br><br>"
# 					"<b>Citizen ID No:</b> {0}<br>"
# 					"<b>Previous Applicant Name:</b> {1}<br>"
# 					"<b>Correct Applicant Name:</b> {2}"
# 				).format(
# 					frappe.escape_html(cid),
# 					frappe.escape_html(previous_name),
# 					frappe.escape_html(official_name)
# 				),
# 				title=_("CID and Name Mismatch"),
# 				indicator="orange"
# 			)

# 		else:
# 			# Use the official spelling and capitalization.
# 			self.application_name = official_name


# 	# ==============================================================
# 	# NEW FUNCTION 2:
# 	# Try all available sources for the official applicant name
# 	# ==============================================================
# 	def get_official_name_from_cid(self, cid):
# 		"""
# 		First try the CID API if it exists.

# 		If the CID API is unavailable, try the latest matching
# 		Tenant Information record.
# 		"""

# 		official_name = self.get_name_from_existing_cid_api(cid)

# 		if official_name:
# 			return official_name

# 		official_name = self.get_name_from_tenant_information(cid)

# 		if official_name:
# 			return official_name

# 		return None


# 	# ==============================================================
# 	# NEW FUNCTION 3:
# 	# Use get_cid_detail only when that function actually exists
# 	# ==============================================================
# 	def get_name_from_existing_cid_api(self, cid):
# 		"""
# 		Dynamically check whether get_cid_detail exists.

# 		This avoids an import error when get_cid_detail is not available.
# 		"""

# 		try:
# 			api_module = importlib.import_module(
# 				"erpnext.rental_management.doctype.api_setting.api_setting"
# 			)

# 		except Exception:
# 			return None

# 		get_cid_detail = getattr(
# 			api_module,
# 			"get_cid_detail",
# 			None
# 		)

# 		if not callable(get_cid_detail):
# 			return None

# 		try:
# 			# First try passing CID normally.
# 			response = get_cid_detail(cid)

# 		except TypeError:
# 			try:
# 				# Some functions may require CID as a keyword argument.
# 				response = get_cid_detail(cid=cid)

# 			except Exception:
# 				frappe.log_error(
# 					frappe.get_traceback(),
# 					"Housing Clearance CID API Error"
# 				)
# 				return None

# 		except Exception:
# 			frappe.log_error(
# 				frappe.get_traceback(),
# 				"Housing Clearance CID API Error"
# 			)
# 			return None

# 		return self.get_name_from_cid_response(response)


# 	# ==============================================================
# 	# NEW FUNCTION 4:
# 	# Get the name from Tenant Information
# 	# ==============================================================
# 	def get_name_from_tenant_information(self, cid):
# 		"""
# 		Find the latest Tenant Information record matching the CID
# 		and retrieve the tenant's name.
# 		"""

# 		tenant_information = frappe.db.get_value(
# 			"Tenant Information",
# 			{
# 				"tenant_cid": cid
# 			},
# 			[
# 				"name"
# 			],
# 			order_by="allocated_date desc",
# 			as_dict=True
# 		)

# 		if not tenant_information:
# 			return None

# 		tenant_id = tenant_information.name

# 		# Possible fieldnames that may contain the person's name.
# 		possible_name_fields = [
# 			"tenant_name",
# 			"full_name",
# 			"name_of_tenant",
# 			"applicant_name",
# 			"application_name",
# 			"citizen_name"
# 		]

# 		meta = frappe.get_meta("Tenant Information")

# 		for fieldname in possible_name_fields:
# 			if meta.has_field(fieldname):
# 				tenant_name = frappe.db.get_value(
# 					"Tenant Information",
# 					tenant_id,
# 					fieldname
# 				)

# 				if tenant_name:
# 					return str(tenant_name).strip()

# 		return None


# 	# ==============================================================
# 	# NEW FUNCTION 5:
# 	# Read different possible API response formats
# 	# ==============================================================
# 	def get_name_from_cid_response(self, response):
# 		"""
# 		Extract the citizen name from different possible API responses.
# 		"""

# 		if not response:
# 			return None

# 		# Some APIs return a requests.Response object.
# 		if hasattr(response, "json") and callable(response.json):
# 			try:
# 				response = response.json()
# 			except Exception:
# 				pass

# 		# Some APIs return JSON as text.
# 		if isinstance(response, str):
# 			try:
# 				response = frappe.parse_json(response)
# 			except Exception:
# 				return None

# 		# Some APIs return a list.
# 		if isinstance(response, (list, tuple)):
# 			for item in response:
# 				official_name = self.get_name_from_cid_response(item)

# 				if official_name:
# 					return official_name

# 			return None

# 		# Most APIs return a dictionary.
# 		if isinstance(response, dict):
# 			possible_name_fields = [
# 				"full_name",
# 				"fullName",
# 				"citizen_name",
# 				"citizenName",
# 				"applicant_name",
# 				"application_name",
# 				"name"
# 			]

# 			for fieldname in possible_name_fields:
# 				value = response.get(fieldname)

# 				if value and isinstance(value, str):
# 					return value.strip()

# 			# Check if the name is returned in separate parts.
# 			first_name = (
# 				response.get("first_name")
# 				or response.get("firstName")
# 				or ""
# 			)

# 			middle_name = (
# 				response.get("middle_name")
# 				or response.get("middleName")
# 				or ""
# 			)

# 			last_name = (
# 				response.get("last_name")
# 				or response.get("lastName")
# 				or ""
# 			)

# 			full_name = " ".join(
# 				name_part.strip()
# 				for name_part in [
# 					str(first_name),
# 					str(middle_name),
# 					str(last_name)
# 				]
# 				if name_part and str(name_part).strip()
# 			)

# 			if full_name:
# 				return full_name

# 			# Check whether the citizen information is nested.
# 			nested_fields = [
# 				"data",
# 				"result",
# 				"message",
# 				"response",
# 				"citizen",
# 				"citizen_detail",
# 				"citizen_details",
# 				"citizenDetail",
# 				"citizenDetails"
# 			]

# 			for fieldname in nested_fields:
# 				if fieldname in response:
# 					official_name = self.get_name_from_cid_response(
# 						response.get(fieldname)
# 					)

# 					if official_name:
# 						return official_name

# 		return None


# 	# ==============================================================
# 	# NEW FUNCTION 6:
# 	# Normalize names before comparing
# 	# ==============================================================
# 	def normalize_person_name(self, value):
# 		"""
# 		Treat capitalization and extra spaces as the same.

# 		Example:
# 		'Dil  Bahadur Mongar'
# 		and
# 		'dil bahadur mongar'

# 		will match.
# 		"""

# 		return " ".join(
# 			str(value or "").strip().lower().split()
# 		)


# 	# ==============================================================
# 	# EXISTING CODE BELOW
# 	# ==============================================================

# 	def check_id_exist(self):
# 		for a in frappe.db.sql("""
# 					 		select name, application_status, application_date, docstatus
# 					 		from `tabHousing Clearance`
# 					 		where name!='{}'
# 					 		and cid='{}'
# 						   and docstatus != 2
# 						 """.format(self.name, self.cid), as_dict=True):

# 			if a.application_status == "Pending":
# 				frappe.throw(
# 					"Your Housing Clearance Application <b>{}</b> is still Pending".format(
# 						a.name
# 					)
# 				)

# 			if a.application_status == "Approved" and a.docstatus == 1:
# 				if self.get_numbers_of_day(a.application_date) < 90:
# 					frappe.throw(
# 						"Your Housing Clearance Application <b>{}</b> is Not Expired".format(
# 							a.name
# 						)
# 					)

# 		self.update_detail()


# 	def get_numbers_of_day(self, application_date):
# 		# Return the number of days.
# 		current_date = nowdate()
# 		num_day = date_diff(current_date, application_date)

# 		# frappe.errprint(num_day)

# 		return num_day


# 	def update_detail(self):
# 		# Updates the clearance details.

# 		if self.applicant_type == "Bhutanese":

# 			# frappe.throw(self.applicant_type)

# 			if len(str(self.cid)) == 11:
# 				if self.cid:
# 					if frappe.db.exists(
# 						"Tenant Information",
# 						{
# 							"tenant_cid": self.cid
# 						}
# 					):
# 						tenant_id = frappe.db.sql("""
# 							select name
# 							from `tabTenant Information`
# 							where tenant_cid='{}'
# 							order by allocated_date desc
# 							limit 1
# 						""".format(self.cid))[0][0]

# 						self.is_tenant = 1
# 						self.tenant = tenant_id

# 					else:
# 						self.application_status = "Approved"
# 						self.is_tenant = 0
# 						self.docstatus = 1

# 			else:
# 				frappe.throw("Invalid Length of Cid")

# 		else:
# 			if self.cid:
# 				if frappe.db.exists(
# 					"Tenant Information",
# 					{
# 						"tenant_cid": self.cid
# 					}
# 				):
# 					tenant_id = frappe.db.sql("""
# 						select name
# 						from `tabTenant Information`
# 						where tenant_cid='{}'
# 						order by allocated_date desc
# 						limit 1
# 					""".format(self.cid))[0][0]

# 					self.is_tenant = 1
# 					self.tenant = tenant_id

# 				else:
# 					self.application_status = "Approved"
# 					self.is_tenant = 0
# 					self.docstatus = 1


# 	def on_submit(self):

# 		if self.application_status == "Pending":
# 			frappe.throw(
# 				"Not allow to submit the application with <b>Pending</b> Status"
# 			)

# 		'''
# 		if self.tenant_status and self.tenant_status != "Surrendered" and self.application_status == "Approved":
# 			frappe.throw("Not allow to Approve the application as the Tenant Status is not <b>Surrendered</b>")
# 		'''

# 		self.application_approval_date = nowdate()
# 		self.notify()


# 	def get_args(self):
# 		parent_doc = frappe.get_doc(
# 			self.doctype,
# 			self.name
# 		)

# 		args = parent_doc.as_dict()

# 		return args


# 	def notify(self):
# 		# args = self.get_args()

# 		# template = frappe.db.get_single_value(
# 		# 	'HR Settings',
# 		# 	'housing_clearance_approver_notification'
# 		# )

# 		# if not template:
# 		# 	frappe.msgprint(
# 		# 		_(
# 		# 			"Please set default template for Housing Clearance "
# 		# 			"Approver Notification in HR Settings."
# 		# 		)
# 		# 	)
# 		# 	return

# 		# email_template = frappe.get_doc(
# 		# 	"Email Template",
# 		# 	template
# 		# )

# 		# message = frappe.render_template(
# 		# 	email_template.response,
# 		# 	args
# 		# )

# 		message = (
# 			f"The Housing Clearance Application {self.name} "
# 			f"is approved. Please check Your Attachment."
# 		)

# 		# frappe.msgprint(str(message))

# 		recipients = self.email

# 		# subject = email_template.subject

# 		subject = "Housing Clearance Approver Notification"

# 		self.send_mail(
# 			recipients,
# 			message,
# 			subject
# 		)


# 	def send_mail(self, recipients, message, subject):
# 		attachments = self.get_attachment()

# 		try:
# 			frappe.sendmail(
# 				recipients=recipients,
# 				subject=_(subject),
# 				message=_(message),
# 				attachments=attachments
# 			)

# 		except Exception:
# 			pass


# 	def get_attachment(self):
# 		"""Check print settings and attach the PDF."""

# 		print_settings = frappe.get_doc(
# 			"Print Settings",
# 			"Print Settings"
# 		)

# 		return [
# 			{
# 				"print_format_attachment": 1,
# 				"doctype": self.doctype,
# 				"name": self.name,
# 				"print_format": "Housing Clearance Certificate",
# 				"print_letterhead": print_settings.with_letterhead,
# 				"lang": "en"
# 			}
# 		]