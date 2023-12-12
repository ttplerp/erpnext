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
	def check_id_exist(self):
     
		exist = frappe.db.exists("Housing Clearance",{"cid":self.cid})
		if exist:
			if self.get_numbers_of_day() <= 30: 
				frappe.msgprint("Sorry Your Clearance already exist and it is not expired")
			else:
				self.update_detail() # if number of days is greater than one month save a details
		else:
			self.update_detail() # if cid does not exist, update the details
		# frappe.errprint(exist)
  
	def get_numbers_of_day(self): # return the number of days 
		self.application_date
		current_date = nowdate()
		applications_date= frappe.db.get_value('Housing Clearance',{'cid':self.cid} , ['application_date'])
		num_day = date_diff(current_date,applications_date)
		frappe.errprint(num_day)
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

		if self.tenant_status and self.tenant_status != "Surrendered" and self.application_status == "Approved":
			frappe.throw("Not allow to Approve the application as the Tenant Status is not <b>Surrendered</b>")
	
		self.application_approval_date = nowdate()
     
    