# -*- coding: utf-8 -*-
# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt
# developed by Birendra on 01/02/2021
from __future__ import unicode_literals
import frappe
import urllib.parse
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt,nowdate
from frappe.model.mapper import get_mapped_doc
from erpnext.custom_workflow import validate_workflow_states, notify_workflow_states

class TargetSetUp(Document):
	def validate(self):
		self.load_pre_requirement()
		self.check_target()
		self.check_duplicate_entry() 
		validate_workflow_states(self) 
		if self.workflow_state != "Approved":
			notify_workflow_states(self)
		if self.reference and self.reason:
			return
		else:  
			self.validate_calendar()
			
	def on_submit(self):
		if self.reference and self.reason:
			return
		else:
			self.validate_calendar()

	def load_pre_requirement(self):
		doc = frappe.get_doc("PMS Setting")
		self.max_weightage_for_target = doc.max_weightage_for_target
		self.max_no_of_target = doc.max_no_of_target
		self.min_weightage_for_target = doc.min_weightage_for_target
		self.min_no_of_target = doc.min_no_of_target

	def on_update_after_submit(self):
		self.check_target()
		review = frappe.db.get_value('Review',{'target':self.name,'docstatus':('!=',2)},['name'])
		if not review:
			return
		rev_doc = frappe.get_doc('Review',review)
		for r, t in zip(rev_doc.review_target_item,self.target_item):
			r.quantity = t.quantity
			r.quality = t.quality
			r.timeline = t.timeline
			r.qty_quality = t.qty_quality
			r.timeline_base_on = t.timeline_base_on
		
		rev_doc.save(ignore_permissions=True)

		evaluation = frappe.db.get_value('Performance Evaluation',{'review':review,'docstatus':('<',2)},['name'])
		if not evaluation :
			return
		eval_doc = frappe.get_doc('Performance Evaluation',evaluation)
			
		for e, t in zip(eval_doc.evaluate_target_item,self.target_item):
			e.quantity = t.quantity
			e.quality = t.quality
			e.timeline = t.timeline
			e.timeline_base_on = t.timeline_base_on
			e.qty_quality = t.qty_quality
		eval_doc.save(ignore_permissions = True)
		
	def validate_calendar(self):
		if frappe.db.exists("Target Set Up", {"employee": self.employee, "docstatus":2, "pms_calendar": self.pms_calendar}):
			doc = frappe.get_doc('Target Set Up', self.amended_from)
			if self.pms_calendar == doc.pms_calendar:
				return
			else:
				frappe.throw(_("PMS Calendar doesnot match with the cancelled Target"))

		elif self.workflow_state == 'Draft' or self.workflow_state == 'Rejected':
			return   
		# check whether pms is active for target setup       
		elif not frappe.db.exists("PMS Calendar",{"name": self.pms_calendar, "docstatus": 1,
					"target_start_date":("<=",nowdate()),"target_end_date":(">=",nowdate())}):
			frappe.throw(_('Target Set Up for PMS Calendar <b>{}</b> is not open').format(self.pms_calendar))

	def check_duplicate_entry(self):
		# check duplicate entry for particular employee
		if self.reference and len(frappe.db.get_list('Target Set Up',filters={'employee': self.employee, 'pms_calendar': self.pms_calendar, 'docstatus': 1,'reference':self.reference})) >= 2 :
			frappe.throw("You cannot set more than <b>2</b> Target Set Up for PMS Calendar <b>{}</b>".format(self.pms_calendar))
		
		if self.reference and len(frappe.db.get_list('Target Set Up',filters={'employee': self.employee, 'pms_calendar': self.pms_calendar, 'docstatus': 1,'reference':self.reference,'section':self.section})) >= 2:
			frappe.throw("You cannot set more than <b>2</b> Target Set Up for PMS Calendar <b>{}</b> within Section <b>{}</b>".format(self.pms_calendar,self.section))

		if not self.reference and frappe.db.exists("Target Set Up", {'employee': self.employee, 'pms_calendar': self.pms_calendar, 'docstatus': 1}):
			frappe.throw(_('You have already set the Target for PMS Calendar <b>{}</b> or Route from <b><a href="#List/Change In Performance Evaluation/List">Change In Performance Evaluation</a></b> if you have 2 PMS'.format(self.pms_calendar)))

	def check_target(self):
		check = frappe.db.get_value("PMS Group",self.pms_group,"required_to_set_target")
		if not check:
			frappe.throw(
					title='Error',
					msg="You are not required to set Target")
		else:
			if not self.target_item:
				frappe.throw(_('You need to <b>Set The Target</b>'))

			# validate total number of target
			target_length = flt(len(self.target_item)) + flt(len(self.common_target))
			if flt(target_length) > flt(self.max_no_of_target) or flt(target_length) < flt(self.min_no_of_target):
				frappe.throw(
					title='Error',
					msg="Total number of target must be between <b>{}</b> and <b>{}</b> but you have set only <b>{}</b> target".format(self.min_no_of_target,self.max_no_of_target,target_length))

			total_target_weightage = 0
			# total weightage must be 100
			for i, t in enumerate(self.target_item):
				if t.qty_quality == 'Quantity' and flt(t.quantity) <= 0 :
					frappe.throw(
						title=_('Error'),
						msg=_("<b>{}</b> value is not allowed for <b>Quantity</b> in Target Item at Row <b>{}</b>".format(t.quantity,i+1)))

				if t.qty_quality == 'Quality' and flt(t.quality) <= 0 :
					frappe.throw(
						title=_("Error"),
						msg=_("<b>{}</b> value is not allowed for <b>Quality</b> in Target Item at Row <b>{}</b>".format(t.quality,i+1)))

				if flt(t.weightage) > flt(self.max_weightage_for_target) or flt(t.weightage) < flt(self.min_weightage_for_target):
					frappe.throw(
						title=_('Error'),
						msg="Weightage for target must be between <b>{}</b> and <b>{}</b> but you have set <b>{}</b> at row <b>{}</b>".format(self.min_weightage_for_target,self.max_weightage_for_target,t.weightage, i+1))

				if flt(t.timeline) <= 0:
					frappe.throw(
						title=_("Error"),
						msg=_("<b>{}</b> value is not allowed for <b>Timeline</b> in Target Item at Row <b>{}</b>".format(t.timeline,i+1)))
				
				total_target_weightage += flt(t.weightage)
				if t.qty_quality == 'Quantity':
					t.quality = None

				if t.qty_quality == 'Quality':
					t.quantity = None
			for item in self.common_target:
				total_target_weightage += flt(item.weightage)

			if flt(total_target_weightage) != 100:
				frappe.throw(
					title=_("Error"),
					msg=_('Sum of Weightage for Target must be 100 but your total weightage is <b>{}</b>'.format(total_target_weightage)))

			self.total_weightage = total_target_weightage
		
	def get_supervisor_id(self):
		# get supervisor details         
		reports_to = frappe.db.get_value("Employee",{"name":self.employee},"reports_to")
		if not reports_to:
			frappe.throw('You have not set report to in your master data')
		email,name, designation = frappe.db.get_value("Employee",{"name":reports_to},["user_id","employee_name","designation"])
		if not email:
			frappe.throw('Your supervisor <b>{}</b> email not found in Employee Master Data, please contact your HR'.format(name))
		self.approver = email
		self.approver_name = name
		self.approver_designation = designation
	@frappe.whitelist()
	def calculate_total_weightage(self):
		total = 0
		for item in self.target_item :
			total += flt(item.weightage)
		for item in self.common_target:
			total += flt(item.weightage)
		self.total_weightage = total
	
	def set_approver_designation(self):
		desig = frappe.db.get_value('Employee', {'user_id': self.approver}, 'designation')
		return desig
 
@frappe.whitelist()
def create_review(source_name, target_doc=None):
	if frappe.db.exists('Review',
		{'target':source_name,
		'docstatus':('=',1)
		}):
		frappe.throw(
			title='Error',
			msg="You have already created Review for this Target")
	doclist = get_mapped_doc("Target Set Up", source_name, {
		"Target Set Up": {
			"doctype": "Review",
			"field_map":{
					"target":"name"
				},
			},
		"Common Target Item":{
				"doctype":"Review Target Item"
			},
		"Performance Target Evaluation":{
				"doctype":"Review Target Item"
			},
		"Negative Target":{
			"doctype":"Negative Target Review"
			},
	}, target_doc)

	return doclist

@frappe.whitelist()
def apply_target_filter(doctype, txt, searchfield, start, page_len, filters):
	cond = " parent = '{}' ".format(filters['parent'])
	return frappe.db.sql("""select name, performance_target from `tabCommon Target Details`
			where {cond}
			AND (`{key}` LIKE %(txt)s OR performance_target LIKE %(txt)s )
			order by name limit %(start)s, %(page_len)s"""
			.format(key=searchfield, cond = cond), {
				'txt': '%' + txt + '%',
				'start': start, 'page_len': page_len
			})

@frappe.whitelist()
def manual_approval_for_hr(name, employee, pms_calendar):
	frappe.db.sql("update `tabTarget Set Up` set workflow_state = 'Approved', docstatus = 1 where employee = '{0}' and pms_calendar = '{1}' and name = '{2}' and workflow_state = 'Waiting Approval'".format(employee, pms_calendar, name))
	frappe.msgprint("Document has been Approved")

def get_permission_query_conditions(user):
	# restrict user from accessing this doctype    
	if not user: user = frappe.session.user     
	user_roles = frappe.get_roles(user)

	if user == "Administrator":      
		return
	if "HR Master" in user_roles or "HR Manager" in user_roles:       
		return
	return """(
		`tabTarget Set Up`.owner = '{user}'
		or
		exists(select 1
				from `tabEmployee`
				where `tabEmployee`.name = `tabTarget Set Up`.employee
				and `tabEmployee`.user_id = '{user}')
		or
		(`tabTarget Set Up`.approver = '{user}' and `tabTarget Set Up`.workflow_state not in ('Draft', 'Rejected','Cancelled'))
	)""".format(user=user)