# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class HousingApplicationDetailsUpdate(Document):
	pass

@frappe.whitelist(allow_guest=True)
def checkCidExistence(cid):
	try:
		# Execute SQL query
		sql_query = """
		SELECT name
		FROM `tabHousing Application` 
		WHERE cid = %(cid)s
		ORDER BY creation DESC LIMIT 1
		
		"""

		# Parameters to pass to the query
		query_params = {"cid": cid}

		# Fetch data using frappe.db.sql
		data = frappe.db.sql(sql_query, query_params, as_dict=True)

		if data:
			return True
		else: return False

	except Exception as e:
		# Log any exceptions that occur during the execution of the query
		frappe.log_error(_("Error in check_cid_existence: {0}").format(e))
		return None
	

@frappe.whitelist(allow_guest=True)
def getApplicantDetails(cid):
	
	try:
		# Execute SQL query
		sql_query = """
		SELECT name, applicant_name, gender, marital_status
		FROM `tabHousing Application` 
		WHERE cid = %(cid)s
		"""
		# Parameters to pass to the query
		query_params = {"cid": cid}

		data = frappe.db.sql(sql_query, query_params, as_dict=True)
		
	   
		

		# Return the data as JSON to the client side
		return data
	except Exception as e:
		frappe.log_error(_("Error in get_tenant_name: {0}").format(e))
	return None

		
	
	
