# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import add_to_date, get_last_day, flt, getdate, cint
from frappe import _
from frappe.model.mapper import get_mapped_doc
from erpnext.rental_management.doctype.api_setting.api_setting import get_cid_detail, get_civil_servant_detail


class HousingApplication(Document):
	def validate(self):
		self.check_agree()
		self.check_status()
		self.check_employee_type()
		self.check_salary()
		if self.application_status == None or self.application_status== 'Pending':
			self.validate_detail()
		self.validate_duplicate()
		
		self.check_app_limit()
		creation_time = frappe.utils.get_datetime(self.get('creation'))
		if creation_time and (frappe.utils.now_datetime() - creation_time).total_seconds() <= 2:
			self.generate_rank()
	
	def onload(self):
		# Initialize the gross salary values
		gross_sal = 0.0
		spouse_gross = 0.0

		# Assign values if they exist
		if self.gross_salary:
			gross_sal = self.gross_salary
		if self.spouse_gross_salary:
			spouse_gross = self.spouse_gross_salary

		# Calculate total gross salary
		self.total_gross_salary = flt(gross_sal, 2) + flt(spouse_gross, 2)

	def on_update(self):	
		if self.application_status != "Pending" and self.docstatus == 0:
			frappe.db.set_value("Housing Application", self.name, "applicant_rank", 0)
			self.update_ranks()
		self.reload()
			
	def check_status(self):
		action = frappe.request.form.get('action')
		if action and action in ("Submit"):
			if self.application_status=="Pending":
				frappe.throw("Cannot submit while the application status is still pending")
	def check_employee_type(self):
		if self.is_new() and self.employment_type == "Civil Servant":
			frappe.throw("New applications for civil servants are temporarily suspended, due to a substantial backlog")
   
		if self.is_new() and self.work_station != "Thimphu":
			frappe.throw("Applications are currently only allowed for Thimphu.")
   
	def check_app_limit(self):
		limit = frappe.db.sql('''
                        select name from `tabHousing Application` where work_station="Thimphu" and employment_type="Corporation, Private and etc"
                        and application_status="Pending"

                        ''')
		if self.is_new() and len(limit) > 29:
			frappe.throw("The number of applications has reached the limit of 30 for now.")

	def check_salary(self):
		gross_salary = float(self.gross_salary) if self.gross_salary else 0
		spouse_gross_salary = float(self.spouse_gross_salary) if self.spouse_gross_salary else 0
		
		total_salary = gross_salary + spouse_gross_salary
		
		grade = self.grade
		
		# if total_salary >= 80000 and grade not in  ('ES3','EX3','ES2','EX2','ES1','EX1') :
		# 	frappe.throw("Since the total gross salary exceeds Nu.80000, you are not applicable")
		if self.is_new() and total_salary > 16000:
			frappe.throw("Private applicants of gross houshold income below Nu.16,000 is accepted for now")

	def update_ranks(self):
    # Fetch the applicant list filtered by application_status, building_classification, and work_station, sorted by application_date_time
		applicant_list = frappe.get_all(
			"Housing Application",
			filters={
				"application_status": "Pending",
				"building_classification": self.building_classification,
				"work_station": self.work_station,
				"employment_type":self.employment_type
			},
			fields=["name", "application_date_time", "building_classification"],
			order_by="application_date_time ASC"
		)

		# Initialize rank counters for different building classifications
		rank_counters = {
			"Class IA": 1,
			"Class IB": 1,
			"Class II": 1,
			"Class III": 1,
			"Class IV": 1,
			"Class V": 1,
			# Add more classes as needed
		}

		for applicant in applicant_list:
			# Get the building classification of the applicant
			building_classification = applicant.get("building_classification")

			# Check if the building classification is in the rank_counters dictionary
			if building_classification in rank_counters:
				# Update the rank for the current applicant
				frappe.db.set_value("Housing Application", applicant.get("name"), "applicant_rank", rank_counters[building_classification])
				
				# Increment the rank counter for the current building classification
				rank_counters[building_classification] += 1	


	def validate_detail(self):
		#citizenship Detail
		data=get_cid_detail(cid=self.cid)
		if data:
			if data['firstName'] and data['middleName'] and data['lastName']:
				self.applicant_name = data['firstName'] + " " + data['middleName'] + " " + data['lastName']
			elif data['firstName'] and data['lastName']:
				self.applicant_name = data['firstName'] + " " + data['lastName']
			elif data['firstName']:
				self.applicant_name = data['firstName']
			self.gender = "Male" if data['gender'] == "M" else "Female"
			self.dzongkhag = data['dzongkhagName']
			self.gewog = data['gewogName']
			self.village = data['permanentVillagename']

		if self.employment_type == "Civil Servant":
			#Civil Servant Deail
			data1=get_civil_servant_detail(cid=self.cid)
			if data1:
				self.grade = data1['positionLevel']
				if 'OperatingUnit' in data1:
					self.ministry_agency = data1['OperatingUnit']
				if 'DeptName' in data1:
					self.department = data1['DeptName']
				if 'EmpID' in data1:
					self.employee_id = data1['EmpID']
				if 'Designation' in data1:
					self.designation = data1['Designation']
				# self.email_id = data1['Email']
				# self.mobile_no = data1['MobileNo']
				if 'GrossPay' in data1:
					self.gross_salary = data1['GrossPay']
		
		if self.marital_status == "Married":
			data2=get_cid_detail(cid=self.spouse_cid)
			if data2:
				if data2['firstName'] and data2['middleName'] and data2['lastName']:
					self.spouse_name = data2['firstName'] + " " + data2['middleName'] + " " + data2['lastName']
				elif data2['firstName'] and data2['lastName']:
					self.spouse_name = data2['firstName'] + " " + data2['lastName']
				elif data2['firstName']:
					self.spouse_name = data2['firstName']
				self.spouse_dob = data2['dob']
				self.spouse_dzongkhag = data2['dzongkhagName']
				self.spouse_gewog = data2['gewogName']
				self.spouse_village = data2['permanentVillagename']
				
			if self.spouse_employment_type=="Civil Servant":
				data3=get_civil_servant_detail(cid=self.spouse_cid)
				if data3:
					self.spouse_designation = data3['positionTitle']
					self.spouse_grade = data3['positionLevel']
					self.spouse_ministry = data3['OrganogramLevel1']
					self.spouse_department = data3['OrganogramLevel2']
					self.spouse_gross_salary = data3['GrossPay']

	def on_submit(self):
		pass
	
	def check_agree(self):
		if not self.agree:
			frappe.throw("You must <b>Agree to Terms</b> in order to submit the application")
		# if self.employment_type != "Civil Servant" and self.work_station != "Thimphu":
		# 	frappe.throw("Housing Application for <b>Non Civil Servant</b> are accepted only for <b>Thimphu</b>")

	def generate_rank(self):
		gross_income = flt(self.gross_salary, 2) + flt(self.spouse_gross_salary, 2)
		
		# Using parameterized queries to prevent SQL injection
		building_class_result = frappe.db.sql("""
			SELECT name 
			FROM `tabBuilding Classification`
			WHERE %s BETWEEN minimum_income AND maximum_income
		""", (gross_income,))
		
		if not building_class_result or not building_class_result[0]:
			frappe.throw("Building Classification not found")
		
		building_class = building_class_result[0][0]
		self.building_classification = building_class

		if not self.applicant_rank:
			highest_rank_result = frappe.db.sql("""
				SELECT MAX(applicant_rank) AS ranking 
				FROM `tabHousing Application`
				WHERE employment_type=%s
				AND building_classification=%s
				AND work_station=%s
			""", (self.employment_type, self.building_classification, self.work_station))
			
			if highest_rank_result and highest_rank_result[0][0] is not None:
				self.applicant_rank = cint(highest_rank_result[0][0]) + 1
			else:
				self.applicant_rank = 1


	def validate_duplicate(self):
		if frappe.db.exists("Housing Application", {"cid":self.cid, "name":("!=",self.name), "docstatus":("!=", 2)}):
			frappe.throw("Applicant with <b>CID No. {} </b>has already registered for Housing application".format(self.cid))

		if frappe.db.exists("Tenant Information", {"tenant_cid":self.cid, "status":"Allocated", "docstatus":("!=", 2)}):
			frappe.throw("Applicant with <b>CID No. {} </b> is an active  tenant in Tenant Information".format(self.cid))

@frappe.whitelist()
def make_tenant_information(source_name, target_doc=None):
	def set_missing_values(obj, target, source_parent):
		if obj.employment_type == "Civil Servant":
			target.ministry_and_agency = obj.ministry_agency
			target.tenant_department = obj.department
		else:
			target.agency = obj.agency

		if obj.flat_no:
			block_no=frappe.db.get_value("Flat No", obj.flat_no, "block_no")
			target.block_no=block_no
			target.locations=frappe.db.get_value("Block No", block_no, "location")
			target.flat_no=obj.flat_no

		if obj.employment_type=="Civil Servant":
			pass

		target.employee_id=""

	doc = get_mapped_doc("Housing Application", source_name, {
			"Housing Application": {
				"doctype": "Tenant Information",
				"field_map": {
					"name": "housing_application",
					"applicant_name":"tenant_name",
					"cid":"tenant_cid",
					"phone_no":"mobile_no",
					"email":"email_id",
				},
				"postprocess": set_missing_values,
			},
	}, target_doc, ignore_permissions=True)
	return doc


	