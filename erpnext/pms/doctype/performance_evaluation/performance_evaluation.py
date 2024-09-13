# -*- coding: utf-8 -*-
# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt
# developed by Birendra on 01/03/2021

from __future__ import unicode_literals
from frappe import _
import frappe
from frappe.model.document import Document
from frappe.utils import flt,nowdate, cint
from frappe.model.mapper import get_mapped_doc
from erpnext.custom_workflow import validate_workflow_states, notify_workflow_states

class PerformanceEvaluation(Document):
	def validate(self):
		if self.upload_old_data:
			return 
		if self.workflow_state != frappe.db.get_value('Performance Evaluation',self.name,'workflow_state'): 
			validate_workflow_states(self)  
		self.set_dafault_values() 
		self.check_duplicate_entry()
		self.calculate_target_score()
		self.calculate_competency_score()
		self.calculate_negative_score()
		self.calculate_final_score()
		self.check_target()
		self.validate_no_months_served()
		if self.workflow_state != "Approved":
			notify_workflow_states(self)

		# to record the approver details when it is manually set to be used if the pms gets Rejected
		if self.workflow_state == "Waiting Supervisor Approval":
			# sup_user_id, sup_name = frappe.db.get_value(
			#     "Employee", {"user_id": self.approver}, ["user_id","first_name"]) or None
			self.approver_in_first_level = self.approver
			self.approver_fl_name = self.approver_name
			self.approver_fl_designation = self.approver_designation

	def on_submit(self):
		if self.upload_old_data:
			return
		if self.reference and self.reason:
			return
		else:  
			self.validate_calendar()

		#Added by Kinley Dorji for creating pms record in employee master
		self.create_employee_pms_record()
	
	def on_update_after_submit(self):
		if self.upload_old_data:
			return
		self.calculate_target_score()
		self.calculate_competency_score()
		self.calculate_negative_score()
		self.calculate_final_score()
		self.update_employee_pms_record() 

	def on_cancel(self):
		self.remove_employee_pms_record()        

	def set_dafault_values(self):
		self.max_rating_limit = frappe.db.get_single_value('PMS Setting','max_rating_limit')
	@frappe.whitelist()
	def create_employee_pms_record(self):
		if self.reference:
			return
		emp = frappe.get_doc("Employee",self.employee)
		row = emp.append("employee_pms",{})
		row.fiscal_year = self.pms_calendar
		row.final_score = self.final_score
		row.final_score_percent = self.final_score_percent
		row.overall_rating = self.overall_rating
		row.reference_type = 'Performance Evaluation'
		row.performance_evaluation = self.name
		emp.save(ignore_permissions=True)

	def remove_employee_pms_record(self):
		doc = frappe.db.get_value("Employee PMS Rating",{"performance_evaluation":self.name},"name")
		if doc:
			frappe.delete_doc("Employee PMS Rating",doc)
		else:
			frappe.msgprint("""No PMS record found in Employee Master Data of employee <a href= "#Form/Employee/{0}">{0}</a>""".format(self.employee))
	
	def update_employee_pms_record(self):
		doc = frappe.get_doc("Employee", self.employee)
		for d in doc.employee_pms:
			if d.fiscal_year == self.pms_calendar and d.performance_evaluation == self.name:
				d.final_score = self.final_score
				d.final_score_percent = self.final_score_percent
				d.overall_rating = self.overall_rating
		doc.save(ignore_permissions=True)
			
	# calculate score and average of target
	def calculate_target_score(self):
		total_score = 0
		for item in self.evaluate_target_item:
			quality_rating, quantity_rating, timeline_rating= 0, 0, 0
			if cint(item.reverse_formula) == 0:
				item.accept_zero_qtyquality = 0
			if item.timeline_achieved <= 0:
				frappe.throw('Timeline Achieved for target <b>{}</b> must be greater than 0'.format(item.performance_target))
			if item.qty_quality == 'Quality':
				if item.quality_achieved <= 0:
					frappe.throw('Quality Achieved for target <b>{}</b> must be greater than or equal to 0'.format(item.performance_target))

				if flt(item.quality_achieved) >= flt(item.quality):
					quality_rating = item.weightage

				else:
					quality_rating = flt(item.quality_achieved) / flt(item.quality) * flt(item.weightage)
				
				item.quality_rating = quality_rating

			elif item.qty_quality == 'Quantity':
				if item.quantity_achieved <= 0:
					frappe.throw('Quality Achieved for target <b>{}</b> must be greater than or equal to 0'.format(item.performance_target))
				
				if flt(item.quantity_achieved)>= flt(item.quantity):
					quantity_rating = flt(item.weightage)
				else:
					quantity_rating = flt(item.quantity_achieved) / flt(item.quantity)  * flt(item.weightage)
				
				item.quantity_rating = quantity_rating

			if flt(item.timeline_achieved)<= flt(item.timeline):
				timeline_rating = flt(item.weightage)
			else:
				timeline_rating = flt(item.timeline) / flt(item.timeline_achieved) *  flt(item.weightage)
			item.timeline_rating = timeline_rating
			
			if item.qty_quality == 'Quality':
				item.average_rating = (flt(item.timeline_rating) + flt(item.quality_rating)) / 2

			elif item.qty_quality == 'Quantity':
				item.average_rating = (flt(item.timeline_rating) + flt(item.quantity_rating)) / 2
			target_rating = frappe.db.get_value("PMS Group",self.pms_group,"weightage_for_target")
			item.score = (flt(item.average_rating ) / flt(item.weightage)) * 100

			total_score += flt(item.average_rating)

		""" Additional Achievement, 07/08/2024 """
		for k, a in enumerate(self.achievements_items):
			if a.supervisor_rating > a.weightage:
				frappe.throw("Rating for <b>Achievement</b> cannot be greater than weightage at Row <b>{}</b>".format(k+1))
			if  a.supervisor_rating == 0 and not a.comment and frappe.session.user == self.approver:
				frappe.throw("Give <b>Comment</b> for <b>Achievement</b>'s rating <b>0</b> at Row <b>{}</b>".format(k+1))
			total_score += a.supervisor_rating

		score =flt(total_score)/100 * flt(target_rating)
		total_score = score
		self.form_i_total_rating = total_score
		self.db_set('form_i_total_rating', self.form_i_total_rating)

	#calculate negative score
	def calculate_negative_score(self):
		if not self.negative_target:
			pass
		else:
			total=0
			for row in self.business_target:
				total += flt(row.supervisor_rating)
			self.negative_rating = flt(total)
			self.db_set('negative_rating', self.negative_rating)

	# calculate score and average of competency
	def calculate_competency_score(self):
		# if self.eval_workflow_state == 'Draft':
		#     return
		if not self.evaluate_competency_item:
			frappe.throw('Competency cannot be empty please use <b>Get Competency Button</b>')
		indx, total, count, total_score = 0,0,0,0
		for i, item in enumerate(self.evaluate_competency_item):
			if not item.is_parent and not item.achievement:
				frappe.throw('You need to rate competency at row <b>{}</b>'.format(i+1))
			# frappe.throw(str(self.evaluate_competency_item[indx].competency))
			if not item.is_parent and item.top_level == self.evaluate_competency_item[indx].competency:
				# frappe.throw(str(item.rating))
				tot_rating = flt(item.weightage_percent)/100 * flt(self.evaluate_competency_item[indx].weightage)
				total += tot_rating
				count += 1
				if i == len(self.evaluate_competency_item):
					indx = i
					
			elif i != indx and item.is_parent and item.top_level != self.evaluate_competency_item[indx].competency :
				self.evaluate_competency_item[indx].average = total / count
				self.evaluate_competency_item[indx].db_set('average',self.evaluate_competency_item[indx].average)
				self.evaluate_competency_item[indx].score = flt(self.evaluate_competency_item[indx].average)/ flt(self.evaluate_competency_item[indx].weightage) * 100
				self.evaluate_competency_item[indx].db_set('score',self.evaluate_competency_item[indx].score)
				total_score += flt(self.evaluate_competency_item[indx].average)
				indx, total, count = i,0,0

		self.evaluate_competency_item[indx].average = total / count
		self.evaluate_competency_item[indx].db_set('average',self.evaluate_competency_item[indx].average)
		self.evaluate_competency_item[indx].score = flt(self.evaluate_competency_item[indx].average)/ flt(self.evaluate_competency_item[indx].weightage) * 100
		self.evaluate_competency_item[indx].db_set('score',self.evaluate_competency_item[indx].score)
		competency_rating = frappe.db.get_value("PMS Group",self.pms_group,"weightage_for_competency")
		rating_ii = total_score + flt(self.evaluate_competency_item[indx].average)
		self.form_ii_total_rating = flt(competency_rating)/100 * flt(rating_ii)
		self.db_set('form_ii_total_rating', self.form_ii_total_rating)
	
	def calculate_final_score(self):
		self.target_total_weightage, self.competency_total_weightage = frappe.db.get_value('PMS Group', {'name':self.pms_group}, ['weightage_for_target', 'weightage_for_competency'])
		self.db_set('form_i_score', flt(self.form_i_total_rating))
		self.db_set('form_ii_score', flt(self.form_ii_total_rating))
		self.db_set('form_iii_score',flt(self.negative_rating))
		self.db_set('final_score', flt(self.form_i_score) + flt(self.form_ii_score)+ flt(self.form_iii_score))
		self.db_set('final_score_percent', flt(self.final_score))
		# frappe.throw(str(self.final_score_percent))
		self.overall_rating = frappe.db.sql('''select name from `tabOverall Rating` where  upper_range_percent >= {0} and lower_range_percent <= {0}'''.format(self.final_score_percent))[0][0]
		self.db_set('overall_rating', self.overall_rating)
		# self.star_obtained = frappe.db.get_value('Overall Rating',self.overall_rating,'star')
		# self.db_set('star_obtained', self.star_obtained)

	def validate_no_months_served(self):
	# sum of month served must be within 12 for those having two pms
		if self.reason in ['Change In Section/Division/Department','Transfer']:
			if flt(self.no_of_months_served) == 12:
				frappe.throw(title=_("Error"),
				msg=_("No. of month served cannot be <b>{}</b> as you will have Two PMS".format(self.no_of_months_served)))
			no_of_month_from_another_pms = frappe.db.get_value("Performance Evaluation",{'employee':self.employee,'pms_calendar':self.pms_calendar,'name':('!=',self.name),'docstatus':1},"no_of_months_served")
			
			if flt(self.no_of_months_served) + flt(no_of_month_from_another_pms) != 12 and no_of_month_from_another_pms:
				frappe.throw(title=_("Error"),
				msg=_("Sum of months served within 2 PMS must be <b>12</b> but your is <b>{}</b>".format(flt(self.no_of_months_served) + flt(no_of_month_from_another_pms))))

	def check_target(self):
		# validate target
		if flt(self.required_to_set_target) > 0:
			if not self.evaluate_target_item:
				frappe.throw(_('You need to <b>Get The Target</b>'))
		if not self.evaluate_competency_item:
			frappe.throw(_('You need to <b>Get The Competency</b>'))
			
	def validate_calendar(self):
		# check whether pms is active for target setup
		if not frappe.db.exists("PMS Calendar", {"name": self.pms_calendar, "docstatus": 1, "evaluation_start_date": ("<=", nowdate()), "evaluation_end_date": (">=", nowdate())}):
			frappe.throw(
				_('Evaluation for PMS Calendar <b>{}</b> is not open, Check the posting date').format(self.pms_calendar))

	def check_duplicate_entry(self):       
		# check duplicate entry for particular employee
		if len(frappe.db.get_list('Performance Evaluation',filters={'employee': self.employee, 'pms_calendar': self.pms_calendar, 'docstatus': 1})) > 2:
			frappe.throw("You cannot set more than <b>2</b> Evaluation for PMS Calendar <b>{}</b>".format(self.pms_calendar))
		
		if frappe.db.get_list('Performance Evaluation',filters={'employee': self.employee, 'pms_calendar': self.pms_calendar, 'docstatus': 1,'review':self.review}):
			frappe.throw("You cannot set more than <b>1</b> Performance Evaluation for PMS Calendar <b>{}</b> for Review <b>{}</b>".format(self.pms_calendar, self.review))

		if frappe.db.exists("Performance Evaluation", {'employee': self.employee, 'pms_calendar': self.pms_calendar, 'docstatus': 1}):
			frappe.throw(_('Evaluation for employee <b>{}</b> has been already approved for PMS Calendar <b>{}</b>'.format(self.employee_name, self.pms_calendar)), title="Duplicate Entry")

	def get_current_user(self):
		if frappe.session.user == "Administrator":
			return
		employee = frappe.db.get_value("Employee",{'user_id':frappe.session.user},"name")
		self.employee = employee

	def set_approver_designation(self):
		desig = frappe.db.get_value('Employee', {'user_id': self.approver}, 'designation')
		return desig
	@frappe.whitelist()
	def get_competency(self):
		if self.docstatus == 1:
			return
		# get competency applicable to particular category
		data = frappe.db.sql("""
			SELECT 
				name as parent, competency, weightage, is_parent
			FROM 
				`tabWork Competency` 
			WHERE `group` = '{}'
			ORDER BY 
				idx
		""".format(self.pms_group), as_dict=True)
		if not data:
			frappe.throw(_('There are no Work Competency defined'))

		# set competency item values
		self.set('evaluate_competency_item', [])
		for d in data:
			row = self.append('evaluate_competency_item', {})
			row.update(d)
			for item in frappe.db.sql('''
				SELECT sub_competency
				FROM `tabSub Competency`
				WHERE parent = '{}'
				ORDER BY idx
			'''.format(d.parent),as_dict = True):
				item['top_level'] = d.competency
				row = self.append('evaluate_competency_item', {})
				row.update(item)
	@frappe.whitelist()
	def get_additional_achievements(self):
		data = frappe.db.sql("""
			SELECT 
				aa.additional_achievements,
				aa.weightage,
				aa.appraisees_remarks,
				aa.own_initiativedirected,
				aa.appraisers_remarks
			FROM 
				`tabReview` r 
			INNER JOIN
				`tabAdditional Achievements` aa
			ON 
				r.name = aa.parent 
			WHERE
				r.employee = '{}' 
			AND
				r.docstatus = 1
			AND
				r.pms_calendar = '{}' AND r.review_type = 'Review IV'
			ORDER BY aa.idx
			""".format(self.employee, self.pms_calendar), as_dict=True)
		if data:
			self.set('achievements_items', [])
			for d in data:
				row = self.append('achievements_items', {})
				row.update(d)   
@frappe.whitelist()
def pms_appeal(source_name, target_doc=None):
	if frappe.db.exists('PMS Appeal',
		{'reference':source_name,
		'docstatus':('!=',2)
		}):
		frappe.throw(
			title='Error',
			msg="You have already created PMS Appeal for this Evaluation")
	doclist = get_mapped_doc("Performance Evaluation", source_name, {
		"Performance Evaluation": {
			"doctype": "PMS Appeal",
			"field_map":{
					"reference":"name"
				},
		},
		"Evaluate Target Item":{
			"doctype":"Evaluate Appeal Target Item"
		},
		"Evaluate Competency Item":{
			"doctype":"Evaluate Appeal Competency Item"
		},
		"Performance Evaluation Negative Target":{
			"doctype":"Performance Appeal Evaluation Negative Target"
		},
		"Evaluate Additional Achievements":{
			"doctype":"Appeal Additional Achievements"
		}
	}, target_doc)

	return doclist
@frappe.whitelist()
def set_perc_approver(perc):
	if perc == "Yes":
		approver = frappe.db.get_single_value("HR Settings","appeal")
	return approver

def get_permission_query_conditions(user):
	# restrict user from accessing this doctype
	if not user: user = frappe.session.user
	user_roles = frappe.get_roles(user)

	if user == "Administrator":
		return
	if "HR User" in user_roles or "HR Manager" in user_roles:
		return

	return """(
		`tabPerformance Evaluation`.owner = '{user}'
		or
		exists(select 1
				from `tabEmployee`
				where `tabEmployee`.name = `tabPerformance Evaluation`.employee
				and `tabEmployee`.user_id = '{user}')
		or
		(`tabPerformance Evaluation`.approver = '{user}' and `tabPerformance Evaluation`.workflow_state not in ('Draft', 'Rejected', 'Cancelled'))
		)""".format(user=user)

