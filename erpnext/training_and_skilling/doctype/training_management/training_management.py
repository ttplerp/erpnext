# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import flt, getdate, cint, today, nowdate, add_years, add_months, add_days, date_diff, month_diff

from datetime import datetime

class TrainingManagement(Document):
	def validate(self):
		# self.set_status()
		if self.workflow_state == "Submitted" and self.docstatus == 0:
			self.notify_lo()
		# self.check_date()
		# self.validate_trainer_course()
		# self.validate_desuup_course()
		# self.count_duration()
		# self.check_cohort_batch()

	def notify_lo():
		receipients = []
		args = self.as_dict()
		lo_emails = frappe.get_list("Laison Officer", filters={"parent":self.training_center}, fields=['email'])
		if lo_emails:
			receipients = [a['email'] for a in lo_emails]
		
		email_template = frappe.get_doc("Email Template", "Notify Laison Officer")
		message = frappe.render_template(email_template.response, args)
		if receipients:
			self.notify({
				# for post in messages
				"message": message,
				"message_to": receipients,
				# for email
				"subject": email_template.subject
			})

	def set_status(self):
		self.docstatus = {
			"Draft": 0,
			"Created": 0,
			"On Going": 0,
			"Completed": 1,
			"Cancelled": 2
		}[str(self.status) or 'Draft']

	def check_date(self):
		if(datetime.strptime(str(self.training_start_date),"%Y-%m-%d") > datetime.strptime(str(self.training_end_date),"%Y-%m-%d")):
			frappe.throw("Training start date cannot be before training end date")
	
	def count_duration(self):
		no_of_days = date_diff(self.training_end_date,self.training_start_date) + 1
		self.course_duration =  str(no_of_days)

	def validate_trainer_course(self):
		trainer = frappe.db.sql("""
						SELECT
							ti.trainer_id, tm.name, tm.training_end_date, tm.course_cost_center
						FROM `tabTraining Management` tm inner join `tabTrainer Information` ti 
						ON tm.name=ti.parent 
						WHERE tm.status in ('On Going', 'Created')
					""", as_dict=True)
		
		for td in self.trainer_details:
			for t in trainer:
				if self.name != t.name: 
					if(t.trainer_id == td.trainer_id):
						frappe.throw(_("At Row {0} Trainer with ID: {1} is already enrolled in training {2} teaching ({3}) till {4}.").format(td.idx, t.trainer_id, t.name, t.course_cost_center, t.training_end_date))

	def validate_desuup_course(self):
		trainee = frappe.db.sql("""
			SELECT
				td.desuup_id, tm.name, tm.training_end_date, tm.course_cost_center
			FROM `tabTraining Management` tm inner join `tabTrainee Details` td 
			ON tm.name=td.parent 
			WHERE tm.status in ('On Going', 'Created')
		""", as_dict=True)
				
		for td in self.trainee_details:
			for t in trainee:
				if self.name != t.name: 
					if(t.desuup_id == td.desuup_id):
						frappe.throw(_("At Row {0} Desuup with ID: {1} is already enrolled in training {2} taking ({3}) as it's course till {4}.").format(td.idx, t.desuup_id, t.name, t.course_cost_center, t.training_end_date))

	def check_cohort_batch(self):
		for a in frappe.db.sql("""
				SELECT tm.cohort_batch, tm.training_center, tm.programme, tm.course
				FROM `tabTraining Management` tm
				WHERE tm.domain = '{}' and tm.course_cost_center = '{}' 
				and  tm.status in ('On Going', 'Created', 'Completed')
				and name != '{}'
			""".format(self.domain, self.course_cost_center, self.name), as_dict=True):

			if self.cohort_batch == a.cohort_batch:
				frappe.throw(_("Cohort Batch " + "{} " + "is being used in Domain: '{}' under Course: '{}'").format(a.cohort, a.domain, a.course_cost_center))

	def on_submit(self):

		for item in self.trainer_details:
			trainer = frappe.get_doc("Employee", item.trainer_id)
			trainer_history = {}
			trainer_history['course'] = self.course_cost_center
			trainer_history['course_duration'] = self.course_duration
			trainer_history['start_date'] = self.training_start_date
			trainer_history['end_date'] = self.training_end_date
			trainer_history['cohort_batch'] = self.cohort
			trainer_history['training_ref'] = self.name
			trainer.append("trainer_history", trainer_history)
			trainer.save()
	
		for item in self.trainee_details:
			trainee = frappe.get_doc("Desuup", item.desuup_id)
			training_history = {}
			training_history['training_attended'] = self.course_cost_center
			training_history['course_duration'] = self.course_duration
			training_history['start_date'] = self.training_start_date
			training_history['end_date'] = self.training_end_date
			training_history['cohort_batch'] = self.cohort
			training_history['training_ref'] = self.name
			training_history['joining_date'] = item.reporting_date
			trainee.append("training_history", training_history)
			trainee.save() 

	def on_cancel(self):
		frappe.db.sql("delete from `tabTrainer History` where training_ref = '{}'".format(self.name))
		frappe.db.sql("delete from `tabTrainee History` where training_ref = '{}'".format(self.name))
		frappe.db.sql("update `tabTraining Management` set status = 'Cancelled' where name = '{}'".format(self.name))

@frappe.whitelist()
def set_status():
	# transaction = frappe.db.sql("select name from `tabTraining Management` where status in ('Created', 'On Going') and docstatus != 2 and name = '{}'".format(str(doc_name)), as_dict=True)
	transaction = frappe.db.sql("select name from `tabTraining Management` where status in ('Created', 'On Going') and docstatus != 2 ", as_dict=True)
	for t in transaction:
		doc = frappe.get_doc("Training Management", t.name)
		if(datetime.strptime(str(doc.training_start_date),"%Y-%m-%d") <= datetime.strptime(nowdate(),"%Y-%m-%d") and doc.status == "Created"):
			doc.status = "On Going"
			doc.save(ignore_permissions = 1)
		elif(datetime.strptime(str(doc.training_end_date),"%Y-%m-%d") < datetime.strptime(nowdate(),"%Y-%m-%d") and doc.status == "On Going"):
			doc.status = "Completed"
			doc.save(ignore_permissions = 1)
			doc.submit()
			frappe.db.set_value("Training Management", t.name, "docstatus","1")

def get_permission_query_conditions(user):
	if not user: user = frappe.session.user
	user_roles = frappe.get_roles(user)
	if "Training User" in user_roles or "Training Manager" in user_roles or "System Manager" in user_roles:
		return
	else:
		return """(
			exists(select 1
				from `tabTraining Center` as t, `tabLaison Officer` as l
				where t.name = l.parent 
				and t.name = `tabTraining Management`.training_center
				and l.user = '{user}')
		)""".format(user=user)

def has_record_permission(doc, user):
	if not user: user = frappe.session.user
	user_roles = frappe.get_roles(user)

	if "Training User" in user_roles or "Training Manager" in user_roles or "System Manager" in user_roles:
		return True
	else:
		if frappe.db.exists("Laison Officer", {"parent":doc.training_center, "user": user}):
			return True
		else:
			return False 