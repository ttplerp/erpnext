# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import add_to_date, get_last_day, flt, getdate, cint
from frappe import _
from frappe.model.mapper import get_mapped_doc

class HousingApplication(Document):
	def validate(self):
		self.generate_rank()

	def on_submit(self):
		pass

	def generate_rank(self):
		if not self.applicant_rank:
			highest_rank = frappe.db.sql("""select max(applicant_rank) as ranking 
									from `tabHousing Application` 
									where employment_type="{employment_type}"
								""".format(employment_type=self.employment_type))[0][0]
			self.applicant_rank = cint(highest_rank) + 1

@frappe.whitelist()
def make_tenant_information(source_name, target_doc=None):
	def set_missing_values(obj, target, source_parent):
		if obj.employment_type == "Civil Servant":
			target.ministry_and_agency = obj.ministry_agency
			target.tenant_department = obj.department
		else:
			target.ministry_and_agency = obj.agency
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