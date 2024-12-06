import frappe
import json
from frappe.model.document import Document
from werkzeug.wrappers import Response
from frappe.utils import response as r
from frappe.utils import nowdate,date_diff

@frappe.whitelist()
def get_all_maf():
	datas = frappe.db.sql(f"""Select * from `tabMaintenance Application Form` where docstatus != 2 limit 5""", as_dict=1)

	return datas

# @frappe.whitelist(methods=['POST'])
@frappe.whitelist(allow_guest=True)
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

# @frappe.whitelist(methods=['POST'])
@frappe.whitelist(allow_guest=True)
def housing_clearance():
	data = json.loads(frappe.request.data)

	try:
		""" check existing """
		for a in frappe.db.sql("""
							select name, application_status, application_date, docstatus
							from `tabHousing Clearance`
							where cid='{}'
							and docstatus != 2
							""".format(data.get('cid')), as_dict=True):
			if a.application_status == "Pending":
				msg = f'Your Housing Clearance Application {a.name} is still Pending'
				return {'status_code':200,  'message': msg}

			if a.application_status == "Approved" and a.docstatus==1:
				num_day = date_diff(nowdate(), a.application_date)
				if num_day < 90:
					msg = f'Your Housing Clearance Application {a.name} is Not Expired'
					return {'status_code':200,  'message': msg}
		
		doc = frappe.new_doc('Housing Clearance')
		# doc.ordered_by = frappe.session.user
		doc.applicant_type = data.get('applicant_type')
		doc.cid = data.get('cid')
		doc.application_name = data.get('applicant_name')
		doc.purpose = data.get('purpose')
		doc.email = data.get('email')
		doc.phone_no = data.get('phone_no')
		doc.insert()

		return {'status_code':200,  'message': 'Housing Clearance Form Successfully Applied'}
	except Exception as e:
		frappe.log_error(_("Error in Tenant Info.: {0}").format(e))
		return {'status_code':502,  'message': 'Server error'}

# @frappe.whitelist(methods=['POST'])
@frappe.whitelist(allow_guest=True)
def post_housing_application():
	data = json.loads(frappe.request.data)
	
	try:
		doc = frappe.new_doc('Housing Application')
		doc.cid = data.get('applicant_cid')
		doc.applicant_name = data.get('applicant_name')
		doc.gender = data.get('gender')
		doc.marital_status = data.get('marital_status')
		doc.work_station = data.get('work_station')
		doc.dzongkhag = data.get('dzongkhag')
		doc.gewog = data.get('gewog')
		doc.village = data.get('village')
		doc.date_of_birth = data.get('date_of_birth')

		doc.employment_type = data.get('employment_type')
		doc.designation = data.get('designation')
		doc.ministry_agency = data.get('ministry_agency')
		doc.grade = data.get('grade')
		doc.department = data.get('department')
		doc.employee_id = data.get('employee_id')
		doc.gross_salary = data.get('gross_salary')
		doc.email_id = data.get('email_id')
		doc.mobile_no = data.get('mobile_no')
		doc.agree = data.get('agree')

		if data.get('spouse_cid'):
			doc.spouse_cid = data.get('spouse_cid')
			doc.spouse_name = data.get('spouse_name')
			doc.spouse_dzongkhag = data.get('spouse_dzongkhag')
			doc.spouse_gewog = data.get('spouse_gewog')
			doc.spouse_village = data.get('spouse_village')
			doc.spouse_dob = data.get('spouse_dob')

		if data.get('spouse_employment_type'):
			doc.spouse_employment_type = data.get('spouse_employment_type')
			doc.spouse_designation = data.get('spouse_designation')
			doc.spouse_ministry = data.get('spouse_ministry')
			doc.spouse_grade = data.get('spouse_grade')
			doc.spouse_department = data.get('spouse_department')
			doc.spouse_employee_id = data.get('spouse_employee_id')
			doc.spouse_gross_salary = data.get('spouse_gross_salary')

		doc.insert()
		
		return {'status_code':200,  'message': 'Housing Application Form Successfully Applied'}
	except Exception as e:
		return {'status_code':502,  'message': 'Server error'}
