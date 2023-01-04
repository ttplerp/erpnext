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

class APISetting(Document):
	def validate(self):
		pass

	@frappe.whitelist()
	def generate_token(self):
		url = self.url

		payload='cid={username}&password={password}'.format(username=self.username, password=self.password)
		headers = {
		'Content-Type': 'application/x-www-form-urlencoded'
		}
		response = requests.request("POST", url, headers=headers, data=payload)
		value = response.json()
		self.db_set("bearer_token", value['access_token'])

@frappe.whitelist()
def fetch_data(name, param):
	doc = frappe.get_doc("API Setting Item", name)
	parent_doc = frappe.get_doc("API Setting", doc.parent)
	bearer_token = 'Bearer '+str(parent_doc.bearer_token)
	if doc.param_required and param == "0":
		frappe.throw("You must input a Parameter for this API")
	url = doc.api_url if not doc.param_required else doc.api_url + str(param)
	#frappe.throw("URL: {}".format(url))
	payload={}
	headers = {
		'Authorization': bearer_token
	}
	response = requests.request(doc.request_method, url, headers=headers, data=payload)
	data = response.json()
	
	if doc.api_name == "Fetch Applicants by Cohort":
		frappe.throw("Not applicable to fetch the data from here. Contact the Administrator")
	elif doc.api_name == "Fetch Course Details":	
		i=1
		for a in data['courses']['data']:
			if frappe.db.exists("Course",{"course_name":str(a['name'])}):
				course_name = a['name'] + " - " + str(i)
			else:
				course_name = a['name']
			course_id = a['id']
			description = a['description']
			created_at = a['created_at']
			updated_at = a['updated_at']
			
			if frappe.db.exists("Course",{"course_id":course_id}):
				docs = frappe.get_doc("Course",{"course_id":course_id})
				docs.course_name = course_name
				docs.description = description
				docs.last_update = updated_at
				docs.save()
				i+=1
			else:
				course = frappe.get_doc(
					{
						"doctype": "Course",
						"course_id": course_id,
						"course_name": course_name,
						"description": description,
						"last_update": updated_at
					}
				)
				course.flags.ignore_validate = True
				course.flags.ignore_mandatory = True
				course.insert()
				i+=1
				frappe.msgprint("Course <b>{}</b> is created".format(course_name))
		if i == 0:
			frappe.msgprint("No new courses found")
	elif doc.api_name == "Fetch Cohort":
		for a in data['cohorts']['data']:
			if not frappe.db.exists("Cohort", {"cohort_id":a['id']}):
				cohort = frappe.new_doc("Cohort")
				cohort.cohort_name = a['name']
				cohort.cohort_id = a['id']
				cohort.open_date = a['open_date']
				cohort.close_date = a['end_date']
				cohort.status = a['status']
				cohort.description = a['description']

				for c in a['courses']:
					if frappe.db.exists("Course", {"course_id":c['id']}):
						course = frappe.db.get_value("Course", {"course_id":c['id']})
					else:
						frappe.throw("Course {} and ID {} is missing. Fetch the Courses before fetching the Cohorts".format(c['name'], c['id']))
					cohort.append("item",{
							"course": course,
							"course_id": c['id'],
							"course_name": c['name'],
							"description": c['description']
						})
			else:
				cohort = frappe.get_doc("Cohort", {"cohort_id": a['id']})
				cohort.cohort_name = a['name']
				cohort.open_date = a['open_date']
				cohort.end_date = a['end_date']
				cohort.status = a['status']
				cohort.description = a['description']

				for c in a['courses']:
					if frappe.db.exists("Course", {"course_id":c['id']}):
						course = frappe.db.get_value("Course", {"course_id":c['id']})
					else:
						frappe.throw("Course {} and ID {} is missing. Fetch the Courses before fetching the Cohorts".format(c['name'], c['id']))
					if not frappe.db.exists("Cohort Item", {"parent":cohort.name, "course_id":c['id']}):
						cohort.append("item",{
								"course": course,
								"course_id": c['id'],
								"course_name": c['name'],
								"description": c['description']
						})

			cohort.flags.ignore_validate = True
			cohort.flags.ignore_mandatory = True
			cohort.save()
	elif doc.api_name == "Old Deployment":
		frappe.msgprint("Not applicable from here. Old Deployment is fetch from Applicant detail")
	elif doc.api_name == "Fetch Desuunp by batch":
		for v in data['data']:
			if not frappe.db.exists("Desuup", v['did']):
				if v['permanent_address']:
					per_add = v['permanent_address']
					gewog =per_add['gewog']['name']
					dzongkhag= per_add['dzongkhag']['state']
					village = per_add['village']
				else:
					gewog = dzongkhag = village = ""

				if v['present_address']:
					country = v['present_address']['country']
					address = v['present_address']['street_name']
					pre_dzongkhag = v['present_address']['state']['state']
				else:
					country = address = pre_dzongkhag = ""

				if v['gender'] == "M":
					gender = "Male"
				elif v['gender'] == "F":
					gender = "Female"
				else:
					gender = "Others"
				photo_link = v['avatar']

				desuup_doc = frappe.new_doc("Desuup")
				desuup_doc.desuung_id = v['did']
				desuup_doc.profile_id = v['id']
				desuup_doc.desuup_name = v['name']
				desuup_doc.cid_number = v['cid']
				desuup_doc.gender = gender
				desuup_doc.date_of_birth = v['date_of_birth']
				desuup_doc.batch_number = v['batch_no']
				desuup_doc.marital_status = v['marital_status'] if v['marital_status'] != "Select" else ""
				desuup_doc.blood_group = v['blood_group']
				desuup_doc.training_location = v['training_center_id']
				desuup_doc.dzongkhag = dzongkhag
				desuup_doc.gewog = gewog
				desuup_doc.village = village
				desuup_doc.present_address = address
				desuup_doc.present_dzongkhag = pre_dzongkhag
				desuup_doc.present_country = country
				desuup_doc.email_id = v['email']
				desuup_doc.mobile_number = v['mobile_no']
				desuup_doc.status = "Active"	
				desuup_doc.photo = "<img src='"+str(photo_link)+"'>"
				
				employment_types = {
						1 : "Employed",
						2 : "Unemployed",
						3 :"Student",
						4 : "Displaced",
						5 : "Retired",
						6 : "Freelancer",
				}

				desuup_doc.employment_type = employment_types.get(v['employment_type_id'])		

				if v['employment_detail']:
					emp = v['employment_detail']
					desuup_doc.append("desuup_employement_history_table", {
									"agency": emp['agency'],
									"agency_type": emp['agency_type']['name'],
									"designation": emp['designation'],
									"profession": emp['profession']['name'],
								})
					
				if v['profile_qualification']:
					qualification = v['profile_qualification']
					desuup_doc.append("desuup_qualification_table",{
							"course_name": qualification['course'],
							"qualification": qualification['qualification']['name'],
							"year_of_completion": qualification['year_of_completion'],
						})
				desuup_doc.flags.ignore_validate = True
				desuup_doc.flags.ignore_mandatory = True
				desuup_doc.save()
	doc.last_update = nowdate()
	doc.save()
	frappe.db.commit()
	
	return "success"

