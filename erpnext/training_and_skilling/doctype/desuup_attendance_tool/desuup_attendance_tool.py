# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import json
import frappe
from frappe.model.document import Document
from frappe.utils import getdate
from frappe import _

class DesuupAttendanceTool(Document):
	pass

@frappe.whitelist()
def get_desuups(date, attendance_for, cost_center=None, training_management=None, desuup_deployment=None, domain=None, programme=None, training_center=None, company=None):
	attendance_not_marked = []
	attendance_marked = []

	def get_conditions():
		cond = ''
		if desuup_deployment:
			cond += " and t1.name = '{}'".format(desuup_deployment)
		if training_center:
			cond += " and t1.training_center = '{}'".format(training_center)
		if training_management:
			cond += " and t1.name = '{}'".format(training_management)
		return cond
	
	def get_deployment_list(new_cond):
		cond = get_conditions()
		return frappe.db.sql("""
						select t2.desuup, t2.desuup_name
						from `tabDesuup Deployment Entry` t1, `tabDesuup Deployment Entry Item` t2
						where t1.name = t2.parent
						and t1.status = 'On Going'
						and t2.status = 'Reported'
						and '{}' between t1.start_date and t1.end_date {} {}
						order by t2.desuup_name
						""".format(getdate(date), cond, new_cond), as_dict=True)

	if attendance_for == "Trainee":
		cond = get_conditions()
		desuup_list = frappe.db.sql("""
						select t2.desuup_id as desuup, t2.desuup_name 
						from `tabTraining Management` t1, `tabTrainee Details` t2
						where t1.name = t2.parent
						and t1.status = 'On Going' 
						and t2.status = 'Reported'
						and '{}' between t1.training_start_date and t1.training_end_date {} 
						order by t2.desuup_name
						""".format(getdate(date), cond), as_dict=True)
		
	elif attendance_for == "OJT":
		new_cond = ''
		new_cond += " and t1.deployment_type = 'OJT'"
		desuup_list = get_deployment_list(new_cond)
	elif attendance_for == "Production":
		new_cond = ''
		new_cond += " and t1.deployment_type = 'Production'"
		desuup_list = get_deployment_list(new_cond)

	else:
		desuup_list = []
	
	marked_desuup = {}
	for dsp in frappe.get_list(
		"Desuup Attendance", fields=["desuup", "status"], filters={"attendance_date": date}
	):
		marked_desuup[dsp["desuup"]] = dsp["status"]

	for dsp in desuup_list:
		dsp['status'] = marked_desuup.get(dsp['desuup'])
		if dsp["desuup"] not in marked_desuup:
			attendance_not_marked.append(dsp)
		else:
			attendance_marked.append(dsp)

	return {"marked": attendance_marked, "unmarked": attendance_not_marked}

@frappe.whitelist()
def mark_desuup_attendance(desuup_list, status, date, attendance_for, company=None):

	desuup_list = json.loads(desuup_list)
	for desuup in desuup_list:

		company = frappe.db.get_value("Desuup", desuup["desuup"], "Company", cache=True)

		attendance = frappe.get_doc(
			dict(
				doctype="Desuup Attendance",
				desuup=desuup.get("desuup"),
				desuup_name=desuup.get("desuup_name"),
				attendance_date=getdate(date),
				attendance_for=attendance_for,
				status=status,
				company=company,
			)
		)
		attendance.insert()
		attendance.submit()
