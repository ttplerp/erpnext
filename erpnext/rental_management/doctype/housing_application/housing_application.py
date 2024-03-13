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
		self.check_salary()
		
		self.validate_detail()
		self.validate_duplicate()
		
		# self.generate_rank()
		creation_time = frappe.utils.get_datetime(self.get('creation'))
		if creation_time and (frappe.utils.now_datetime() - creation_time).total_seconds() <= 2:
			self.generate_rank()
		
		

	def on_update(self):	
		if self.application_status != "Pending" and self.docstatus == 0:
			frappe.db.set_value("Housing Application", self.name, "applicant_rank", 0)
			self.update_ranks()
		self.reload()
			
		


	def check_salary(self):
		gross_salary = float(self.gross_salary) if self.gross_salary else 0
		spouse_gross_salary = float(self.spouse_gross_salary) if self.spouse_gross_salary else 0
		
		total_salary = gross_salary + spouse_gross_salary
		
		grade = self.grade
		
		if total_salary >= 80000 and grade not in  ('ES3','EX3') :
			frappe.throw("Since the total gross salary exceeds Nu.80000, you are not applicable")

	def update_ranks(self):
    # Fetch the applicant list sorted by application_date_time
		applicant_list = frappe.get_all(
			"Housing Application",
			filters={"application_status":"Pending"},
			fields=["name", "application_date_time", "building_classification"],
			order_by="application_date_time ASC",
		)

    # Initialize rank counters for different building classifications
		class1A_rank = 1
		class1B_rank = 1
		class2_rank = 1
		class3_rank = 1
		class4_rank = 1
		class5_rank = 1
    # Add more classes as needed

		for applicant in applicant_list:
			# Assuming you have a function to determine building classification
			building_classification = applicant.get("building_classification")

			# Assign ranks based on building classification
			if building_classification == "Class IA":
				frappe.db.set_value("Housing Application", applicant.get("name"), "applicant_rank", class1A_rank)
				class1A_rank += 1
			elif building_classification == "Class IB":
				frappe.db.set_value("Housing Application", applicant.get("name"), "applicant_rank", class1B_rank)
				class1B_rank += 1
			elif building_classification == "Class II":
				frappe.db.set_value("Housing Application", applicant.get("name"), "applicant_rank", class2_rank)
				class2_rank += 1
			elif building_classification == "Class III":
				frappe.db.set_value("Housing Application", applicant.get("name"), "applicant_rank", class3_rank)
				class3_rank += 1
			elif building_classification == "Class IV":
				frappe.db.set_value("Housing Application", applicant.get("name"), "applicant_rank", class4_rank)
				class4_rank += 1
			elif building_classification == "Class V":
				frappe.db.set_value("Housing Application", applicant.get("name"), "applicant_rank", class5_rank)
				class5_rank += 1	


	def validate_detail(self):
		#citizenship Detail
		data=get_cid_detail(cid=self.cid)
		if data:
			self.applicant_name = data['firstName']+" "+data['middleName']+" "+data['lastName'] if data['middleName'] else data['firstName'] + " " + data['lastName']
			self.gender = "Male" if data['gender'] == "M" else "Female"
			self.dzongkhag = data['dzongkhagName']
			self.gewog = data['gewogName']
			self.village = data['permanentVillagename']

		if self.employment_type == "Civil Servant":
			#Civil Servant Deail
			data1=get_civil_servant_detail(cid=self.cid)
			if data1:
				self.grade = data1['positionLevel']
				self.ministry_agency = data1['OrganogramLevel1']
				self.department = data1['OrganogramLevel2']
				self.employee_id = data1['employeeNumber']
				self.designation = data1['positionTitle']
				self.email_id = data1['Email']
				self.mobile_no = data1['MobileNo']
				self.gross_salary = data1['GrossPay']
		
		if self.marital_status == "Married":
			data2=get_cid_detail(cid=self.spouse_cid)
			if data2:
				self.spouse_name = data2['firstName']+" "+data2['middleName']+" "+data2['lastName'] if data2['middleName'] else data2['firstName'] + " " + data2['lastName']
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
		if self.employment_type != "Civil Servant" and self.work_station != "Thimphu":
			frappe.throw("Housing Application for <b>Non Civil Servant</b> are accepted only for <b>Thimphu</b>")

	def generate_rank(self):
		gross_income = flt(self.gross_salary,2) + flt(self.spouse_gross_salary,2)
		building_class=frappe.db.sql("""
								select name from `tabBuilding Classification`
								where '{gross_income}' between 	minimum_income and maximum_income
							""".format(gross_income=gross_income))[0][0]
		if not building_class:
			frappe.throw("Building Classification not found")
		self.building_classification = building_class

		if not self.applicant_rank:
			highest_rank=frappe.db.sql("""select max(applicant_rank) as ranking 
						from `tabHousing Application`
						where employment_type="{employment_type}"
						and building_classification="{classification}"
					""".format(employment_type=self.employment_type, classification=self.building_classification))[0][0]
			self.applicant_rank=cint(highest_rank) + 1
	
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
					"mobile_no":"phone_no",
					"email_id":"email",
				},
				"postprocess": set_missing_values,
			},
	}, target_doc, ignore_permissions=True)
	return doc


	