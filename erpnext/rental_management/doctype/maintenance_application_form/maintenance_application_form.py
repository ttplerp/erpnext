# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import datetime
import frappe
import re
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc

from frappe import _
from frappe.utils.data import get_datetime, now_datetime

class MaintenanceApplicationForm(Document):
	def get_query(self, doctype, txt, searchfield, start, page_len, filters):
		if searchfield == "linked_field":
			return frappe.db.sql("""
				SELECT name, other_field
				FROM `tabLinkedDocType`
				WHERE other_field LIKE %(txt)s
				ORDER BY other_field ASC
				LIMIT %(start)s, %(page_len)s
			""", {
				"txt": "%%%s%%" % txt,
				"start": start,
				"page_len": page_len
			})
	
		
	def validate(self):
		self.get_branch_missing()
		if self.maf_status =="On Hold":
			pass
		elif self.workflow_state == "Waiting Supervisor Approval":
			self.maf_status ="In Process"
		
		pattern = r'^[\w\.-]+@[a-zA-Z\d\.-]+\.[a-zA-Z]{2,}$'

		
		if self.email and not re.match(pattern, self.email):
			frappe.throw("Email Format is not right") 
	
	
	
	def get_branch_missing(self):
		if self.tenant_id and frappe.db.get_value("Tenant Information", self.tenant_id, "branch"):
			self.db_set("branch", frappe.db.get_value("Tenant Information", self.tenant_id, "branch"))

@frappe.whitelist()
def make_technical_sanction(source_name, target_doc=None):
	doclist = get_mapped_doc("Maintenance Application Form", source_name, {
		"Maintenance Application Form": {
			"doctype": "Technical Sanction",
			"field_map": {
				"parent": "name",
			},
			"validation": {
				#    "docstatus": ["=", 1]
			}
		},
	}, target_doc)

	return doclist


# @frappe.whitelist()
# def send_typed_input(typed_input):
#     # Perform necessary actions with the typed_input
#     # For example:
#     frappe.msgprint(typed_input)  # To print the input as a message in Frappe

#     # Return a message or data
#     return 'success'
import frappe
import json
from frappe import _

def after_save(doc,method):
		if doc.maf_status =="Completed":
			
			modified_date_time = get_datetime(doc.modified)
			current_time = now_datetime()
			time_difference = current_time - modified_date_time
			if time_difference.total_seconds() < 2:
				# frappe.msgprint("HIOOOOO")
				message  = f"The Maintenance for the Maintenance Application {doc.name}  has been successfully completed. "
				recipients = doc.email
				subject = "Maintenance Completion Notification"
				
				try:
					frappe.sendmail(
					recipients=recipients,
					subject=_(subject),
					message= _(message)
					
				)
				except:
					pass

def notify_after_submitting(doc,method):
	creation_time  = get_datetime(doc.creation )
	current_time = now_datetime()
	time_difference = current_time - creation_time
	if time_difference.total_seconds() < 2:
				message  = f"The Maintenance Application {doc.name}  has been successfully received. "
				recipients = doc.email
				subject = "Maintenance Application Received Notification"
				
				try:
					frappe.sendmail(
						recipients=recipients,
								subject=_(subject),
								message= _(message)
								
							)
				except:
						pass
	

@frappe.whitelist(allow_guest=True)
def get_cid_detail(tenant_cid):
	try:
		# Execute SQL query
		sql_query = """
		SELECT name, tenant_name, block_no, flat_no, location_name,dzongkhag,locations,phone_no, name,tenant_cid
		FROM `tabTenant Information` 
		WHERE tenant_cid = %(tenant_cid)s
		"""
		# Parameters to pass to the query
		query_params = {"tenant_cid": tenant_cid}

		data = frappe.db.sql(sql_query, query_params, as_dict=True)
		
	   
		

		# Return the data as JSON to the client side
		return data
	except Exception as e:
		frappe.log_error(_("Error in get_tenant_name: {0}").format(e))
		return None

@frappe.whitelist(allow_guest=True)
def checkCidExistence(tenant_cid):
	
	try:
		# Execute SQL query
		sql_query = """
		SELECT name, maf_status
		FROM `tabMaintenance Application Form` 
		WHERE cidd = %(tenant_cid)s
		ORDER BY creation DESC LIMIT 1
		
		"""

		# Parameters to pass to the query
		query_params = {"tenant_cid": tenant_cid}

		# Fetch data using frappe.db.sql
		data = frappe.db.sql(sql_query, query_params, as_dict=True)

		if data:
			first_record = data[0]  # Accessing the first record
			maf_status = first_record.get('maf_status')  # Retrieving the 'name' field
			# frappe.throw(record_name)
		
		# Check if data exists
		if data and maf_status not in ['Closed', 'Completed']:
		   
			# CID exists, showing the existing CID and allowing the check
			frappe.msgprint(f"CID {tenant_cid} already applied and that application is not yet closed or completed.")
			return True
		else:
			# CID does not exist, preventing the check and showing a message
		   
			return False
		
		 # Check if data exists
		# if data and maf_status!='closed':
		#     # CID exists, showing the existing CID and allowing the check
		#     frappe.msgprint(f"CID {tenant_cid} already applied and its not closed yet. ")
		#     return True
		# else:
		#     # CID does not exist, preventing the check and showing a message
		   
		#     return False
	  

	except Exception as e:
		# Log any exceptions that occur during the execution of the query
		frappe.log_error(_("Error in check_cid_existence: {0}").format(e))
		return None

	


	   
 
	