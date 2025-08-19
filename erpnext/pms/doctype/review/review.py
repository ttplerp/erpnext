# -*- coding: utf-8 -*-
# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt
# developed by Birendra on 15/02/2021

from __future__ import unicode_literals
from frappe import _
import frappe
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from frappe.utils import flt, nowdate
from erpnext.custom_workflow import validate_workflow_states, notify_workflow_states

class Review(Document):
	def validate(self):
		self.check_duplicate_entry()
		validate_workflow_states(self)
		self.check_target()

	def on_submit(self):
		if self.reference and self.reason:
			return
		# else:
			# self.validate_calendar()
	
	def validate_calendar(self): 
		# check whether pms is active for review
		if not frappe.db.exists("PMS Calendar",{"name": self.pms_calendar,"docstatus": 1,
					"review_start_date":("<=",nowdate()),"review_end_date":(">=",nowdate())}):
			frappe.throw(_('Review for PMS Calendar <b>{}</b> is not open please check your posting date').format(self.pms_calendar))

	def check_duplicate_entry(self):       
		# check duplicate entry for particular employee
		if self.reference and len(frappe.db.get_list('Review',filters={'employee': self.employee, 'pms_calendar': self.pms_calendar, 'docstatus': 1,'reference':self.reference})) > 2:
			frappe.throw("You cannot set more than <b>2</b> Review for PMS Calendar <b>{}</b>".format(self.pms_calendar))
		
		if self.reference and frappe.db.get_list('Review',filters={'employee': self.employee, 'pms_calendar': self.pms_calendar, 'docstatus': 1,'reference':self.reference,'target':self.target}):
			frappe.throw("You cannot set more than <b>1</b> Review for PMS Calendar <b>{}</b> for Target <b>{}</b>".format(self.pms_calendar, self.target))

		if not self.reference and frappe.db.exists("Review", {'employee': self.employee, 'pms_calendar': self.pms_calendar, 'docstatus': 1}):
				frappe.throw(_('You have already set the Review for PMS Calendar <b>{}</b>'.format(self.pms_calendar)))

	def check_target(self):
		# validate target
		if self.required_to_set_target:
			if not self.review_target_item:
				frappe.throw(_('You need to <b>Get The Target</b>'))

	def set_approver_designation(self):
		desig = frappe.db.get_value('Employee', {'user_id': self.approver}, 'designation')
		return desig

def get_permission_query_conditions(user):
	# restrick user from accessing this doctype
	if not user: user = frappe.session.user
	user_roles = frappe.get_roles(user)

	if user == "Administrator":
		return
	if "HR User" in user_roles or "HR Manager" in user_roles:
		return

	return """(
		`tabReview`.owner = '{user}'
		or
		exists(select 1
				from `tabEmployee`
				where `tabEmployee`.name = `tabReview`.employee
				and `tabEmployee`.user_id = '{user}')
		or
		(`tabReview`.approver = '{user}' and `tabReview`.workflow_state not in ('Draft', 'Rejected'))
	)""".format(user=user)
 
@frappe.whitelist()
def create_evaluation(source_name, target_doc=None):
	if frappe.db.exists('Performance Evaluation',
		{'review':source_name,
		'docstatus':('!=',2)
		}):
		frappe.throw(
			title='Error',
			msg="You have already created Evaluation for this Target")
	doclist = get_mapped_doc("Review", source_name, {
		"Review": {
			"doctype": "Performance Evaluation",
			"field_map":{
					"review":"name"
				},
		},
		"Review Target Item":{
			"doctype":"Evaluate Target Item"
		}
	}, target_doc)

	return doclist

@frappe.whitelist()
def manual_approval_for_hr(name, employee, pms_calendar):
	frappe.db.sql("update `tabReview` set rev_workflow_state = 'Approved', docstatus = 1 where employee = '{0}' and pms_calendar = '{1}' and name = '{2}' and rev_workflow_state = 'Waiting Approval'".format(employee, pms_calendar, name))
	frappe.msgprint("Document has been Approved")