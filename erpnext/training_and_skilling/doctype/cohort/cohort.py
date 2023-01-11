# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import requests, json
from frappe.utils import (
	add_days,
	add_months,
	cint,
	date_diff,
	flt,
	get_datetime,
	get_last_day,
	get_first_day,
	getdate,
	month_diff,
	nowdate,
	today,
	get_year_ending,
	get_year_start,
)

class Cohort(Document):
	def validate(self):
		pass

	@frappe.whitelist()
	def get_applicants(self):
		if not self.cohort_id:
			frappe.throw("Cohort ID is mandatory to fetch applicants")
		
		doc = frappe.get_doc("API Setting Item", {"api_name":"Fetch Applicants by Cohort"})
		parent_doc = frappe.get_doc("API Setting", doc.parent)
		bearer_token = 'Bearer '+str(parent_doc.bearer_token)

		url = doc.api_url + str(self.cohort_id)
		payload={}
		headers = {
			'Authorization': bearer_token
		}
		response = requests.request(doc.request_method, url, headers=headers, data=payload)
		data = response.json()
		self.set('applicant', [])
		for k, a in enumerate(data):
			#frappe.msgprint("Data : {}".format(a['profile']['did']))
			row = self.append('applicant', {})
			row.profile_id = a['profile']['id']
			row.did = a['profile']['did']
			row.cid = a['profile']['cid']
			row.mobile = a['profile']['mobile_no']	
			if frappe.db.exists("Desuup", a['profile']['did']):
				doc = frappe.get_doc("Desuup", a['profile']['did'])
				row.desuup_name = doc.desuup_name
				row.gender =  doc.gender
				row.email =  doc.email_id
				row.date_of_birth = doc.date_of_birth
			row.cohort_id = a['cohorts']['id']
			row.cohort_name = a['cohorts']['name']
			row.course_id = a['course']['id']
			row.course_name = a['course']['name']
			row.course = frappe.db.get_value("Course", {"course_id":a['course']['id']})
