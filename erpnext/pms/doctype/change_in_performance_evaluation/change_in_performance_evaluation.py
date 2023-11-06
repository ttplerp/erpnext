# -*- coding: utf-8 -*-
# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc

class ChangeInPerformanceEvaluation(Document):
	def on_submit(self):
		self.send_mail()
		self.update_target()

	def update_target(self):
		# frappe.throw("test")
		if self.current_target:
			doc = frappe.get_doc('Target Set Up',self.current_target)
			# doc.have_double_pms = 1
			doc.reason = self.reason
			doc.reference = self.name
			doc.save(ignore_permissions = True)

			review = frappe.db.get_value('Review',{'target':self.current_target,'docstatus':('<',2)},['name'])
			if not review:
				return
			rev_doc = frappe.get_doc('Review',review)
			# rev_doc.have_double_pms = 1
			rev_doc.reason = self.reason
			rev_doc.reference = self.name
			rev_doc.save(ignore_permissions=True)

			evaluation = frappe.db.get_value('Performance Evaluation',{'review':review,'docstatus':('<',2)},['name'])
			if not evaluation :
				return
			eval_doc = frappe.get_doc('Performance Evaluation',evaluation)
			# eval_doc.have_double_pms = 1
			eval_doc.reason = self.reason
			eval_doc.reference = self.name
			eval_doc.save(ignore_permissions = True)
		else:
			evaluation = frappe.db.get_value('Performance Evaluation',{'employee':self.employee,'pms_calendar': self.fiscal_year},['name'])
			if not evaluation :
				return
			eval_doc = frappe.get_doc('Performance Evaluation',evaluation)
			# eval_doc.have_double_pms = 1
			eval_doc.reason = self.reason
			eval_doc.reference = self.name
			eval_doc.save(ignore_permissions = True)

	def send_mail(self):
		return
		recipient = []
		user = frappe.db.get_values("Employee",self.employee,["user_id"])
		recipient.append(user)
		subject = ''
		message = ''
		try:
			frappe.sendmail(
				recipients=recipients,
				subject=_(subject),
				message= _(message)
			)
		except:
			pass

def get_permission_query_conditions(user):
	# restrict user from accessing this doctype    
	if not user: user = frappe.session.user     
	user_roles = frappe.get_roles(user)

	if user == "Administrator":      
		return
	if "HR User" in user_roles or "HR Manager" in user_roles:       
		return

	return """(
		`tabChange In Performance Evaluation`.owner = '{user}'
		or
		exists(select 1
				from `tabEmployee`
				where `tabEmployee`.name = `tabChange In Performance Evaluation`.employee
				and `tabEmployee`.user_id = '{user}')
		)""".format(user=user)

@frappe.whitelist()
def create_target(source_name, target_doc=None):
	doclist = get_mapped_doc("Change In Performance Evaluation", source_name, {
		"Change In Performance Evaluation": {
			"doctype": "Target Set Up",
            "field_map":{
					"reference":"name",
					"pms_calendar":"fiscal_year",
				},
		},
	}, target_doc)

	return doclist