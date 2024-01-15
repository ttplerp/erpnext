# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class HousingApplicationDetailsUpdate(Document):
	pass



def update_housing_application_doctype(doc, method):
	
	sql_query = """
			UPDATE `tabHousing Application`
			SET gender= %s,
			marital_status =%s,
			spouse_cid=%s,
			spouse_name=%s,
			spouse_dob=%s,
			spouse_employment_type=%s,
			spouse_dzongkhag=%s,
			spouse_gewog=%s,
			spouse_village=%s,
			spouse_designation=%s,
			spouse_grade=%s,
			spouse_ministry=%s,
			spouse_agency=%s,
			spouse_department=%s,
			spouse_gross_salary=%s,
			
			mobile_no=%s
			

			where cid = %s
		"""
	try: 
		frappe.db.sql(sql_query,(doc.gender,doc.marital_status,doc.spouse_citizen_id,
						         doc.spouse_name,doc.spouse_date_of_birth,doc.spouse_employment_type, 
						         doc.spouse_dzongkhag,doc.spouse_gewog,
								 doc.spouse_village,doc.spouse_designation,
								 doc.spouse_grade,doc.spouse_ministryagency,
								 doc.spouse_name_of_agency,doc.spouse_department,doc.spouse_gross_salary or 0,
								doc.mobile_no,doc.cid))
		frappe.db.commit()
		# frappe.msgprint(f"Data updated succefully for CID: {doc.cid}")
	except Exception as e:
		frappe.msgprint(f"Error updating data: {str(e)}")
	
	

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
		SELECT name,
		   
		  mobile_no,
		  applicant_name, 
		  gender, 
		  marital_status,
		  spouse_cid,

		  spouse_name,
		  spouse_dzongkhag,
		  spouse_gewog,
		  spouse_dob,
		  spouse_village,
		  spouse_employment_type,
		  spouse_employee_id,
		  spouse_ministry,
		  spouse_designation,
		  spouse_agency,
		  spouse_grade,
		  spouse_gross_salary,
		  date_of_birth






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

		
	
	
