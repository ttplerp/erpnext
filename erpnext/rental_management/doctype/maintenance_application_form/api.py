import frappe
import json
from frappe.model.document import Document
from werkzeug.wrappers import Response
from frappe.utils import response as r

@frappe.whitelist()
def get_all_maf():
	datas = frappe.db.sql(f"""Select * from `tabMaintenance Application Form` where docstatus != 2 limit 5""", as_dict=1)

	return datas

@frappe.whitelist(methods=['POST'])
def create_maf():
	data = json.loads(frappe.request.data)
	tenant_info = get_cid_detail(data.get('cid'))
	
	if len(tenant_info) == 0:
		return {'status_code':404,  'message': 'No data found!'}
	# maf = frappe.get_doc({
	#     "doctype": 'Maintenance Application Form',
	#     "tenant_id": tenant_info[0].name,
	#     "tenant_name": tenant_info[0].tenant_name,
	#     "block_no": tenant_info[0].block_no,
	#     "flat_no": tenant_info[0].flat_no,
	#     "location_name": tenant_info[0].location_name,
	#     "location": tenant_info[0].locations,
	#     "dzongkhag": tenant_info[0].dzongkhag,
	#     "cidd": data.get('cid'),
	#     "maintenance_type": data.get('maintenance_type'),
	#     "phone_number": data.get('phone_no'),
	#     "email": data.get('email'),
	#     "longtex": data.get('descriptioin'),
	#     })
	# maf.insert()

	doc = frappe.new_doc('Maintenance Application Form')
	# doc.ordered_by = frappe.session.user
	doc.tenant_id = tenant_info[0].name
	doc.tenant_name = tenant_info[0].tenant_name
	doc.block_no = tenant_info[0].block_no
	doc.flat_no = tenant_info[0].flat_no
	doc.location_name = tenant_info[0].location_name
	doc.location = tenant_info[0].locations
	doc.dzongkhag = tenant_info[0].dzongkhag
	doc.cidd = data.get('cid')
	doc.maintenance_type = data.get('maintenance_type')
	doc.phone_number = data.get('phone_no')
	doc.email = data.get('email')
	doc.longtex = data.get('descriptioin')
	doc.insert()

	return {'status_code':200,  'message': 'Maintenance Application Form Successfully Applied'}

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
		frappe.log_error(_("Error in Tenant Info.: {0}").format(e))
		return None

""" {"tenant_cid": "cid here"} """
@frappe.whitelist(methods=['GET'])
def get_applicant_info(applicant_cid):
	if applicant_cid:
		sql_query = """ 
				SELECT name, applicant_name, cid, gender, employment_type, applicant_rank, application_status, 
					mobile_no, flat_no, building_classification, application_date_time
				from `tabHousing Application`
				where cid = %(applicant_cid)s
			"""
		
		# Parameters to pass to the query
		query_params = {"applicant_cid": applicant_cid}

		data = frappe.db.sql(sql_query, query_params, as_dict=True)
		# Return the data as JSON to the client side

		if len(data) > 0:
			return {'status_code':200,  'message': 'Successful', 'data': data}
		else:
			return {'status_code':404,  'message': 'No data found!'}

@frappe.whitelist(methods=['GET'])
def tenant_cid(tenant_cid):
	try:
		# Execute SQL query
		sql_query = """
		SELECT name as tenant_id, tenant_name, block_no, flat_no, location_name,dzongkhag,locations,phone_no,tenant_cid,
		rate_per_sqft as rate, total_floor_area as floor_area, initial_allotment_date as allotment_date, rental_term_year as rental_year
		FROM `tabTenant Information` 
		WHERE tenant_cid = %(tenant_cid)s
		"""
		# Parameters to pass to the query
		query_params = {"tenant_cid": tenant_cid}

		data = frappe.db.sql(sql_query, query_params, as_dict=True)
		# Return the data as JSON to the client side

		if len(data) > 0:
			return {'status_code':200,  'message': 'Successful', 'data': data}
		else:
			return {'status_code':404,  'message': 'No dataaaa found!', 'data': {}}
	except Exception as e:
		frappe.log_error(_("Error in Tenant Info.: {0}").format(e))
		return {'status_code':502,  'message': 'Server error'}