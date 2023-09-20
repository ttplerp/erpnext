# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import add_to_date, get_last_day, flt, getdate, cint
from frappe import _
from frappe.model.mapper import get_mapped_doc

class HousingApplication(Document):
	def validate(self):
		self.check_agree()
		self.validate_duplicate()
		self.generate_rank()

	def on_submit(self):
		pass
	
	def check_agree(self):
		if not self.agree:
			frappe.throw("You must agree to terms in order to submit the application")
		if self.employment_type != "Civil Servant" and self.work_station != "Thimphu":
			frappe.throw("Housing Application for Non Civil Servant are accepted only for Thimphu")

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