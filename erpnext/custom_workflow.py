# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

'''
------------------------------------------------------------------------------------------------------------------------------------------
Version          Author         Ticket#           CreatedOn          ModifiedOn          Remarks
------------ --------------- --------------- ------------------ -------------------  -----------------------------------------------------
3.0               SHIV		                   28/01/2019                          Original Version
------------------------------------------------------------------------------------------------------------------------------------------                                                                          
'''

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import nowdate, cint, flt
# from erpnext.hr.doctype.approver_settings.approver_settings import get_final_approver
from hrms.hr.hr_custom_functions import get_officiating_employee
from frappe.utils.nestedset import get_ancestors_of

class CustomWorkflow:
	def __init__(self, doc):
		self.doc = doc
		self.old_state 		= self.doc.get_db_value("workflow_state")
		self.new_state 		= self.doc.workflow_state
		self.field_map 		= get_field_map()
		self.doc_approver	= self.field_map[self.doc.doctype]
		# if frappe.session.user == "Administrator":
		# 	frappe.throw(str(doc))
		self.field_list		= ["user_id","employee_name","designation","name"]
		if self.doc.doctype != "Material Request":
			self.employee		= frappe.db.get_value("Employee", self.doc.employee, self.field_list)
			self.reports_to		= frappe.db.get_value("Employee", frappe.db.get_value("Employee", self.doc.employee, "reports_to"), self.field_list)
			# self.hrm_approver	= frappe.db.get_value("Employee", frappe.db.get_single_value("HR Settings", "hrm_approver"), self.field_list)
			# self.hrd_approver	= frappe.db.get_value("Employee", frappe.db.get_single_value("HR Settings", "hrd_approver"), self.field_list)
			# self.ceo			= frappe.db.get_value("Employee", frappe.db.get_value("Employee", {"grade": "CEO", "status": "Active"}), self.field_list)
			# self.dept_approver	= frappe.db.get_value("Employee", frappe.db.get_value("Department", frappe.db.get_value("Employee", self.doc.employee, "department"), "approver"), self.field_list)
			# self.dir_approver	= frappe.db.get_value("Employee", frappe.db.get_value("Department", frappe.db.get_value("Department", frappe.db.get_value("Employee", self.doc.employee, "department"), "parent_department"),"approver"), self.field_list)
		self.login_user		= frappe.db.get_value("Employee", {"user_id": frappe.session.user}, self.field_list)
		#self.final_approver= frappe.db.get_value("Employee", {"user_id": get_final_approver(doc.branch)}, self.field_list)
		self.final_approver	= []

		if not self.login_user and frappe.session.user != "Administrator":
			frappe.throw("{0} is not added as the employee".format(frappe.session.user))

	def update_employment_status(self):
		emp_status = frappe.db.get_value("Leave Type", self.doc.leave_type, ["check_employment_status","employment_status"])
		if emp_status[0] and emp_status[1]:
			emp = frappe.get_doc("Employee", self.doc.employee)
			emp.employment_status = emp_status[1]
			emp.save(ignore_permissions=True)

	def set_approver(self, approver_type):
		if approver_type == "Supervisor":
			officiating = get_officiating_employee(self.reports_to[3])
			if officiating:
				officiating = frappe.db.get_value("Employee", officiating[0].officiate, self.field_list)
			vars(self.doc)[self.doc_approver[0]] = officiating[0] if officiating else self.reports_to[0]
			vars(self.doc)[self.doc_approver[1]] = officiating[1] if officiating else self.reports_to[1]
			vars(self.doc)[self.doc_approver[2]] = officiating[2] if officiating else self.reports_to[2]
		elif approver_type == "HRM":
			officiating = get_officiating_employee(self.hrm_approver[3])
			if officiating:
				officiating = frappe.db.get_value("Employee", officiating[0].officiate, self.field_list)
			vars(self.doc)[self.doc_approver[0]] = officiating[0] if officiating else self.hrm_approver[0]
			vars(self.doc)[self.doc_approver[1]] = officiating[1] if officiating else self.hrm_approver[1]
			vars(self.doc)[self.doc_approver[2]] = officiating[2] if officiating else self.hrm_approver[2]
		elif approver_type == "HRD":
			officiating = get_officiating_employee(self.hrd_approver[3])
			if officiating:
				officiating = frappe.db.get_value("Employee", officiating[0].officiate, self.field_list)
			vars(self.doc)[self.doc_approver[0]] = officiating[0] if officiating else self.hrd_approver[0]
			vars(self.doc)[self.doc_approver[1]] = officiating[1] if officiating else self.hrd_approver[1]
			vars(self.doc)[self.doc_approver[2]] = officiating[2] if officiating else self.hrd_approver[2]
		elif approver_type == "Department Head":
			officiating = get_officiating_employee(self.dept_approver[3])
			if officiating:
				officiating = frappe.db.get_value("Employee", officiating[0].officiate, self.field_list)
			vars(self.doc)[self.doc_approver[0]] = officiating[0] if officiating else self.dept_approver[0]
			vars(self.doc)[self.doc_approver[1]] = officiating[1] if officiating else self.dept_approver[1]
			vars(self.doc)[self.doc_approver[2]] = officiating[2] if officiating else self.dept_approver[2]
		elif approver_type == "Director":
			officiating = get_officiating_employee(self.dir_approver[3])
			if officiating:
				officiating = frappe.db.get_value("Employee", officiating[0].officiate, self.field_list)
			vars(self.doc)[self.doc_approver[0]] = officiating[0] if officiating else self.dir_approver[0]
			vars(self.doc)[self.doc_approver[1]] = officiating[1] if officiating else self.dir_approver[1]
			vars(self.doc)[self.doc_approver[2]] = officiating[2] if officiating else self.dir_approver[2]
		elif approver_type == "CEO":
			officiating = get_officiating_employee(self.ceo[3])
			if officiating:
				officiating = frappe.db.get_value("Employee", officiating[0].officiate, self.field_list)
			vars(self.doc)[self.doc_approver[0]] = officiating[0] if officiating else self.ceo[0]
			vars(self.doc)[self.doc_approver[1]] = officiating[1] if officiating else self.ceo[1]
			vars(self.doc)[self.doc_approver[2]] = officiating[2] if officiating else self.ceo[2]
		elif approver_type == "Final Approver":
			officiating = get_officiating_employee(self.final_approver[3])
			if officiating:
				officiating = frappe.db.get_value("Employee", officiating[0].officiate, self.field_list)
			vars(self.doc)[self.doc_approver[0]] = officiating[0] if officiating else self.final_approver[0]
			vars(self.doc)[self.doc_approver[1]] = officiating[1] if officiating else self.final_approver[1]
			vars(self.doc)[self.doc_approver[2]] = officiating[2] if officiating else self.final_approver[2]
		else:
			frappe.throw(_("Invalid approver type for Workflow"))


	def apply_workflow(self):
		if (self.doc.doctype not in self.field_map) or not frappe.db.exists("Workflow", {"document_type": self.doc.doctype, "is_active": 1}):
			return

		if self.doc.doctype == "Leave Application":
			self.leave_application()	
		elif self.doc.doctype == "Leave Encashment":
			self.leave_encashment()
		elif self.doc.doctype == "Salary Advance":
			self.salary_advance()
		elif self.doc.doctype == "Travel Authorization":
			self.travel_authorization()
		elif self.doc.doctype == "Travel Claim":
			self.travel_claim()
		elif self.doc.doctype == "Overtime Application":
			self.overtime_application()
		elif self.doc.doctype == "Material Request":
			self.material_request()		
		elif self.doc.doctype == "Festival Advance":
			self.festival_advance()
		elif self.doc.doctype == "Employee Transfer":
			self.employee_transfer()
		elif self.doc.doctype == "Employee Benefits":
			self.employee_benefits()
		elif self.doc.doctype == "Training Nomination":
			self.training_nomination()
		elif self.doc.doctype == "Training Approval Request":
			self.training_approval_request()
		elif self.doc.doctype == "Ad hoc Training Request":
			self.adhoc_training_request()
		elif self.doc.doctype == "SWS Application":
			self.sws_application()
		else:
			frappe.throw(_("Workflow not defined for {}").format(self.doc.doctype))

	def training_nomination(self):		
		if not self.old_state:     
			return
		elif self.old_state.lower() == "Draft".lower() and self.new_state.lower() != "Draft".lower():
			if self.doc.training_category == "Third Country" and self.doc.training_mode == "Regular":
				self.doc.workflow_state = "Waiting CEO Approval"
			elif self.doc.training_category == "India" and self.doc.training_mode == "Regular":
				self.doc.workflow_state = "Waiting Director, CA Approval"             
			elif self.doc.training_category == "Third Country" or self.doc.training_category == "India" or self.doc.is_professional_certificate == 1 and self.doc.training_mode == "Online":
				self.doc.workflow_state = "Waiting Director, CA Approval"  
					
			else:
				self.doc.workflow_state = "Waiting Chief, PCD Approval"

	def training_approval_request(self):		
		if not self.old_state:     
			return
		elif self.old_state.lower() == "Draft".lower() and self.new_state.lower() != "Draft".lower():
			if self.doc.training_category == "Third Country" and self.doc.is_professional != 1:
				self.doc.workflow_state = "Waiting CEO Approval"
			elif self.doc.training_category == "India" and self.doc.is_professional != 1:
				self.doc.workflow_state = "Waiting Director, CA Approval" 
			elif self.doc.is_professional == 1:
				self.doc.workflow_state = "Waiting Director, CA Approval"            
			# elif (self.doc.training_category == "Third Country" and self.doc.is_professional == 1)  or (self.doc.training_category == "India" or self.doc.is_professional == 1):
			#     self.doc.workflow_state = "Waiting Director, CA Approval" 
			else:
				self.doc.workflow_state = "Waiting Chief, PCD Approval"
	
	def adhoc_training_request(self):        
		if not self.old_state:     
			return
		elif self.old_state.lower() =="Waiting HR Approval".lower() and self.new_state.lower() != "Waiting HR Approval".lower():
			data = frappe.db.sql(""" 
								 SELECT i.training_category,i.training_mode
								 from `tabAd hoc Training Request` atr, `tabTraining Needs Assessment Item` i 
								 where atr.name=i.parent
								 and atr.name='{}' and atr.fiscal_year='{}'""".format(self.doc.name,self.doc.fiscal_year),as_dict=True)      
			if data[0].training_category == "Third Country" and data[0].training_mode == "Regular":
				self.doc.workflow_state = "Waiting CEO Approval"
			elif data[0].training_category == "India" and data[0].training_mode == "Regular":
				self.doc.workflow_state = "Waiting Director, CA Approval"
			elif data[0].training_category == "Third Country" or data[0].training_category == "India" or data[0].is_professional_certificate == 1 and data[0].training_mode == "Online":
				self.doc.workflow_state = "Waiting Director, CA Approval"
			else:
				self.doc.workflow_state = "Waiting Chief, PCD Approval"

	def leave_application(self):
		''' Leave Application Workflow
			1. Employee -> Supervisor
		'''
		if self.new_state.lower() in ("Draft".lower(), "Waiting Supervisor Approval".lower()):
			self.set_approver("Supervisor")
			if self.doc.owner != frappe.session.user:
				frappe.throw("Only <b>{}</b> can apply this Request".format(self.doc.employee_name))

		elif self.new_state.lower() == "Approved".lower():
			if self.doc.leave_approver != frappe.session.user:
				frappe.throw("Only {} can Approve this Application".format(self.doc.leave_approver_name))
			self.doc.status= "Approved"
			# self.update_employment_status()			
	
		elif self.new_state.lower() == 'Rejected'.lower():
			if self.doc.leave_approver != frappe.session.user:
				frappe.throw("Only <b>{}</b> can Reject this request".format(self.doc.leave_approver_name))
		elif self.new_state.lower() == "Cancelled".lower():
			if frappe.session.user not in (self.doc.supervisor, "Administrator"):
				frappe.throw(_("Only <b>{}</b> can Cancel this document.").format(self.doc.leave_approver_name))
			# self.doc.document_status = "Cancelled"

	def leave_encashment(self):
		''' Leave Encashment Workflow
			1. Employee -> HR
		'''
		if self.new_state.lower() in ("Draft".lower(), "Waiting HR Approval".lower()):
			self.set_approver("HRD")
		elif self.new_state.lower() == "Waiting HR Approval".lower():
			if self.doc.approver != frappe.session.user:
				frappe.throw("Only {} can Approve this Leave Encashment".format(self.doc.approver_name))
			self.set_approver("HRD")
		elif self.new_state.lower() == "Approved".lower():
			if self.doc.approver != frappe.session.user:
				frappe.throw("Only {} can Approve this Encashment".format(self.doc.approver_name))
		elif self.new_state.lower() in ('Rejected'):
			if self.doc.approver != frappe.session.user:
				frappe.throw("Only {} can Reject this Encashment".format(self.doc.approver_name))

	def salary_advance(self):
		''' Salary Advance Workflow
			1. Employee -> CEO -> HR
		'''
		if self.new_state.lower() in ("Draft".lower(), "Waiting CEO Approval".lower()):
			self.set_approver("CEO")
		elif self.new_state.lower() in ("Draft".lower(), "Waiting HR Approval".lower()):
			if self.doc.advance_approver != frappe.session.user:
				frappe.throw(_("Only {} can Approve this request").format(self.doc.advance_approver_name))
			self.set_approver("HRD")
		elif self.new_state.lower() == "Approved".lower():
			if self.doc.advance_approver != frappe.session.user:
				frappe.throw(_("Only {} can Approve this request").format(self.doc.advance_approver_name))		
		elif self.new_state.lower() == "Rejected":
			if self.doc.advance_approver != frappe.session.user:
				frappe.throw(_("Only {} can Reject this request").format(self.doc.advance_approver_name))		
		elif self.new_state.lower() == "Cancelled".lower():
			if frappe.session.user not in (self.doc.advance_approver,"Administrator"):
				frappe.throw(_("Only {} can Cancel this document.").format(self.doc.advance_approver_name))
	
	def travel_authorization(self):
		''' Travel Authorization Workflow
			1. Employee -> Supervisor
		'''
		if self.new_state.lower() in ("Draft".lower(), "Waiting Approval".lower()):
			self.set_approver("Supervisor")
			self.doc.document_status = "Draft"
		elif self.new_state.lower() == "Approved".lower():
			if self.doc.supervisor != frappe.session.user:
				frappe.throw("Only {} can Approve this request".format(self.doc.supervisor_name))
			self.doc.document_status = "Approved"
		elif self.new_state.lower() == 'Rejected'.lower():
			if self.doc.supervisor != frappe.session.user:
				frappe.throw("Only {} can Reject this request".format(self.doc.supervisor_name))
			self.doc.document_status = "Rejected"
		elif self.new_state.lower() == "Cancelled".lower():
			if frappe.session.user not in (doc.get(document_approver[0]),"Administrator"):
				frappe.throw(_("Only {} can Cancel this document.").format(self.doc.supervisor_name))
			self.doc.document_status = "Cancelled"

	def travel_claim(self):
		if self.new_state.lower() in ("Draft".lower(), "Waiting Supervisor Approval".lower()):
			self.set_approver("Supervisor")
		elif self.new_state.lower() == "Waiting HR Approval".lower():
			if self.doc.supervisor != frappe.session.user:
				frappe.throw("Only {} can Approve this request".format(self.doc.supervisor_name))
			self.set_approver("HRD")
			self.doc.supervisor_approval = 1
		elif self.new_state.lower() == "Claimed".lower():
			if self.doc.supervisor != frappe.session.user:
				frappe.throw("Only {} can Approve this request".format(self.doc.supervisor))
			self.doc.status = "Claimed"
			self.doc.hr_approval = 1
			self.doc.hr_approved_on = nowdate()
		elif self.new_state.lower() in ('Rejected'.lower(), 'Rejected By Supervisor'.lower()):
			if self.doc.supervisor != frappe.session.user:
				frappe.throw("Only {} can Reject this request".format(self.doc.supervisor))
			self.doc.status = "Rejected"
		elif self.new_state.lower() == "Cancelled".lower():
			if self.doc.supervisor != frappe.session.user:
				frappe.throw("Only {} can Cancel this request".format(self.doc.supervisor))

	def overtime_application(self):
		if self.new_state.lower() in ("Draft".lower(), "Waiting Supervisor Approval".lower()):
			self.set_approver("Supervisor")
		elif self.new_state.lower() == "Waiting Approval".lower():
			if self.doc.approver != frappe.session.user:
				frappe.throw("Only {} can Approve this request".format(self.doc.approver_name))
			self.set_approver("Department Head")
		elif self.new_state.lower() == "Approved".lower():
			if self.doc.approver != frappe.session.user:
				frappe.throw("Only {} can Approve this request".format(self.doc.approver_name))
		elif self.new_state.lower() in ('Rejected'.lower(), 'Rejected By Supervisor'.lower()):
			if self.doc.approver != frappe.session.user:
				frappe.throw("Only {} can Reject this request".format(self.doc.approver_name))
		elif self.new_state.lower() == "Cancelled".lower():
			if self.doc.approver != frappe.session.user:
				frappe.throw("Only {} can Cancel this request".format(self.doc.approver_name))

	def material_request(self):
		workflow_state    = self.new_state.lower()
		# to restrict Admin in creating MR
		# if not self.login_user: 
		#     frappe.throw("You do not have permission to create MR!")
		# owner        = frappe.db.get_value("Employee", {"user_id": self.doc.owner}, ["user_id","employee_name","designation","name"])
		# employee          = frappe.db.get_value("Employee", owner[3], ["user_id","employee_name","designation","name"])
		# reports_to        = frappe.db.get_value("Employee", frappe.db.get_value("Employee", owner[3], "reports_to"), ["user_id","employee_name","designation","name"])
		# frappe.throw(self.new_state.lower())
		if workflow_state == "Waiting For Verifier".lower() and workflow_state != self.old_state.lower():
			if (self.doc.owner != frappe.session.user) and "MR User" not in frappe.get_roles(self.doc.owner):
				frappe.throw("Only the creator of MR can Apply.")
					
		elif workflow_state == "Waiting For Approver".lower() and workflow_state != self.old_state.lower():
			# pmt = frappe.get_list("Program Management Team", filters={"parent":self.doc.cost_center}, fields=['pmt_user_id'])
			# if pmt:
			#     receipients = [a['pmt_user_id'] for a in pmt]
			#     frappe.throw(str(receipients))
			# pmt_user_id = frappe.db.sql("select pmt_user_id from `tabProgram Management Team` where parent='{}'".format(self.doc.cost_center), as_dict=1)
			pmt_user_id = frappe.db.sql("select p.user_id from `tabMR PMT And Domain Lead` p, `tabMR PMT List` a where a.parent=p.name and p.active = 1 and a.cost_center='{}'".format(self.doc.cost_center), as_dict=1)
			receipients = [a['user_id'] for a in pmt_user_id if frappe.db.get_value("User", a['user_id'], "enabled") == 1]
			# frappe.throw(str(receipients))
			if frappe.session.user not in receipients:
				frappe.throw("Only PMT Verifier for <b>{}</b> can Verify".format(self.doc.cost_center))

		elif workflow_state == "Approved".lower() and workflow_state != self.old_state.lower():
			# domain_lead = frappe.db.sql("select domain_lead_user_id from `tabDomain Lead` where parent='{}'".format(self.doc.cost_center), as_dict=1)
			domain_lead = frappe.db.sql("select p.user_id from `tabMR PMT And Domain Lead` p, `tabMR Domain List` a where a.parent=p.name and p.active = 1 and a.cost_center='{}'".format(self.doc.cost_center), as_dict=1)
			receipients = [a['user_id'] for a in domain_lead if frappe.db.get_value("User", a['user_id'], "enabled") == 1]
			if frappe.session.user not in receipients:
				frappe.throw("Only Domain Lead Approver for {} can Approve".format(self.doc.cost_center))

	def festival_advance(self):
		''' Leave Encashment Workflow
			1. Employee -> Supervisor -> HR
		'''
		if self.new_state.lower() in ("Draft".lower(), "Waiting Supervisor Approval".lower()):
			self.set_approver("Supervisor")
		elif self.new_state.lower() == "Waiting HR Approval".lower():
			if self.doc.advance_approver != frappe.session.user:
				frappe.throw("Only {} can Approve this Festival Advance".format(self.doc.advance_approver_name))
			self.set_approver("HRD")
		elif self.new_state.lower() == "Approved".lower():
			if self.doc.advance_approver != frappe.session.user:
				frappe.throw("Only {} can Approve the Festival Claim".format(self.doc.advance_approver_name))
		elif self.new_state.lower() in ('Rejected', 'Rejected By Supervisor'):
			if self.doc.advance_approver != frappe.session.user:
				frappe.throw("Only {} can Reject the Festival Advance".format(self.doc.advance_approver_name))

	def employee_benefits(self):
		workflow_state    = self.doc.get("workflow_state").lower()
		if workflow_state == "Draft".lower():
			# if doc.purpose == "Separation":
			if not "HR Manager" in frappe.get_roles(frappe.session.user):
				frappe.throw("Only HR user with role HR Manager can create the employee benefit with purpose Separation")


		elif workflow_state == "Waiting Approval".lower():
			# if doc.purpose == "Separation":
			officiating = get_officiating_employee(self.hrd_approver[3])

			if not officiating and not "HR Manager" in frappe.get_roles(frappe.session.user):
				frappe.throw("Only HR user with role HR Manager can create the employee benefit with purpose Separation")

		elif workflow_state == "Approved".lower():
			if self.doc.docstatus == 0 and self.doc.workflow_state == "Approved":
				self.doc.workflow_state == "Waiting Approval"
			if not "Chief PCD" in frappe.get_roles(frappe.session.user):
				frappe.throw(_("Only Chief PCD can approve this application").format(title="Invalid Operation"))
			vars(self.doc)[self.doc_approver[0]] = self.login_user[0]
			vars(self.doc)[self.doc_approver[1]] = self.login_user[1]
	
		elif workflow_state == "Rejected".lower():
			if not "Chief PCD" in frappe.get_roles(frappe.session.user):
				if workflow_state != self.doc.get_db_value("workflow_state"):
					frappe.throw(_("Only Cheif PCD can reject this application").format(title="Invalid Operation"))
		else:
			pass

	def employee_transfer(self):
		if self.doc.workflow_state == "Draft":
			# if not self.description or self.description == "":
			# 		frappe.throw("Please write a reason for transfer")
			if self.doc.transfer_type != 'Personal':
				if "HR Manager" not in frappe.get_roles(frappe.session.user):
					frappe.throw("Only HR Manager can apply for Management Transfer or Mutual Swipe")
			# frappe.throw(frappe.db.get_value("Employee",self.employee,"user_id"))
			else:
				if "HR Manager" in frappe.get_roles(frappe.session.user):
					frappe.throw("HR Manager can apply for Management Transfer or Mutual Swipe only")
				if frappe.session.user != frappe.db.get_value("Employee",self.doc.employee,"user_id"):
					frappe.throw("Only the selected employee {0} can apply for employee transfer".format(self.doc.employee))
			supervisor_id = frappe.db.get_value("Employee", self.doc.employee, "reports_to")
			self.doc.supervisor_name = frappe.db.get_value("Employee", supervisor_id, "employee_name")
			self.doc.supervisor_email = frappe.db.get_value("Employee", supervisor_id, "company_email")
			self.doc.supervisor = frappe.db.get_value("User", frappe.db.get_value("Employee", supervisor_id, "user_id"), "name")

		if self.doc.workflow_state == "Rejected":
			if not self.doc.rejection_reason:
				frappe.throw("Please input a rejection reason")

	def sws_application(self):
		if self.new_state.lower() in ("Draft".lower(), "Waiting Supervisor Approval".lower()):
			if not self.doc.verified and self.doc.approval_status == "Approved":
				frappe.throw("Can approve claim only after verification by supervisors")
			self.set_approver("Supervisor")
			try:
				eid = frappe.db.get_value("Employee",self.doc.employee,"user_id")
			except:
				frappe.throw("User ID not set for Employee '{0}'".format(self.doc.employee))
			if frappe.session.user != eid :
				frappe.throw("Only Selected Employee can apply for SWS Application")

		if self.new_state.lower() == "Waiting Supervisor Approval".lower():
			if not self.doc.verified and self.doc.approval_status == "Approved":
				frappe.throw("Can approve claim only after verification by supervisors")
	
		if self.new_state.lower() == "Waiting SWS User Approval".lower():
			if not self.doc.verified and self.doc.approval_status == "Approved":
				frappe.throw("Can approve claim only after verification by supervisors")

		if self.new_state.lower() == "Cancelled".lower():
			if not self.doc.verified and self.doc.approval_status == "Approved":
				frappe.throw("Can approve claim only after verification by supervisors")

		if self.new_state.lower() == "Verified".lower():
			self.doc.verified = 1
   
		if self.new_state.lower() =="Rejected".lower():
			self.doc.verified = 0
			self.doc.approval_status = "Rejected"
   
		if self.new_state.lower() =="Approved".lower():
			self.doc.approval_status = "Approved"

class NotifyCustomWorkflow:
	def __init__(self,doc):
		self.doc 			= doc
		self.old_state 		= self.doc.get_db_value("workflow_state")
		self.new_state 		= self.doc.workflow_state
		self.field_map 		= get_field_map()
		self.doc_approver	= self.field_map[self.doc.doctype]
		self.field_list		= ["user_id","employee_name","designation","name"]
		if self.doc.doctype != 'Material Request':
			self.employee		= frappe.db.get_value("Employee", self.doc.employee, self.field_list)
		self.login_user		= frappe.db.get_value("Employee", {"user_id": frappe.session.user}, self.field_list)

	def notify_employee(self):
		employee = frappe.get_doc("Employee", self.doc.employee)
		if not employee.user_id:
			return

		parent_doc = frappe.get_doc(self.doc.doctype, self.doc.name)
		args = parent_doc.as_dict()

		if self.doc.doctype == "Leave Application":
			template = frappe.db.get_single_value('HR Settings', 'leave_status_notification_template')
			if not template:
				frappe.msgprint(_("Please set default template for Leave Status Notification in HR Settings."))
				return
		elif self.doc.doctype == "Leave Encashment":
			template = frappe.db.get_single_value('HR Settings', 'encashment_status_notification_template')
			if not template:
				frappe.msgprint(_("Please set default template for Encashment Status Notification in HR Settings."))
				return
		elif self.doc.doctype == "Salary Advance":
			template = frappe.db.get_single_value('HR Settings', 'advance_status_notification_template')
			if not template:
				frappe.msgprint(_("Please set default template for Advance Status Notification in HR Settings."))
				return
		elif self.doc.doctype == "Travel Authorization":
			template = frappe.db.get_single_value('HR Settings', 'authorization_status_notification_template')
			if not template:
				frappe.msgprint(_("Please set default template for Authorization Status Notification in HR Settings."))
				return
		elif self.doc.doctype == "Travel Claim":
			template = frappe.db.get_single_value('HR Settings', 'claim_status_notification_template')
			if not template:
				frappe.msgprint(_("Please set default template for Claim Status Notification in HR Settings."))
				return
		elif self.doc.doctype == "Overtime Application":
			template = frappe.db.get_single_value('HR Settings', 'overtime_status_notification_template')
			if not template:
				frappe.msgprint(_("Please set default template for Overtime Status Notification in HR Settings."))
				return

		elif self.doc.doctype == "Employee Benefits":
			template = frappe.db.get_single_value('HR Settings', 'benefits_status_notification_template')
			if not template:
				frappe.msgprint(_("Please set default template for Employee Benefits Status Notification in HR Settings."))
				return

		elif self.doc.doctype == "SWS Application":
			template = frappe.db.get_single_value('HR Settings', 'sws_application_status_notification_template')
			if not template:
				frappe.msgprint(_("Please set default template for SWS Application Status Notification in HR Settings."))
				return
		elif self.doc.doctype == "Training Request":
			template = frappe.db.get_single_value('HR Settings', 'training_request_status_notification_template')
			if not template:
				frappe.msgprint(_("Please set default template for Training Request Status Notification in HR Settings."))
				return

		elif self.doc.doctype == "Training Nomination":
			# template needs to be taken care
			pass
		elif self.doc.doctype == "Ad hoc Training Request":
			# template needs to be taken care
			pass
		elif self.doc.doctype == "Training Approval Request":
			# template needs to be taken care
			pass

		elif self.doc.doctype == "Festival Advance":
			# template needs to be taken care
			pass
		else:
			template = ""

		if not template:
			frappe.msgprint(_("Please set default template for {}.").format(self.doc.doctype))
			return
		email_template = frappe.get_doc("Email Template", template)
		message = frappe.render_template(email_template.response, args)

		self.notify({
			# for post in messages
			"message": message,
			"message_to": employee.user_id,
			# for email
			"subject": email_template.subject,
			"notify": "employee"
		})

	def notify_approver(self):
		if self.doc.get(self.doc_approver[0]):
			parent_doc = frappe.get_doc(self.doc.doctype, self.doc.name)
			args = parent_doc.as_dict()

			if self.doc.doctype == "Leave Application":
				template = frappe.db.get_single_value('HR Settings', 'leave_approval_notification_template')
				if not template:
					frappe.msgprint(_("Please set default template for Leave Approval Notification in HR Settings."))
					return
			elif self.doc.doctype == "Leave Encashment":
				template = frappe.db.get_single_value('HR Settings', 'encashment_approval_notification_template')
				if not template:
					frappe.msgprint(_("Please set default template for Encashment Approval Notification in HR Settings."))
					return
			elif self.doc.doctype == "Salary Advance":
				template = frappe.db.get_single_value('HR Settings', 'advance_approval_notification_template')
				if not template:
					frappe.msgprint(_("Please set default template for Advance Approval Notification in HR Settings."))
					return
			elif self.doc.doctype == "Travel Authorization":
				template = frappe.db.get_single_value('HR Settings', 'authorization_approval_notification_template')
				if not template:
					frappe.msgprint(_("Please set default template for Authorization Approval Notification in HR Settings."))
					return
			elif self.doc.doctype == "Travel Claim":
				template = frappe.db.get_single_value('HR Settings', 'claim_approval_notification_template')
				if not template:
					frappe.msgprint(_("Please set default template for Claim Approval Notification in HR Settings."))
					return
			elif self.doc.doctype == "Overtime Application":
				template = frappe.db.get_single_value('HR Settings', 'overtime_approval_notification_template')
				if not template:
					frappe.msgprint(_("Please set default template for Overtime Approval Notification in HR Settings."))
					return
			elif self.doc.doctype == "Employee Benefits":
				template = frappe.db.get_single_value('HR Settings', 'benefits_approval_notification_template')
				if not template:
					frappe.msgprint(_("Please set default template for Employee Benefits Notification in HR Settings."))
					return 
			elif self.doc.doctype == "SWS Application":
				template = frappe.db.get_single_value('HR Settings', 'sws_application_approval_notification_template')
				if not template:
					frappe.msgprint(_("Please set default template for SWS Application Notification in HR Settings."))
					return
			elif self.doc.doctype == "Training Request":
				template = frappe.db.get_single_value('HR Settings', 'training_request_approval_notification_template')
				if not template:
					frappe.msgprint(_("Please set default template for Training Request Notification in HR Settings."))
					return
			   

			elif self.doc.doctype == "Training Nomination":
				# template needs to be taken care
				pass
			elif self.doc.doctype == "Ad hoc Training Request":
				# template needs to be taken care
				pass
			elif self.doc.doctype == "Training Approval Request":
				# template needs to be taken care
				pass
			elif self.doc.doctype == "Festival Advance":
				# template needs to be taken care
				pass
			else:
				template = ""

			if not template:
				frappe.msgprint(_("Please set default template for {}.").format(self.doc.doctype))
				return
			email_template = frappe.get_doc("Email Template", template)
			message = frappe.render_template(email_template.response, args)

			self.notify({
				# for post in messages
				"message": message,
				"message_to": self.doc.get(self.doc_approver[0]),
				# for email
				"subject": email_template.subject
			})

	def notify_material_request(self):
		owner_designation = frappe.db.get_value("Employee", {"user_id":self.doc.owner}, "designation")
		domain_name = frappe.db.get_value("Cost Center", self.doc.cost_center, "parent_cost_center")
		link_html = "<a href=" + frappe.utils.get_url_to_form(self.doc.doctype, self.doc.name) + ">" + self.doc.name + "</a>"
		if self.new_state == "Waiting For Verifier":
			pmt = frappe.db.sql("select p.user_id from `tabMR PMT And Domain Lead` p, `tabMR PMT List` a where a.parent=p.name and p.active = 1 and a.cost_center='{}'".format(self.doc.cost_center), as_dict=1)
			if pmt:
				receipients = [a['user_id'] for a in pmt if frappe.db.get_value("User", a['user_id'], "enabled") == 1]
				parent_doc = frappe.get_doc(self.doc.doctype, self.doc.name)
				args = parent_doc.as_dict()
				args.update({'domain_name': domain_name,'link_html': link_html,'owner_designation': owner_designation, 'employee_name':self.login_user[1],'employee_designation':self.login_user[2]})
				email_template = frappe.get_doc("Email Template", "MR PMT Email")
				message = frappe.render_template(email_template.response, args)
				
		elif self.new_state == "Waiting For Approver":
			dl = frappe.db.sql("select p.user_id from `tabMR PMT And Domain Lead` p, `tabMR Domain List` a where a.parent=p.name and p.active = 1 and a.cost_center='{}'".format(self.doc.cost_center), as_dict=1)
			if dl:
				receipients = [a['user_id'] for a in dl if frappe.db.get_value("User", a['user_id'], "enabled") == 1]
				parent_doc = frappe.get_doc(self.doc.doctype, self.doc.name)
				args = parent_doc.as_dict()
				args.update({'domain_name': domain_name,'link_html': link_html,'owner_designation': owner_designation, 'employee_name':self.login_user[1],'employee_designation':self.login_user[2]})
				email_template = frappe.get_doc("Email Template", "Domain Lead Approve")
				message = frappe.render_template(email_template.response, args)

		# frappe.throw(self.doc.get(self.doc_approver[0]))
		self.notify({
			# for post in messages
			"message": message,
			"message_to": receipients,
			# for email
			"subject": email_template.subject
		})
	
	def notify_fd_head(self):
		owner_designation = frappe.db.get_value("Employee", {"user_id":self.doc.owner}, "designation")
		receipients = [frappe.db.get_single_value("HR Settings", "fd_head_user_id")]
		receipients.append(self.doc.owner)
		# notify pmt's, domain leads, MR creator and FD Head
		# pmt = frappe.get_list("Program Management Team", filters={"parent":self.doc.cost_center}, fields=['pmt_user_id'])
		# if pmt:
		#     for a in pmt:
		#         receipients.append(a['pmt_user_id'])
		# dl = frappe.get_list("Domain Lead", filters={"parent":self.doc.cost_center}, fields=['domain_lead_user_id'])
		# if dl:
		#     for a in dl:
		#         receipients.append(a['domain_lead_user_id'])
		# notify all POs, one with Purchase Manager rols
		# users = frappe.db.sql("""SELECT u.name AS user
		#                 FROM `tabUser` u
		#                 WHERE u.name NOT IN ('Administrator') AND u.enabled = 1
		#                     AND EXISTS(SELECT 1
		#                         FROM `tabHas Role` hr
		#                         WHERE hr.parent = u.name
		#                         AND hr.role = 'Purchase Manager')
		#                 ORDER BY u.name
		#         """, as_dict=True)
		# for d in users:
		#     if d.user not in receipients:
		#         receipients.append(d.user)
		domain_name = frappe.db.get_value("Cost Center", self.doc.cost_center, "parent_cost_center")
		link_html = "<a href=" + frappe.utils.get_url_to_form(self.doc.doctype, self.doc.name) + ">" + self.doc.name + "</a>"
		parent_doc = frappe.get_doc(self.doc.doctype, self.doc.name)
		args = parent_doc.as_dict()
		args.update({'domain_name': domain_name,'link_html': link_html,'owner_designation': owner_designation, 'employee_name':self.login_user[1],'employee_designation':self.login_user[2]})
		email_template = frappe.get_doc("Email Template", "FD Head MR Notice")
		message = frappe.render_template(email_template.response, args)
		self.notify({
			# for post in messages
			"message": message,
			"message_to": receipients,
			# for email
			"subject": email_template.subject
		})
	
	def notify_rejected_state(self):
		owner_designation = frappe.db.get_value("Employee", {"user_id":self.doc.owner}, "designation")
		domain_name = frappe.db.get_value("Cost Center", self.doc.cost_center, "parent_cost_center")
		if self.new_state in ("Rejected"):
			receipients = self.doc.owner
		else:
			receipients = []
			receipients.append(self.doc.owner)
			pmt = frappe.db.sql("select p.user_id from `tabMR PMT And Domain Lead` p, `tabMR PMT List` a where a.parent=p.name and p.active = 1 and a.cost_center='{}'".format(self.doc.cost_center), as_dict=1)
			if pmt:
				for a in pmt:
					receipients.append(a['user_id'])

		parent_doc = frappe.get_doc(self.doc.doctype, self.doc.name)
		args = parent_doc.as_dict()
		args.update({'domain_name': domain_name,'owner_designation': owner_designation, 'employee_name':self.login_user[1],'employee_designation':self.login_user[2]})
		email_template = frappe.get_doc("Email Template", "Rejected MR Notice")
		message = frappe.render_template(email_template.response, args)
		self.notify({
			# for post in messages
			"message": message,
			"message_to": receipients,
			# for email
			"subject": email_template.subject
		})

	def notify(self, args):
		args = frappe._dict(args)
		# args -> message, message_to, subject

		contact = args.message_to
		if not isinstance(contact, list):
			if not args.notify == "employee":
				contact = frappe.get_doc('User', contact).email or contact

		sender      	    = dict()
		sender['email']     = frappe.get_doc('User', frappe.session.user).email
		sender['full_name'] = frappe.utils.get_fullname(sender['email'])

		try:
			frappe.sendmail(
				recipients = contact,
				sender = sender['email'],
				subject = args.subject,
				message = args.message,
			)
			frappe.msgprint(_("Email sent to {0}").format(contact))
		except frappe.OutgoingEmailError:
			pass

	def send_notification(self):

		if (self.doc.doctype not in self.field_map) or not frappe.db.exists("Workflow", {"document_type": self.doc.doctype, "is_active": 1}):
			return

		if self.new_state == "Draft":
			return
		elif self.new_state in ("Approved", "Rejected", "Cancelled", "Domain Lead Rejected"):
			if self.doc.doctype == "Material Request" and self.new_state == "Approved":
				self.notify_fd_head()
			elif self.doc.doctype == "Material Request" and self.new_state in ("Rejected","Domain Lead Rejected"):
				self.notify_rejected_state()
			else:
				self.notify_employee()
		elif self.new_state.startswith("Waiting") and self.old_state != self.new_state:
			if self.doc.doctype == "Material Request":
				self.notify_material_request()
			else:
				self.notify_approver()
		else:
			frappe.msgprint(_("Email notifications not configured for workflow state {}").format(self.new_state))

def get_field_map():
	return {
		"Salary Advance": ["advance_approver","advance_approver_name","advance_approver_designation"],
		"Leave Encashment": ["approver","approver_name","approver_designation"],
		"Leave Application": ["leave_approver", "leave_approver_name", "leave_approver_designation"],
		"Travel Authorization": ["supervisor", "supervisor_name", "supervisor_designation"],
		"Travel Claim": ["supervisor", "supervisor_name", "supervisor_designation"],
		"Overtime Application": ["approver", "approver_name", "approver_designation"],
		"Material Request": ["approver","approver_name","approver_designation"],
		"Festival Advance": ["advance_approver","advance_approver_name", "advance_approver_designation"],
		"Employee Transfer": ["supervisor", "supervisor_name", "supervisor_designation"],
		"Employee Benefits": ["benefit_approver","benefit_approver_name","benefit_approver_designation"],
		"SWS Application": ["supervisor","supervisor_name","supervisor_designation"],
		"Training Nomination": [],
		"Ad hoc Training Request": [],
		"Training Approval Request": [],
	}

def validate_workflow_states(doc):
	wf = CustomWorkflow(doc)
	wf.apply_workflow()

def notify_workflow_states(doc):
	wf = NotifyCustomWorkflow(doc)
	wf.send_notification()

