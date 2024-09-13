# -*- coding: utf-8 -*-
# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import flt,nowdate, cint, getdate
from frappe.model.mapper import get_mapped_doc
from erpnext.custom_workflow import validate_workflow_states, notify_workflow_states

class PMSAppeal(Document):
	def validate(self):
		self.set_reference()
		self.calculate_target_score()
		self.calculate_competency_score()
		self.calculate_negative_score()
		self.calculate_final_score()
		validate_workflow_states(self)
		if self.workflow_state != "Approved":
			notify_workflow_states(self)
		# Validate appeal dates
		self.validate_appeal_period()	
	def on_submit(self):
		self.employee_pms_record()
	def on_cancel(self):
		self.set_reference(cancel=True)
		self.update_employee_master()

	def set_perc_approver(self):
		approver = frappe.db.get_single_value("HR Settings","appeal")
		approver_name = frappe.db.get_single_value("HR Settings","approver_name")
		self.db_set("approver", approver)
		self.db_set("approver_name", approver_name)
	def set_reference(self, cancel=False):
		if self.reference:
			if not cancel:
				frappe.db.set_value("Performance Evaluation",self.reference,"reference",self.name)
			else:
				frappe.db.set_value("Performance Evaluation",self.reference,"reference","")


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
				# if item.quantity_achieved <= 0:
				# 	frappe.throw('Quality Achieved for target <b>{}</b> must be greater than or equal to 0'.format(item.performance_target))
				
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
	def calculate_negative_score(self):
		if not self.negative_target:
			pass
		else:
			total=0
			for row in self.business_target:
				total += flt(row.supervisor_rating)
			self.negative_rating = flt(total)
			self.db_set('negative_rating', self.negative_rating)

	def calculate_final_score(self):
		self.target_total_weightage, self.competency_total_weightage = frappe.db.get_value('PMS Group', {'name':self.pms_group}, ['weightage_for_target', 'weightage_for_competency'])
		self.db_set('form_i_score', flt(self.form_i_total_rating))
		self.db_set('form_ii_score', flt(self.form_ii_total_rating))
		self.db_set('form_iii_score',flt(self.negative_rating))
		self.db_set('final_score', flt(self.form_i_score) + flt(self.form_ii_score)+ flt(self.form_iii_score))
		self.db_set('final_score_percent', flt(self.final_score))
		self.overall_rating = frappe.db.sql('''select name from `tabOverall Rating` where  upper_range_percent >= {0} and lower_range_percent <= {0}'''.format(self.final_score_percent))[0][0]
		self.db_set('overall_rating', self.overall_rating)
		
	def update_employee_master(self):
		doc = frappe.db.get_value("Employee PMS Rating",{"performance_evaluation":self.name},"name")
		if doc:
			frappe.delete_doc("Employee PMS Rating",doc)
		else:
			frappe.msgprint("""No PMS Appeal record found in Employee Master Data of employee <a href= "#Form/Employee/{0}">{0}</a>""".format(self.employee))
		final_score = frappe.db.get_value("Performance Evaluation",self.reference,"final_score")
		final_score_percent = frappe.db.get_value("Performance Evaluation",self.reference,"final_score_percent")
		overall_rating = frappe.db.get_value("Performance Evaluation",self.reference,"overall_rating")
		
		emp = frappe.get_doc("Employee",self.employee)
		row = emp.append("employee_pms",{})
		row.fiscal_year = self.pms_calendar
		row.final_score = final_score
		row.final_score_percent = final_score_percent
		row.overall_rating = overall_rating
		row.reference_type = 'Performance Evaluation'
		row.performance_evaluation = self.reference
		emp.save(ignore_permissions=True)
		frappe.msgprint("""Performance Evaluation record Updated in Employee Master Data of employee <a href= "#Form/Employee/{0}">{0}</a>""".format(self.employee))
	def employee_pms_record(self):
		if self.reference:
			doc = frappe.db.get_value("Employee PMS Rating",{"performance_evaluation":self.reference},"name")
			if doc:
				frappe.delete_doc("Employee PMS Rating",doc)
			else:
				frappe.msgprint("""No PMS record found in Employee Master Data of employee <a href= "#Form/Employee/{0}">{0}</a>""".format(self.employee))
		emp = frappe.get_doc("Employee",self.employee)
		row = emp.append("employee_pms",{})
		row.fiscal_year = self.pms_calendar
		row.final_score = self.final_score
		row.final_score_percent = self.final_score_percent
		row.overall_rating = self.overall_rating
		row.reference_type = 'PMS Appeal'
		row.performance_evaluation = self.name
		emp.save(ignore_permissions=True)
		frappe.msgprint("""PMS Appeal record Updated in Employee Master Data of employee <a href= "#Form/Employee/{0}">{0}</a>""".format(self.employee))

	def validate_appeal_period(self):
		"""Validates if the PMS appeal is submitted within the appeal period."""
		pms_calendar = frappe.get_value("PMS Calendar", self.pms_calendar, ["appeal_start_date", "appeal_end_date"])
		if not pms_calendar:
			frappe.throw(_("PMS Calendar not found for employee {0}".format(self.employee)))
		appeal_start_date, appeal_end_date = pms_calendar
		today = nowdate()
		if not is_date_within_range(getdate(today), getdate(appeal_start_date), getdate(appeal_end_date)):
			frappe.throw(_("PMS appeal period for employee {0} has ended. Appeals can only be submitted between {1} and {2}.".format(self.employee, appeal_start_date, appeal_end_date)))

def is_date_within_range(date, start_date, end_date):
	"""Checks if a given date is within a specified range."""
	return start_date <= date <= end_date


def get_permission_query_conditions(user):
	# restrict user from accessing this doctype if not the owner
	if not user: user = frappe.session.user
	user_roles = frappe.get_roles(user)

	if user == "Administrator":
		return
	if "HR User" in user_roles or "HR Manager" in user_roles or "CEO" in user_roles or "PERC Member" in user_roles:
		return

	return """(
		`tabPMS Appeal`.owner = '{user}'
		or
		exists(select 1
				from `tabEmployee`
				where `tabEmployee`.name = `tabPMS Appeal`.employee
				and `tabEmployee`.user_id = '{user}')
	)""".format(user=user)
