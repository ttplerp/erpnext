# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _, throw
from frappe.model.document import Document
import requests, json
from frappe.utils import (
	add_days,add_months, cint, date_diff, flt, get_datetime, get_last_day, get_first_day, getdate, month_diff, nowdate,	today, get_year_ending,	get_year_start,
)

class TrainingSelection(Document):
	def validate(self):
		if self.gender_base_selection:
			self.slot = int(self.male_slot) + int(self.female_slot)
		self.check_duplicate_cohort_course()
		self.workflow_process()

	def check_duplicate_cohort_course(self):
		for a in frappe.db.sql("""select name, posting_date
								from `tabTraining Selection`
								where cohort = '{0}' and course = '{1}'
								and name != '{2}'
						""".format(self.cohort, self.course, self.name), as_dict=True):
			frappe.throw("""Selection Process for cohort <b>{}</b> and course <b>{}</b> is already recorded in transaction <b>{}</b> 
						""".format(self.cohort, self.course, a.name))
		
		if not self.slot or self.slot < 1:
			frappe.throw("No of slots for the training should be greater than 1")

	def workflow_process(self):
		if self.workflow_state == "Deployment Updated":
			for a in self.get("item"):
				if not a.update_deployment:
					frappe.throw(_("""Deployment not updated for Desuup <b>{}</b> at <b>Row : {}</b>. Please update deployment from Utilities""".format(a.did, a.idx)))
		
		if self.workflow_state == "Selection Completed":
			for a in self.get("item"):
				if self.pre_requisite:
					if a.course_pre_requisite == "" and a.status == "Registered":
						frappe.throw("Course Prerequisite check is missing for Desuup ID <b>{}</b>. Please process the prerequisite check from Utilities".format(a.did))
				if a.status == "Registered":
					frappe.throw("Shortlisting and Ranking is not processed. Please proceed from Utilities")			
	
	@frappe.whitelist()
	def applicant_shortlisting(self):
		idx = highest_rank = 0
		if self.gender_base_selection:
			if self.male_slot < 1 or self.female_slot < 1:
				frappe.throw("For Gender Base Selection, Training Slot for male or female should be greater than 0 (Zero)")
			
			for gender in ["Male","Female"]:
				slot = self.male_slot + idx if gender == "Male" else self.female_slot + idx
				if self.pre_requisite:
					for a in self.get("item"):
						if a.course_pre_requisite == "" and a.status == "Registered":
							frappe.throw("Course Prerequisite check is missing for Desuup ID <b>{}</b>. Please process the prerequisite check from Utilities".format(a.did))
					for a in frappe.db.sql(""" SELECT name, did, final_point, DENSE_RANK() OVER (order by final_point desc) as rank
									from `tabTraining Selection Item` 
									where status not in ("Withdrawn","Disqualified","Barred")  
									and course_pre_requisite = "Yes"
									and parent = '{0}'
									and gender = '{1}'
									""".format(self.name, gender), as_dict=True):
						idx += 1
						status = "Standby" if idx > slot else "Shortlisted"
						frappe.db.sql("""update `tabTraining Selection Item` 
									set selection_rank = '{0}', status = '{1}', idx = "{2}"
									where name= '{3}'""".format(int(a.rank), status, idx, a.name))
						highest_rank = int(a.rank) if int(a.rank) > highest_rank else highest_rank
			
				for b in frappe.db.sql(""" SELECT name, did, final_point, DENSE_RANK() OVER (order by final_point desc) as rank
									from `tabTraining Selection Item` 
									where status not in ("Withdrawn","Disqualified","Barred") 
									and (course_pre_requisite != "Yes" or course_pre_requisite is NULL)
									and parent = '{0}'
									and gender = '{1}'
									""".format(self.name, gender), as_dict=True):
					idx += 1
					status = "Standby" if idx > slot else "Shortlisted"
					frappe.db.sql("""update `tabTraining Selection Item` 
									set selection_rank = '{0}', status = '{1}', idx = "{2}"
									where name= '{3}'""".format(int(b.rank) + highest_rank, status, idx, b.name))
		else:
			if self.pre_requisite:
				for a in self.get("item"):
					if a.course_pre_requisite == "" and a.status == "Registered":
						frappe.throw("Course Prerequisite check is missing for Desuup ID <b>{}</b>. Please process the prerequisite check from Utilities".format(a.did))
				for a in frappe.db.sql(""" SELECT name, did, final_point, DENSE_RANK() OVER (order by final_point desc) as rank
									from `tabTraining Selection Item` 
									where status not in ("Withdrawn","Disqualified","Barred")  
									and course_pre_requisite = "Yes"
									and parent = '{0}'
									""".format(self.name), as_dict=True):
					idx += 1
					status = "Standby" if idx > self.slot else "Shortlisted"
					frappe.db.sql("""update `tabTraining Selection Item` 
									set selection_rank = '{0}', status = '{1}', idx = "{2}"
									where name= '{3}'""".format(int(a.rank), status, idx, a.name))
					highest_rank = int(a.rank) if int(a.rank) > highest_rank else highest_rank
			
			for b in frappe.db.sql(""" SELECT name, did, final_point, DENSE_RANK() OVER (order by final_point desc) as rank
									from `tabTraining Selection Item` 
									where status not in ("Withdrawn","Disqualified","Barred") 
									and (course_pre_requisite != "Yes" or course_pre_requisite is NULL)
									and parent = '{0}'
									""".format(self.name), as_dict=True):
					idx += 1
					status = "Standby" if idx > self.slot else "Shortlisted"
					frappe.db.sql("""update `tabTraining Selection Item` 
									set selection_rank = '{0}', status = '{1}', idx = "{2}"
									where name= '{3}'""".format(int(b.rank) + highest_rank, status, idx, b.name))
		
		for c in frappe.db.sql(""" SELECT name, did
								from `tabTraining Selection Item` 
								where status in ("Withdrawn","Disqualified","Barred") 
								and parent = '{0}'
								""".format(self.name), as_dict=True):
				idx += 1
				frappe.db.sql("""update `tabTraining Selection Item` 
								set idx = "{0}"
								where name= '{1}'""".format(idx, c.name))		
		frappe.db.commit()
		frappe.msgprint("Shortlisting and Ranking completed successfully")

	@frappe.whitelist()
	def calculate_points(self):
		for a in self.get("item"):
			if a.status == "Registered":
				if not a.update_deployment:
					frappe.throw("Deployment data is not fetch and updated from dashboard database for Desuup <b>{}</b>".format(a.did))
				if not a.barred_list:
					frappe.throw("Dessup {} has not gone through validation check with Desuup Barred list".format(a.did))
				if not a.maximum_three_core_skill_check:
					frappe.throw("Dessup {} has not gone through validation check for Eligibility for Maximum of 3 core skill training".format(a.did))
			desuup_id = a.did
			total_points = 0.00
			detail = ""
			count_dtl = frappe.db.sql(""" Select count(*) as training_attended_count
										from `tabTraining Management` m
										inner join `tabTrainee Details` d
										on m.name = d.parent
										where m.docstatus != 2
										and d.desuup_id = '{}'
								""".format(desuup_id), as_dict=True)
			training_attended_count = count_dtl[0].training_attended_count
								
			for a in frappe.db.sql(""" select  name, deployment_title, deployment_category, days_attended
								from `tabDeployment`
								where desuung_id = '{}'
								""".format(desuup_id), as_dict=True):
				deployment_category = a.deployment_category
				if not deployment_category:
					deployment_category = frappe.db.get_value("Deployment Title", a.deployment_title)
					if not deployment_category:
						frappe.throw("{0} not mapped to Deployment Category. Please map to proceed further {1} and {2}".format(frappe.get_desk_link("Deployment Title",a.deployment_title), desuup_id, a.name))
				else:
					actual_point = flt(a.days_attended) * flt(frappe.db.get_value("Deployment Category", a.deployment_category, "point"))
					detail += "'" + str(a.deployment_title) + " (" + str(a.deployment_category) + ")' : " + str(actual_point) + "<br/>"
				total_points += flt(actual_point)
			
			final_point = flt(total_points/(training_attended_count+1),2)
			frappe.db.sql("""Update `tabTraining Selection Item` 
							set point_remark="{}", 
								total_point="{}", 
								training_attended="{}",
								final_point ="{}" 
							where did = "{}"
								and parent = "{}"
						""".format(detail, total_points, training_attended_count, final_point, desuup_id, self.name))
			frappe.db.commit()

	@frappe.whitelist()
	def check_barred(self):
		if self.get("item"):
			for a in self.get("item"):
				barred_dtl = frappe.db.sql(""" select name, reason, from_date, to_date
									from `tabBarred Desuup`
									where docstatus != 2 
									and '{}' between from_date and to_date
									and desuung_id = '{}'
							""".format(self.posting_date , a.did), as_dict=True)
				status = a.status
				remark = a.remark
				if barred_dtl:
					status = "Barred"
					remark = "Barred reason: " + str(barred_dtl[0].reason) + ". Dessuup barred from " + str(barred_dtl[0].from_date) + \
									" till " + str(barred_dtl[0].to_date) + " in Document " + str(barred_dtl[0].name)
				frappe.db.sql("Update `tabTraining Selection Item` set barred_list = '1', status = '{0}', remark = '{1}' \
							where name= '{2}'".format(status, remark, a.name))
			frappe.db.commit()

	@frappe.whitelist()
	def check_pre_requisites(self):
		if self.pre_requisite:
			cond = ""
			if self.pre_requisite_course:
				cond = " and m.course = '{}'".format(self.pre_requisite_course)
			
			for a in self.get("item"):
				status = a.status
				remark = str(a.remark)
				if a.status == "Registered":
					training_dtl = frappe.db.sql(""" Select m.name
													from `tabTraining Management` m
													inner join `tabTrainee Details` d
													on m.name = d.parent
													where m.docstatus != 2
													and d.desuup_id = '{}'
													{}
										""".format(a.did, cond), as_dict=True)
					if training_dtl:
						remark = str(remark) + "Prerequisite met and applicant is allowed to process further"
						meets_rerequisite = "Yes"
					else:
						status = "Prerequisite Not Met"
						meets_rerequisite = "No"
						remark + str(remark) + " Prerequisite Not Met "
					frappe.db.sql("Update `tabTraining Selection Item` set course_pre_requisite = '{0}', remark = '{1}' \
								where name= '{2}'".format(meets_rerequisite, remark, a.name))
			frappe.db.commit()

	@frappe.whitelist()
	def eligibility_for_domain(self):
		for a in self.get("item"):
			if a.status == "Registered":
				domain_count = 0
				domain_count = frappe.db.sql(""" Select count(distinct(domain)) as domain_count
												from `tabTraining Management` m
												inner join `tabTrainee Details` d
												on m.name = d.parent
												where m.docstatus != 2
												and d.desuup_id = '{}'
										""".format(a.did), as_dict=True)
				status = a.status
				remark = a.remark
				if domain_count[0].domain_count > 3:
					status = "Disqualified"
					remark = str(remark) + " Applicant is disqualified as he has already availed training in 3 different domains"
				frappe.db.sql("Update `tabTraining Selection Item` set maximum_three_core_skill_check = 1, status = '{0}', remark = '{1}' \
								where name= '{2}'".format(status, remark, a.name))
		frappe.db.commit()

	@frappe.whitelist()
	def update_desuup_deployment(self):
		api_doc = frappe.get_doc("API Setting Item", {"api_name":"Old Deployment"})
		parent_doc = frappe.get_doc("API Setting", api_doc.parent)
		bearer_token = 'Bearer '+str(parent_doc.bearer_token)
		if self.get("item"):
			for a in self.get("item"):
				if not a.update_deployment:
					url = api_doc.api_url + str(a.profile_id) + "/old-deployment?pageSize=10000"
					payload={}
					headers = {
						'Authorization': bearer_token
					}
					response = requests.request(api_doc.request_method, url, headers=headers, data=payload)
					data = response.json()
					if data['content']:
						for d in data['content']:
							if not frappe.db.exists("Deployment", {"deployment_id":d['id']}):
								doc = frappe.new_doc("Deployment")
								doc.deployment_id = d['id']
								doc.desuung_id = a.did
								doc.profile_id = a.profile_id
								doc.cid = a.cid
								doc.start_date = d['startDate']
								doc.end_date = d['endDate']
								doc.days_attended = d['daysAttended']
								title = d['deploymentTitle'].lstrip()
								deployment_title = title.replace('"','')
								if not frappe.db.exists("Deployment Title", deployment_title):
									dep_doc = frappe.new_doc("Deployment Title")
									dep_doc.deployment_title = deployment_title
									dep_doc.save()
								else:
									deployment_category = frappe.db.get_value("Deployment Title", deployment_title)
									doc.deployment_category = deployment_category
								doc.deployment_title = deployment_title
								doc.location = d['location']
								doc.submit()
					frappe.db.sql("Update `tabTraining Selection Item` set update_deployment = '1' where name= '{}'".format(a.name))
					frappe.db.commit()

	@frappe.whitelist()
	def get_applicants(self):
		self.set('item', [])
		for a in frappe.db.sql(""" select did, cid, profile_id, desuup_name,  gender, mobile, email, date_of_birth,
									employment_type
									from `tabCohort Applicant`
									where cohort_id = "{cohort}"
									and course_id = "{course}"
						""".format(cohort=self.cohort_id, course=self.course_id), as_dict=True):
			if frappe.db.exists("Desuup", a.did):
				row = self.append('item', {})
				if frappe.db.exists("Desuup Qualification", {"parent":a.did}):
					edu_doc = frappe.get_doc("Desuup Qualification", {"parent":a.did})
					row.qualification =  edu_doc.qualification
					row.level = edu_doc.level
					row.year_of_completion = edu_doc.year_of_completion
					row.course_name = edu_doc.course_name
				if frappe.db.exists("Desuup Employment History", {"parent":a.did}):
					emp_doc = frappe.get_doc("Desuup Employment History", {"parent":a.did})
					row.agency_type = emp_doc.agency_type
					row.agency = emp_doc.agency
					row.profession = emp_doc.profession
				desuup_doc = frappe.get_doc("Desuup", a.did)
				row.country = desuup_doc.present_country 
				row.present_address = desuup_doc.present_address
				row.dzongkhag = desuup_doc.dzongkhag
				row.gewog = desuup_doc.gewog
				row.village = desuup_doc.village
				row.status = "Registered"
				row.update(a)
			else:
				frappe.msgprint("Desuup ID <b>{}</b> details are missing from Desuung database".format(a.did))
	
	@frappe.whitelist()
	def send_offer_letter(self):
		for a in self.get("item"):
			if a.confirmation_status ==  "Selected"  and not a.offer_letter_sent:
				frappe.db.sql("update `tabTraining Selection Item` set offer_letter_sent = 1 where name = '{}'".format(a.name))
		frappe.db.sql("update `tabTraining Selection` set offer_letter_sent = 1 where name = '{}'".format(self.name))
		frappe.db.commit()
		frappe.msgprint("<b>DSP Offer Letter </b> sent successfully for selected applicants via respective email address")

	@frappe.whitelist()
	def create_training(self):
		frappe.msgprint("<b>DSP Training created successfully for selected applicants</b>")
			
@frappe.whitelist()
def get_courses(doctype, txt, searchfield, start, page_len, filters):
	return frappe.db.sql("""
				select name, course_name, domain, description from `tabCourse`
						where name in (
							select course
							from `tabCohort Item`
							where parent = '{cohort}'
						)
						and ({key} like %(txt)s
								or course_name like %(txt)s
								or domain like %(txt)s)
				order by
						name, domain, course_name
				limit %(start)s, %(page_len)s""".format(**{
						'cohort': filters.get("cohort"),
						'key': searchfield,
				}), {
						'txt': "%%%s%%" % txt,
						'_txt': txt.replace("%", ""),
						'start': start,
						'page_len': page_len
	})
