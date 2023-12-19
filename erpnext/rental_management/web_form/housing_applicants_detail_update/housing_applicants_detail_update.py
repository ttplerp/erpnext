import frappe

def get_context(context):
	# do your magic here
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
	return "hello"
	
	# try:
	# 	# Execute SQL query
	# 	sql_query = """
	# 	SELECT name, maf_status
	# 	FROM `tabMaintenance Application Form` 
	# 	WHERE cidd = %(tenant_cid)s
	# 	ORDER BY creation DESC LIMIT 1
		
	# 	"""

	# 	# Parameters to pass to the query
	# 	query_params = {"tenant_cid": tenant_cid}

	# 	# Fetch data using frappe.db.sql
	# 	data = frappe.db.sql(sql_query, query_params, as_dict=True)

	# 	if data:
	# 		first_record = data[0]  # Accessing the first record
	# 		maf_status = first_record.get('maf_status')  # Retrieving the 'name' field
	# 		# frappe.throw(record_name)
		
	# 	# Check if data exists
	# 	if data and maf_status not in ['Closed', 'Completed']:
		   
	# 		# CID exists, showing the existing CID and allowing the check
	# 		frappe.msgprint(f"CID {tenant_cid} already applied and that application is not yet closed or completed.")
	# 		return True
	# 	else:
	# 		# CID does not exist, preventing the check and showing a message
		   
	# 		return False
		
	# 	 # Check if data exists
	# 	# if data and maf_status!='closed':
	# 	#     # CID exists, showing the existing CID and allowing the check
	# 	#     frappe.msgprint(f"CID {tenant_cid} already applied and its not closed yet. ")
	# 	#     return True
	# 	# else:
	# 	#     # CID does not exist, preventing the check and showing a message
		   
	# 	#     return False
	  

	# except Exception as e:
	# 	# Log any exceptions that occur during the execution of the query
	# 	frappe.log_error(_("Error in check_cid_existence: {0}").format(e))
	# 	return None



