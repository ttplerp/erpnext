# -*- coding: utf-8 -*-
# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import _
from frappe.model.mapper import get_mapped_doc
from erpnext.custom_workflow import validate_workflow_states, notify_workflow_states

class PMSAppeal(Document):
	def validate(self):
		# validate_workflow_states(self)
		self.check_value_length()
		self.check_duplicate_entry()
		self.set_perc_approver()

	def set_perc_approver(self):
		approver = frappe.db.get_single_value("HR Settings","appeal")
		approver_name = frappe.db.get_single_value("HR Settings","approver_name")
		self.db_set("approver", approver)
		self.db_set("approver_name", approver_name)
	
	def check_value_length(self):
		if not self.form_i and not self.form_ii:
			frappe.throw(_('You need to enter relevant values in Form I and Form II'))

	def check_duplicate_entry(self):       
		# check duplicate entry for particular employee
		if len(frappe.db.get_list('PMS Appeal',filters={'employee': self.employee, 'pms_calendar': self.pms_calendar, 'docstatus': 1})) > 2:
			frappe.throw("You cannot set more than <b>2</b> Appeal for PMS Calendar <b>{}</b>".format(self.pms_calendar))
		
		if frappe.db.get_list('PMS Appeal',filters={'employee': self.employee, 'pms_calendar': self.pms_calendar, 'docstatus': 1, 'appeal_based_on':self.appeal_based_on}):
			frappe.throw("You cannot set more than <b>1</b> PMS Appeal for PMS Calendar <b>{}</b> for Performance Evaluation <b>{}</b>".format(self.pms_calendar, self.appeal_based_on))

		if frappe.db.exists("PMS Appeal", {'employee': self.employee, 'pms_calendar': self.pms_calendar, 'docstatus': 1}):
			frappe.throw(_('You have already set the Appeal for PMS Calendar <b>{}</b>'.format(self.pms_calendar))) 

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
