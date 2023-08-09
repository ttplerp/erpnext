# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

'''
------------------------------------------------------------------------------------------------------------------------------------------
Version          Author         Ticket#           CreatedOn          ModifiedOn          Remarks
------------ --------------- --------------- ------------------ -------------------  -----------------------------------------------------
3.0               SHIV		                     28/01/2019                          Original Version
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
		self.new_state = self.doc.workflow_state
		self.old_state = self.doc.get_db_value("workflow_state")
		self.field_map 		= get_field_map()
		self.doc_approver	= self.field_map[self.doc.doctype]
		self.field_list		= ["user_id","employee_name","designation","name"]
		if self.doc.doctype != "Material Request" and self.doc.doctype != "Performance Evaluation" and self.doc.doctype not in ("Project Capitalization","Asset Issue Details", "Compile Budget","Asset Movement", "Budget Reappropiation", "Employee Advance", "Imprest Advance", "Imprest Recoup", "Vehicle Request"):
			self.employee = frappe.db.get_value("Employee", self.doc.employee, self.field_list)
			self.reports_to = frappe.db.get_value("Employee", {"name":frappe.db.get_value("Employee", self.doc.employee, "reports_to")}, self.field_list)
			self.hr_approver	= frappe.db.get_value("Employee", frappe.db.get_single_value("HR Settings", "hr_approver"), self.field_list)
			self.hrgm 			= frappe.db.get_value("Employee",frappe.db.get_single_value("HR Settings","hrgm"), self.field_list)
			self.ceo			= frappe.db.get_value("Employee", frappe.db.get_value("Employee", {"designation": "Chief Executive Officer", "status": "Active"},"name"), self.field_list)
			self.gmcsd			= frappe.db.get_value("Employee", frappe.db.get_value("Department", {"department_name": "Corporate Support Services Division"},"approver"), self.field_list)

			if self.doc.doctype in ["Employee Separation Clearance","Leave Encashment","Leave Application"]:
				self.adm_section_manager = frappe.db.get_value("Employee",{"user_id":frappe.db.get_value(
					"Department Approver",
					{"parent": "Administration Section - SMCL", "parentfield": "expense_approvers", "idx": 1},
					"approver",
				)},self.field_list)

		if self.doc.doctype in ("Travel Request","Leave Application","Employee Separation","Overtime Application"):
			division = frappe.db.get_value("Employee",self.doc.employee,"division")
			section = frappe.db.get_value("Employee",self.doc.employee, "section")
			unit = frappe.db.get_value("Employee",self.doc.employee, "unit")
			self.hrgm 	= frappe.db.get_value("Employee",frappe.db.get_single_value("HR Settings","hrgm"), self.field_list)
			self.ceo	= frappe.db.get_value("Employee", frappe.db.get_value("Employee", {"designation": "Chief Executive Officer", "status": "Active"},"name"), self.field_list)

			self.section_approver = frappe.db.get_value("Employee",{"user_id":frappe.db.get_value(
					"Department Approver",
					{"parent": section, "parentfield": "leave_approvers", "idx": 1},
					"approver",
				)},self.field_list)
			self.division_approver = frappe.db.get_value("Employee",{"user_id":frappe.db.get_value(
					"Department Approver",
					{"parent": division, "parentfield": "leave_approvers", "idx": 1},
					"approver",
				)},self.field_list)

		if self.doc.doctype == "Performance Evaluation":
			self.employee		= frappe.db.get_value("Employee", self.doc.employee, self.field_list)
			self.reports_to		= frappe.db.get_value("Employee", frappe.db.get_value("Employee", self.doc.employee, "reports_to"), self.field_list)
			
		if self.doc.doctype == "Asset Movement":
			department = frappe.db.get_value("Employee",{"user_id":frappe.session.user}, "department")
			if not department:
				frappe.throw("Department not set for {}".format(frappe.session.user))
			if department != "CHIEF EXECUTIVE OFFICE - SMCL":
				self.asset_verifier = frappe.db.get_value("Employee",{"user_id":frappe.db.get_value(
						"Department Approver",
						{"parent": department, "parentfield": "expense_approvers", "idx": 1},
						"approver",
					)},self.field_list)
			else:
				self.asset_verifier = frappe.db.get_value("Employee", frappe.db.get_value("Employee", {"designation": "Chief Executive Officer", "status": "Active"},"name"), self.field_list)
		
		if self.doc.doctype in ("Budget Reappropiation"):
			department = frappe.db.get_value("Employee", {"user_id":self.doc.owner},"department")
			section = frappe.db.get_value("Employee", {"user_id":self.doc.owner},"section")
			self.ceo= frappe.db.get_value("Employee", frappe.db.get_value("Employee", {"designation": "Chief Executive Officer", "status": "Active"},"name"), self.field_list)
			if section in ("Chunaikhola Dolomite Mines - SMCL","Samdrup Jongkhar - SMCL"):
				self.budget_reappropiation_approver = frappe.db.get_value("Employee",{"user_id":frappe.db.get_value(
					"Department Approver",
					{"parent": section, "parentfield": "expense_approvers", "idx": 1},
					"approver",
				)},self.field_list)
			else:
				self.budget_reappropiation_approver = frappe.db.get_value("Employee",{"user_id":frappe.db.get_value(
					"Department Approver",
					{"parent": department, "parentfield": "expense_approvers", "idx": 1},
					"approver",
				)},self.field_list)
			if not self.budget_reappropiation_approver:
				frappe.throw("No employee found for user id(expense approver) {}".format(frappe.db.get_value(
					"Department Approver",
					{"parent": department, "parentfield": "expense_approvers", "idx": 1},
					"approver",
				)))
		if self.doc.doctype == "Employee Advance":
			self.ceo			= frappe.db.get_value("Employee", frappe.db.get_value("Employee", {"designation": "Chief Executive Officer", "status": "Active"},"name"), self.field_list)
			self.hr_approver	= frappe.db.get_value("Employee", frappe.db.get_single_value("HR Settings", "hr_approver"), self.field_list)
		
		if self.doc.doctype == "Material Request":
			employee = frappe.db.get_value("Employee", {"user_id":self.doc.owner},"name")
			division = frappe.db.get_value("Employee",employee,"division")
			self.reports_to	= frappe.db.get_value("Employee", frappe.db.get_value("Employee", {'user_id':self.doc.owner}, "reports_to"), self.field_list)

			self.division_approver = frappe.db.get_value("Employee",frappe.db.get_value("Department",division,"approver"),self.field_list)
		if self.doc.doctype == "Employee Benefits":
			self.hrgm = frappe.db.get_value("Employee",frappe.db.get_single_value("HR Settings","hrgm"), self.field_list)	
		
		if self.doc.doctype in ("Imprest Advance", "Imprest Recoup"):
			self.imprest_verifier = frappe.db.get_value("Employee", frappe.db.get_value("Branch", {"branch": self.doc.branch}, "imprest_verifier"), self.field_list)
			if not self.imprest_verifier:
				frappe.throw("Please set the Imprest Verifier for branch <b>{}</b>".format(self.doc.branch))
			self.imprest_approver = frappe.db.get_value("Employee", frappe.db.get_value("Department", {"name": "Corporate Services Division - NHDCL"}, "approver"), self.field_list)
		
		if self.doc.doctype == "Vehicle Request":
			self.fleet_mto = frappe.db.get_value("Employee",{"user_id":frappe.db.get_single_value("Maintenance Settings","fleet_mto")},self.field_list)
	
		self.login_user		= frappe.db.get_value("Employee", {"user_id": frappe.session.user}, self.field_list)
		self.final_approver	= []

		if not self.login_user and frappe.session.user != "Administrator":
			if "PERC Member" in frappe.get_roles(frappe.session.user):
				return
			frappe.throw("{0} is not added as the employee".format(frappe.session.user))
		

	def update_employment_status(self):
		emp_status = frappe.db.get_value("Leave Type", self.doc.leave_type, ["check_employment_status","employment_status"])
		if cint(emp_status[0]) and emp_status[1]:
			emp = frappe.get_doc("Employee", self.doc.employee)
			emp.employment_status = emp_status[1]
			emp.save(ignore_permissions=True)

	def notify_hr(self):
		receipients = []
		email_group = frappe.db.get_single_value("HR Settings","email_group")
		if not email_group:
			frappe.throw("HR Users Email Group not set in HR Settings.")
		hr_users = frappe.get_list("Email Group Member", filters={"email_group":email_group}, fields=['email'])
		if hr_users:
			receipients = [a['email'] for a in hr_users]
			parent_doc = frappe.get_doc(self.doc.doctype, self.doc.name)
			args = parent_doc.as_dict()
			if self.doc.doctype == "Leave Application":
				template = frappe.db.get_single_value('HR Settings', 'leave_approval_notification_template')
				if not template:
					frappe.msgprint(_("Please set default template for Leave Approval Notification in HR Settings."))
					return
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
				"message_to": receipients,
				# for email
				"subject": email_template.subject
			})

	def set_approver(self, approver_type):
		if approver_type == "Supervisor":
			officiating = get_officiating_employee(self.reports_to[3])
			if officiating:
				officiating = frappe.db.get_value("Employee", officiating[0].officiate, self.field_list)
			vars(self.doc)[self.doc_approver[0]] = officiating[0] if officiating else self.reports_to[0]
			vars(self.doc)[self.doc_approver[1]] = officiating[1] if officiating else self.reports_to[1]
			vars(self.doc)[self.doc_approver[2]] = officiating[2] if officiating else self.reports_to[2]

		elif approver_type =="Asset Verifier":
			officiating = get_officiating_employee(self.asset_verifier[3])
			if officiating:
				officiating = frappe.db.get_value("Employee", officiating[0].officiate, self.field_list)
			vars(self.doc)[self.doc_approver[0]] = officiating[0] if officiating else self.asset_verifier[0]
			vars(self.doc)[self.doc_approver[1]] = officiating[1] if officiating else self.asset_verifier[1]
			vars(self.doc)[self.doc_approver[2]] = officiating[2] if officiating else self.asset_verifier[2]
		
		elif approver_type =="Section Approver":
			officiating = get_officiating_employee(self.section_approver[3])
			if officiating:
				officiating = frappe.db.get_value("Employee", officiating[0].officiate, self.field_list)
			vars(self.doc)[self.doc_approver[0]] = officiating[0] if officiating else self.section_approver[0]
			vars(self.doc)[self.doc_approver[1]] = officiating[1] if officiating else self.section_approver[1]
			vars(self.doc)[self.doc_approver[2]] = officiating[2] if officiating else self.section_approver[2]
		
		elif approver_type =="Division Approver":
			officiating = get_officiating_employee(self.division_approver[3])
			if officiating:
				officiating = frappe.db.get_value("Employee", officiating[0].officiate, self.field_list)
			vars(self.doc)[self.doc_approver[0]] = officiating[0] if officiating else self.division_approver[0]
			vars(self.doc)[self.doc_approver[1]] = officiating[1] if officiating else self.division_approver[1]
			vars(self.doc)[self.doc_approver[2]] = officiating[2] if officiating else self.division_approver[2]
		
		elif approver_type =="Imprest Verifier":
			officiating = get_officiating_employee(self.imprest_verifier[3])
			if officiating:
				officiating = frappe.db.get_value("Employee", officiating[0].officiate, self.field_list)
			vars(self.doc)[self.doc_approver[0]] = officiating[0] if officiating else self.imprest_verifier[0]
			vars(self.doc)[self.doc_approver[1]] = officiating[1] if officiating else self.imprest_verifier[1]
			vars(self.doc)[self.doc_approver[2]] = officiating[2] if officiating else self.imprest_verifier[2]

		elif approver_type =="Imprest Approver":
			officiating = get_officiating_employee(self.imprest_approver[3])
			if officiating:
				officiating = frappe.db.get_value("Employee", officiating[0].officiate, self.field_list)
			vars(self.doc)[self.doc_approver[0]] = officiating[0] if officiating else self.imprest_approver[0]
			vars(self.doc)[self.doc_approver[1]] = officiating[1] if officiating else self.imprest_approver[1]
			vars(self.doc)[self.doc_approver[2]] = officiating[2] if officiating else self.imprest_approver[2]
		
		elif approver_type == "HR":
			officiating = get_officiating_employee(self.hr_approver[3])
			if officiating:
				officiating = frappe.db.get_value("Employee", officiating[0].officiate, self.field_list)
			vars(self.doc)[self.doc_approver[0]] = officiating[0] if officiating else self.hr_approver[0]
			vars(self.doc)[self.doc_approver[1]] = officiating[1] if officiating else self.hr_approver[1]
			vars(self.doc)[self.doc_approver[2]] = officiating[2] if officiating else self.hr_approver[2]
		
		elif approver_type == "HRGM":
			officiating = get_officiating_employee(self.hrgm[3])
			if officiating:
				officiating = frappe.db.get_value("Employee", officiating[0].officiate, self.field_list)
			vars(self.doc)[self.doc_approver[0]] = officiating[0] if officiating else self.hrgm[0]
			vars(self.doc)[self.doc_approver[1]] = officiating[1] if officiating else self.hrgm[1]
			vars(self.doc)[self.doc_approver[2]] = officiating[2] if officiating else self.hrgm[2]
		
		elif approver_type == "Fleet Manager":
			officiating = get_officiating_employee(self.fleet_mto[3])
			if officiating:
				officiating = frappe.db.get_value("Employee", officiating[0].officiate, self.field_list)
			vars(self.doc)[self.doc_approver[0]] = officiating[0] if officiating else self.fleet_mto[0]
			vars(self.doc)[self.doc_approver[1]] = officiating[1] if officiating else self.fleet_mto[1]
		
		elif approver_type == "Warehouse Manager":
			officiating = get_officiating_employee(self.warehouse_manager[3])
			if officiating:
				officiating = frappe.db.get_value("Employee", officiating[0].officiate, self.field_list)
			vars(self.doc)[self.doc_approver[0]] = officiating[0] if officiating else self.warehouse_manager[0]
			vars(self.doc)[self.doc_approver[1]] = officiating[1] if officiating else self.warehouse_manager[1]
			vars(self.doc)[self.doc_approver[2]] = officiating[2] if officiating else self.warehouse_manager[2]

		elif approver_type == "CEO":
			officiating = get_officiating_employee(self.ceo[3])
			if officiating:
				officiating = frappe.db.get_value("Employee", officiating[0].officiate, self.field_list)
			vars(self.doc)[self.doc_approver[0]] = officiating[0] if officiating else self.ceo[0]
			vars(self.doc)[self.doc_approver[1]] = officiating[1] if officiating else self.ceo[1]
			vars(self.doc)[self.doc_approver[2]] = officiating[2] if officiating else self.ceo[2]
		
		elif approver_type == "Project Approver":
			officiating = get_officiating_employee(self.project_approver[3])
			if officiating:
				officiating = frappe.db.get_value("Employee", officiating[0].officiate, self.field_list)
			vars(self.doc)[self.doc_approver[0]] = officiating[0] if officiating else self.project_approver[0]
			vars(self.doc)[self.doc_approver[1]] = officiating[1] if officiating else self.project_approver[1]
			vars(self.doc)[self.doc_approver[2]] = officiating[2] if officiating else self.project_approver[2]
			
		elif approver_type == "Budget Reappropiation":
			officiating = get_officiating_employee(self.budget_reappropiation_approver[3])
			if officiating:
				officiating = frappe.db.get_value("Employee", officiating[0].officiate, self.field_list)
			vars(self.doc)[self.doc_approver[0]] = officiating[0] if officiating else self.budget_reappropiation_approver[0]
			vars(self.doc)[self.doc_approver[1]] = officiating[1] if officiating else self.budget_reappropiation_approver[1]
			vars(self.doc)[self.doc_approver[2]] = officiating[2] if officiating else self.budget_reappropiation_approver[2]
		else:
			frappe.throw(_("Invalid approver type for Workflow"))


	def apply_workflow(self):
		if (self.doc.doctype not in self.field_map) or not frappe.db.exists("Workflow", {"document_type": self.doc.doctype, "is_active": 1}):
			return
		if self.doc.doctype == "Leave Application":
			self.leave_application()	
		elif self.doc.doctype == "Leave Encashment":
			self.leave_encashment()
		elif self.doc.doctype == "Travel Request":
			self.travel_request()
		elif self.doc.doctype == "Overtime Application":
			self.overtime_application()
		elif self.doc.doctype == "Material Request":
			self.material_request()		
		elif self.doc.doctype == "Employee Advance":
			self.employee_advance()
		elif self.doc.doctype == "Employee Transfer":
			self.employee_transfer()
		elif self.doc.doctype == "Budget Reappropiation":
			self.budget_reappropiation()
		elif self.doc.doctype == "Target Set Up":
			self.target_setup_request()
		elif self.doc.doctype == "Performance Evaluation":
			self.performance_evaluation_request()
		elif self.doc.doctype == "PMS Appeal":
			self.pms_appeal_request()
		elif self.doc.doctype == "Employee Separation":
			self.employee_separation()
		elif self.doc.doctype == "Employee Benefits":
			self.employee_benefits()
		elif self.doc.doctype == "Imprest Advance":
			self.imprest_advance()
		elif self.doc.doctype == "Imprest Recoup":
			self.imprest_recoup()
		elif self.doc.doctype in ("Asset Issue Details","Project Capitalization"):
			self.asset()
		elif self.doc.doctype == "Asset Movement":
			self.asset_movement()
		elif self.doc.doctype == "Vehicle Request":
			self.vehicle_request()
		else:
			frappe.throw(_("Workflow not defined for {}").format(self.doc.doctype))
	
	def vehicle_request(self):
		if self.new_state.lower() in ("Draft".lower()):
			if self.doc.owner != frappe.session.user:
				frappe.throw("Only {} can Apply this material request".format(self.doc.owner))
			self.set_approver("Fleet Manager")
		elif self.new_state.lower() in ("Waiting MTO Approval".lower()):
			if self.doc.approver_id != frappe.session.user:
				frappe.throw("Only {} can forward this request".format(self.doc.approver_id))
			self.set_approver("Fleet Manager")
		elif self.new_state.lower() in ("Approved".lower()):
			if self.doc.approver_id != frappe.session.user:
				frappe.throw("Only {} can Approve this Vehicle Request".format(self.doc.approver_id))
	def target_setup_request(self):
		pass

	def performance_evaluation_request(self):
		if not self.new_state:
			frappe.throw('Due to slow network/some other issue this document faced issue to save. Please reload the page and save again.')
		if self.new_state.lower() in ("Draft".lower()):
			if (self.doc.owner != frappe.session.user and self.doc.approver != frappe.session.user):
				frappe.throw("Only {} or {} can Apply or make changes to this Request".format(self.doc.employee_name, self.doc.approver_name))	
			if self.doc.set_manual_approver == 1:
				return
			else:
				self.set_approver("Supervisor")

		elif self.new_state.lower() in ("Waiting Supervisor Approval".lower()):
			# to accomodate the approver changes made manually for PMS Calendar 2021
			if self.doc.set_manual_approver != 1:
				self.set_approver("Supervisor")
			elif self.doc.set_manual_approver == 1:
				if self.old_state.lower() == "Rejected".lower():
					self.doc.approver = self.doc.approver_in_first_level
					self.doc.approver_name = self.doc.approver_fl_name
					self.doc.approver_designation = self.doc.approver_fl_designation
				else:
					return
			if ("HR User" in frappe.get_roles(frappe.session.user) or "HR Manager" in frappe.get_roles(frappe.session.user)) and self.doc.employee != frappe.db.get_value('Employee',{'user_id':frappe.session.user},'name') : 
				return
			if (self.doc.owner != frappe.session.user and self.doc.approver != frappe.session.user):
				frappe.throw("Only {} or {} can Apply or make changes to this Request".format(self.doc.employee_name, self.doc.approver_name))
			
		elif self.new_state.lower() in ("Waiting Approval".lower()):
			if self.doc.approver != frappe.session.user:
				frappe.throw("Only {} can Forward/Reject this Target".format(self.doc.approver_name))
			self.set_approver("Supervisors Supervisor")
			if "HR User" in frappe.get_roles(frappe.session.user) or "HR Manager" in frappe.get_roles(frappe.session.user): 
				return	
		elif self.new_state.lower() in ("Approved".lower(), "Waiting PERC".lower(), "Rejected".lower()):
			if self.doc.approver != frappe.session.user:
				frappe.throw("Only {} can Forward/Reject this Target".format(self.doc.approver_name))
		elif self.new_state.lower() in ("Approved By PERC".lower(), "Rejected By PERC".lower()):
			if "PERC Member" in frappe.get_roles(frappe.session.user):
				return
			else:
				frappe.throw("Only PERC Member can Approve/Reject this Target")

	def pms_appeal_request(self):
		pass

	def employee_separation(self):
		division = frappe.db.get_value("Employee",self.doc.employee,"division")
		section = frappe.db.get_value("Employee",self.doc.employee, "section")
		unit = frappe.db.get_value("Employee",self.doc.employee, "unit")
		if self.new_state.lower() in ("Draft".lower(), "Waiting Supervisor Approval".lower()):
			if self.new_state.lower() == ("Waiting Supervisor Approval".lower()):
				self.set_approver("Supervisor")	

		elif self.new_state.lower() == ("Waiting Approval".lower()):
			if self.doc.approver != frappe.session.user:
				frappe.throw("Only {} can Approve this Leave".format(self.doc.approver_name))
			if unit:
				section_approver = frappe.db.get_value(
					"Department Approver",
					{"parent": section, "parentfield": "leave_approvers", "idx": 1},
					"approver",
				)
				if section_approver:
					self.set_approver("Section Approver")
				else:
					self.set_approver("Division Approver")
			else:
				self.set_approver("Division Approver")

		elif self.new_state.lower() == ("Waiting CEO Approval".lower()):
			if self.doc.approver != frappe.session.user:
				frappe.throw("Only {} can Apply or Forward this Application".format(self.doc.approver_name))
			self.set_approver("CEO")

		elif self.new_state.lower() == ("Approved".lower()):
			if self.doc.approver != frappe.session.user:
				frappe.throw("Only {} can Approve this Application".format(self.doc.approver_name))

		elif self.new_state.lower() == ("Rejected".lower(), "Rejected by CEO".lower()):
			if self.doc.approver != frappe.session.user:
				frappe.throw("Only {} can Reject this Application".format(self.doc.approver_name))
		else:
			frappe.throw(_("Invalid Workflow State {}").format(self.doc.workflow_state))
	
	def employee_benefits(self):
		if self.new_state.lower() in ("Draft".lower(), "Waiting GM Approval".lower()):
			if self.new_state.lower() == "Waiting GM Approval".lower():
				if "HR User" not in frappe.get_roles(frappe.session.user):
					frappe.throw("Only HR can Apply this Appeal")
			self.set_approver("HRGM")
		elif self.new_state.lower() == "Waiting Approval".lower():
			if self.doc.benefit_approver != frappe.session.user:
				frappe.throw("Only {} can Forward this document".format(self.doc.benefit_approver_name))
			self.set_approver("CEO")
		elif self.new_state.lower() in ("Approved".lower(), "Rejected".lower()):
			if self.doc.benefit_approver != frappe.session.user:
				frappe.throw("Only {} can Approved or Reject this document".format(self.doc.benefit_approver_name))
	
	def imprest_advance(self):
		if self.new_state.lower() in ("Draft".lower(), "Waiting for Verification".lower()):
			if self.new_state.lower() == "Waiting for Verification".lower():
				if frappe.session.user != self.doc.owner:
					frappe.throw("Only {} can apply this Imprest Advance".format(self.doc.owner))
			self.set_approver("Imprest Verifier")

		elif self.new_state.lower() in ("Waiting Approval".lower(), "Rejected".lower()):
			if self.doc.approver != frappe.session.user:
				frappe.throw("Only {} can Forward or Reject this document".format(self.doc.approver_name))
			self.set_approver("Imprest Approver")
		
		elif self.new_state.lower() in ("Approved".lower(), "Rejected".lower()):
			if self.doc.approver != frappe.session.user:
				frappe.throw("Only {} can Approver or Reject this document".format(self.doc.approver_name))
		else:
			frappe.throw(_("Invalid Workflow State {}").format(self.doc.workflow_state))
	
	def imprest_recoup(self):
		if self.new_state.lower() in ("Draft".lower(), "Waiting for Verification".lower()):
			if self.new_state.lower() == "Waiting for Verification".lower():
				if frappe.session.user != self.doc.owner:
					frappe.throw("Only {} can apply this Imprest Advance".format(self.doc.owner))
			self.set_approver("Imprest Verifier")

		elif self.new_state.lower() in ("Waiting Recoupment".lower(), "Rejected".lower()):
			if self.doc.approver != frappe.session.user:
				frappe.throw("Only {} can Forward or Reject this document".format(self.doc.approver_name))
			self.set_approver("Imprest Approver")
		
		elif self.new_state.lower() in ("Recouped".lower(), "Rejected".lower()):
			if self.doc.approver != frappe.session.user:
				frappe.throw("Only {} can Recoup or Reject this document".format(self.doc.approver_name))
		else:
			frappe.throw(_("Invalid Workflow State {}").format(self.doc.workflow_state))

	def asset(self):
		pass

	def leave_application(self):
		division = frappe.db.get_value("Employee",self.doc.employee,"division")
		section = frappe.db.get_value("Employee",self.doc.employee, "section")
		unit = frappe.db.get_value("Employee",self.doc.employee, "unit")
		if self.new_state.lower() in ("Draft".lower()):
			if frappe.session.user != self.doc.owner:
				frappe.throw("Only {} can apply this leave".format(self.doc.owner))
		elif self.new_state.lower() == ("Waiting Supervisor Approval".lower()):
			self.set_approver("Supervisor")	
		elif self.new_state.lower() == ("Waiting Approval".lower()):
			if self.doc.leave_approver != frappe.session.user:
				frappe.throw("Only {} can Approve this Leave Application".format(self.doc.leave_approver_name))
			if unit:
				section_approver = frappe.db.get_value(
					"Department Approver",
					{"parent": section, "parentfield": "leave_approvers", "idx": 1},
					"approver",
				)
				if section_approver:
					self.set_approver("Section Approver")
				else:
					self.set_approver("Division Approver")
			else:
				self.set_approver("Division Approver")

		elif self.new_state.lower() in ("Waiting HR Approval".lower()):
			if self.doc.leave_approver != frappe.session.user:
				frappe.throw("Only {} can Apply or Forward this Leave Application".format(self.doc.leave_approver_name))
			self.set_approver("HR")	

		elif self.new_state.lower() == ("Waiting CEO Approval".lower()):
			if self.doc.leave_approver != frappe.session.user:
				frappe.throw("Only {} can Apply or Forward this Leave Application".format(self.doc.leave_approver_name))
			self.set_approver("CEO")

		elif self.new_state.lower() == ("Approved".lower()):
			if self.doc.leave_approver != frappe.session.user:
				frappe.throw("Only {} can Approve this Leave Application".format(self.doc.leave_approver_name))

		elif self.new_state.lower() == ("Rejected".lower() or "Rejected by CEO".lower()):
			if self.doc.leave_approver != frappe.session.user:
				frappe.throw("Only {} can Reject this Leave Application".format(self.doc.leave_approver_name))
		else:
			frappe.throw(_("Invalid Workflow State {}").format(self.doc.workflow_state))

	def leave_encashment(self):
		''' Leave Encashment Workflow
			1. Employee -> HR --> HR GM approved
		'''
		if self.new_state.lower() == ("Draft".lower()):
			pass
		elif self.new_state.lower() == "Waiting HR Approval".lower():
			self.set_approver("HR")
		elif self.new_state.lower() == "Waiting Approval".lower():
			if self.doc.approver != frappe.session.user:
				frappe.throw("Only {} can Forward this Encashment".format(self.doc.approver_name))
			self.set_approver("HRGM")
		elif  self.new_state.lower() in ("Approved".lower(), "Rejected".lower()):
			if self.doc.approver != frappe.session.user:
				frappe.throw("Only {} can Approve / Reject this Encashment".format(self.doc.approver_name))
		else:
			frappe.throw(_("Invalid Workflow State {}").format(self.doc.workflow_state))

	def travel_request(self):
		''' Travel Request Workflow
			1. Employee -> reports_to -> section/ Division approver -> HR approved
		'''

		division = frappe.db.get_value("Employee",self.doc.employee,"division")
		section = frappe.db.get_value("Employee",self.doc.employee, "section")
		unit = frappe.db.get_value("Employee",self.doc.employee, "unit")
		if self.new_state.lower() == ("Draft".lower()):
			if self.doc.owner != frappe.session.user:
				frappe.throw("Only {} can Apply this Application".format(self.doc.owner))
		elif self.new_state.lower() in ("Waiting Supervisor Approval".lower()):
			self.set_approver("Supervisor")	

		elif self.new_state.lower() == ("Waiting Approval".lower()):
			if self.doc.supervisor != frappe.session.user:
				frappe.throw("Only {} can Forward this Application".format(self.doc.supervisor_name))
			if unit:
				section_approver = frappe.db.get_value(
					"Department Approver",
					{"parent": section, "parentfield": "leave_approvers", "idx": 1},
					"approver",
				)
				if section_approver:
					self.set_approver("Section Approver")
				else:
					self.set_approver("Division Approver")
			else:
				self.set_approver("Division Approver")

		elif self.new_state.lower() in ("Waiting HR Approval".lower()):
			if self.doc.supervisor != frappe.session.user:
				frappe.throw("Only {} can Apply or Forward this Application".format(self.doc.supervisor_name))
			self.set_approver("HR")	

		elif self.new_state.lower() == ("Approved".lower()):
			if self.doc.supervisor != frappe.session.user:
				frappe.throw("Only {} can Approve this Application".format(self.doc.supervisor_name))

		elif self.new_state.lower() == ("Rejected".lower() or "Rejected by CEO".lower()):
			if self.doc.supervisor != frappe.session.user:
				frappe.throw("Only {} can Reject this Application".format(self.doc.supervisor_name))
		else:
			frappe.throw(_("Invalid Workflow State {}").format(self.doc.workflow_state))

	def employee_advance(self):
		if self.new_state.lower() in ("Draft".lower()):
			if self.doc.owner != frappe.session.user:
				frappe.throw("Only {} can Make changes to this document".format(self.doc.owner))

		elif self.new_state.lower() in ("Waiting HR Approval".lower()):
			if self.doc.owner != frappe.session.user:
				frappe.throw("Only {} can Apply this document".format(self.doc.owner))
			self.set_approver("HR")

		elif self.new_state.lower() in ("Waiting CEO Approval".lower()):
			if self.doc.advance_approver != frappe.session.user:
				frappe.throw("Only {} can Forward this document".format(self.doc.advance_approver_name))
			self.set_approver("CEO")

		elif self.new_state.lower() == ("Approved".lower()):
			if self.doc.advance_approver != frappe.session.user:
				frappe.throw("Only {} can Approve this document".format(self.doc.advance_approver_name))

		elif self.new_state.lower() == ("Rejected".lower()):
			if self.doc.advance_approver != frappe.session.user:
				frappe.throw("Only {} can Reject this document".format(self.doc.advance_approver_name))
		else:
			frappe.throw(_("Invalid Workflow State {}").format(self.doc.workflow_state))
	
	def asset_movement(self):
		pass
				
	def budget_reappropiation(self):
		user_roles = frappe.get_roles(frappe.session.user)
		if self.new_state and self.old_state and self.new_state.lower() == self.old_state.lower():
			return
		if self.new_state.lower() in ("Draft".lower(),"Waiting for Verification".lower()):
			if self.doc.owner != frappe.session.user:
				frappe.throw("Only the document owner can Apply this document")

		if self.new_state.lower() in ("Waiting Approval".lower()):
			if "Budget Manager" not in user_roles:
				frappe.throw("Only Budget Manager Can verify this document")
			self.set_approver("Budget Reappropiation")

		if self.new_state.lower() in ("Waiting CEO Approval".lower()):
			if self.doc.approver != frappe.session.user:
				frappe.throw("Only {} can forward this document".format(self.doc.approver))
			self.set_approver("CEO")

		if self.new_state.lower() in ("Approved".lower()):
			if self.old_state.lower() in ("Waiting CEO Approval".lower()) and  "CEO" not in user_roles:
				frappe.throw("Only CEO can approve this document")
			elif self.doc.approver != frappe.session.user :
				frappe.throw("Only {} or CEO can approve this document".format(self.doc.approver))

		if self.new_state.lower() in ("Rejected".lower()):
			if "Budget Manager" not in user_roles or "CEO" not in user_roles or self.doc.approver != frappe.session.user:
				frappe.throw("Only Budget Manager or {} Can reject this document".format(self.doc.approver))

	def overtime_application(self):
		division = frappe.db.get_value("Employee",self.doc.employee,"division")
		section = frappe.db.get_value("Employee",self.doc.employee, "section")
		unit = frappe.db.get_value("Employee",self.doc.employee, "unit")
	
		if self.new_state.lower() == "Draft".lower():
			self.set_approver("Supervisor")
		elif self.new_state.lower() == "Waiting Supervisor Approval".lower():
			self.set_approver("Supervisor")
		elif self.new_state.lower() == "Verified By Supervisor".lower():
			if self.doc.approver != frappe.session.user:
				frappe.throw("Only {} can Forward / Reject this Application".format(self.doc.approver_name))
			if unit:
				section_approver = frappe.db.get_value(
					"Department Approver",
					{"parent": section, "parentfield": "leave_approvers", "idx": 1},
					"approver",
				)
				if section_approver:
					self.set_approver("Section Approver")
				else:
					self.set_approver("Division Approver")
			else:
				self.set_approver("Division Approver")

		elif self.new_state.lower() == "Waiting Approval".lower():
			if self.doc.approver != frappe.session.user:
				frappe.throw("Only {} can Forward / Reject this Application".format(self.doc.approver_name))
			self.set_approver("Division Approver")

		elif self.new_state.lower() == ("Approved".lower() or "Rejected".lower()):
			if self.doc.approver != frappe.session.user:
				frappe.throw("Only {} can Approve/ Reject this Application".format(self.doc.approver_name))
		
		elif self.new_state.lower() == "Cancelled".lower():
			if "HR User" not in frappe.get_roles(frappe.session.user):
				frappe.throw("Only HR User can Cancel this request")
		else:
			frappe.throw(_("Invalid Workflow State {}").format(self.doc.workflow_state))


	def material_request(self):
		if self.new_state.lower() in ("Draft".lower(), "Waiting Supervisor Approval".lower()):
			if self.new_state.lower() == ("Waiting Supervisor Approval".lower()):
				self.set_approver("Supervisor")	
		
		elif self.new_state.lower() == ("Waiting Approval".lower()):
			if self.doc.approver != frappe.session.user:
				frappe.throw("Only {} can Approve this Leave".format(self.doc.approver_name))
			self.set_approver("Division Approver")
		elif self.new_state.lower() == ("Approved".lower()):
			if self.doc.approver != frappe.session.user:
				frappe.throw("Only {} can Approve this Application".format(self.doc.approver_name))

		elif self.new_state.lower() == ("Rejected".lower()):
			if self.doc.approver != frappe.session.user:
				frappe.throw("Only {} can Reject this Application".format(self.doc.approver_name))
		else:
			frappe.throw(_("Invalid Workflow State {}").format(self.doc.workflow_state))
	def employee_transfer(self):
		if self.new_state.lower() in ("Draft".lower(), "Waiting Approval".lower()):
			if self.new_state.lower() == "Waiting Approval".lower():
				if "HR User" not in frappe.get_roles(frappe.session.user):
					frappe.throw("Only HR can Apply this Appeal")
			self.set_approver("HRGM")

		elif self.new_state.lower() in ("Approved".lower(), "Rejected".lower()):
			if self.doc.supervisor != frappe.session.user:
				frappe.throw("Only {} can Approved or Reject this document".format(self.doc.supervisor_name))

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

class NotifyCustomWorkflow:
	def __init__(self,doc):
		self.doc 			= doc
		self.old_state 		= self.doc.get_db_value("workflow_state")
		self.new_state 		= self.doc.workflow_state
		self.field_map 		= get_field_map()
		self.doc_approver	= self.field_map[self.doc.doctype]
		self.field_list		= ["user_id","employee_name","designation","name"]
		if self.doc.doctype not in ("Material Request","Asset Issue Details", "Imprest Advance", "Imprest Recoup"):
			self.employee   = frappe.db.get_value("Employee", self.doc.employee, self.field_list)
		elif self.doc.doctype in ("Imprest Advance", "Imprest Recoup"):
			self.employee   = frappe.db.get_value("Employee", self.doc.party, self.field_list)
		else:
			self.employee = frappe.db.get_value("Employee", {"user_id":self.doc.owner}, self.field_list)

	def notify_employee(self):
		if self.doc.doctype not in ("Material Request","Asset Issue Details","Project Capitalization", "Imprest Advance", "Imprest Recoup"):
			employee = frappe.get_doc("Employee", self.doc.employee)
		elif self.doc.doctype in ("Imprest Advance", "Imprest Recoup"):
			employee = frappe.get_doc("Employee", self.doc.party)
		else:
			employee = frappe.get_doc("Employee", frappe.db.get_value("Employee",{"user_id":self.doc.owner},"name"))
		
		if not employee.user_id:
			return

		parent_doc = frappe.get_doc(self.doc.doctype, self.doc.name)
		args = parent_doc.as_dict()

		if self.doc.doctype == "Leave Application":
			template = frappe.db.get_single_value('HR Settings', 'leave_application_status_notification_template')
			if not template:
				frappe.msgprint(_("Please set default template for Leave Application Status Notification in HR Settings."))
				return
		elif self.doc.doctype == "Leave Encashment":
			template = frappe.db.get_single_value('HR Settings', 'encashment_status_notification_template')
			if not template:
				frappe.msgprint(_("Please set default template for Encashment Status Notification in HR Settings."))
				return
		elif self.doc.doctype == "Employee Advance":
			template = frappe.db.get_single_value('HR Settings', 'employee_advance_status_notification_template')
			if not template:
				frappe.msgprint(_("Please set default template for Encashment Status Notification in HR Settings."))
				return
		elif self.doc.doctype == "Travel Request":
			template = frappe.db.get_single_value('HR Settings', 'travel_request_status_notification_template')
			if not template:
				frappe.msgprint(_("Please set default template for Travel Request Status Notification in HR Settings."))
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
		elif self.doc.doctype == "Employee Separation":
			template = frappe.db.get_single_value('HR Settings', 'employee_separation_status_notification_template')
			if not template:
				frappe.msgprint(_("Please set default template for Employee Separation Status Notification in HR Settings."))
				return
		elif self.doc.doctype == "Material Request":
			template = frappe.db.get_single_value('HR Settings', 'material_request_status_notification_template')
			if not template:
				frappe.msgprint(_("Please set default template for Material Request Status Notification in HR Settings."))
				return
		# elif self.doc.doctype == "Asset Issue Details":
		# 	template = frappe.db.get_single_value('HR Settings', 'asset_issue_status_notification_template')
		# 	if not template:
		# 		frappe.msgprint(_("Please set default template for Asset Issue Status Notification in HR Settings."))
		# 		return
		
		elif self.doc.doctype == "Imprest Advance":
			template = frappe.db.get_single_value('HR Settings', 'imprest_advance_status_notification_template')
			if not template:
				frappe.msgprint(_("Please set default template for Imprest Advance Status Notification in HR Settings."))
				return

		elif self.doc.doctype == "Imprest Recoup":
			template = frappe.db.get_single_value('HR Settings', 'imprest_recoup_status_notification_template')
			if not template:
				frappe.msgprint(_("Please set default template for Imprest Recoup Status Notification in HR Settings."))
				return
		
		elif self.doc.doctype == "Vehicle Request":
			template = frappe.db.get_single_value('Maintenance Settings', 'vehicle_request_status_notification_template')
			if not template:
				frappe.msgprint(_("Please set default template for Vehicle Request Status Notification in Maintenance Settings."))
				return
		else:
			template = ""

		if not template:
			frappe.msgprint(_("Please set default template for {}.").format(self.doc.doctype))
			return
		email_template = frappe.get_doc("Email Template", template)
		message = frappe.render_template(email_template.response, args)
		if employee :
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
				template = frappe.db.get_single_value('HR Settings', 'leave_application_approval_notification_template')
				if not template:
					frappe.msgprint(_("Please set default template for Leave Approval Notification in HR Settings."))
					return
			elif self.doc.doctype == "Leave Encashment":
				template = frappe.db.get_single_value('HR Settings', 'encashment_approval_notification_template')
				if not template:
					frappe.msgprint(_("Please set default template for Encashment Approval Notification in HR Settings."))
					return
			elif self.doc.doctype == "Employee Advance":
				template = frappe.db.get_single_value('HR Settings', 'employee_advance_approval_notification_template')
				if not template:
					frappe.msgprint(_("Please set default template for Encashment Approval Notification in HR Settings."))
					return
			elif self.doc.doctype == "Travel Request":
				template = frappe.db.get_single_value('HR Settings', 'travel_request_approval_notification_template')
				if not template:
					frappe.msgprint(_("Please set default template for Travel Request Approval Notification in HR Settings."))
					return
			elif self.doc.doctype == "Overtime Application":
				template = frappe.db.get_single_value('HR Settings', 'overtime_approval_notification_template')
				if not template:
					frappe.msgprint(_("Please set default template for Overtime Approval Notification in HR Settings."))
					return
			elif self.doc.doctype == "Employee Benefits":
				template = frappe.db.get_single_value('HR Settings', 'benefits_approval_notification_template')
				if not template:
					frappe.msgprint(_("Please set default template for Employee Benefits Approval Notification in HR Settings."))
					return
			elif self.doc.doctype == "Employee Separation":
				template = frappe.db.get_single_value('HR Settings', 'employee_separation_approval_notification_template')
				if not template:
					frappe.msgprint(_("Please set default template for Employee Separation Approval Notification in HR Settings."))
					return
			elif self.doc.doctype == "Material Request":
				template = frappe.db.get_single_value('HR Settings', 'material_request_approval_notification_template')
				if not template:
					frappe.msgprint(_("Please set default template for Material Request Approval Notification in HR Settings."))
					return

			# elif self.doc.doctype == "Asset Issue Details":
			# 	template = frappe.db.get_single_value('HR Settings', 'asset_issue_approval_notification_template')
			# 	if not template:
			# 		frappe.msgprint(_("Please set default template for Asset Issue Approval Notification in HR Settings."))
			# 		return
			
			elif self.doc.doctype == "Imprest Advance":
				template = frappe.db.get_single_value('HR Settings', 'imprest_advance_approval_notification_template')
				if not template:
					frappe.msgprint(_("Please set default template for Imprest Advance Approval Notification in HR Settings."))
					return

			elif self.doc.doctype == "Imprest Recoup":
				template = frappe.db.get_single_value('HR Settings', 'imprest_recoup_approval_notification_template')
				if not template:
					frappe.msgprint(_("Please set default template for Imprest Recoup Approval Notification in HR Settings."))
					return
			
			elif self.doc.doctype == "Vehicle Request":
				template = frappe.db.get_single_value('HR Settings', 'vehicle_request_approval_notification_template')
				if not template:
					frappe.msgprint(_("Please set default template for Vehicle Request Approval Notification in HR Settings."))
					return
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
		elif self.new_state in ("Approved", "Rejected", "Cancelled", "Claimed", "Submitted", "Recouped"):
			if self.doc.doctype == "Material Request" and self.doc.owner != "Administrator":
				self.notify_employee()
			else:
				self.notify_employee()
		elif self.new_state.startswith("Waiting") and self.old_state != self.new_state and self.doc.doctype not in ("Asset Issue Details","Project Capitalization", "Imprest Recoup"):
			self.notify_approver()
		# elif self.new_state.startswith("Waiting") and self.old_state != self.new_state and self.doc.doctype in ("Asset Issue Details","Project Capitalization"):
		# 	self.notify_finance_users()
		elif self.new_state.startswith("Verified") and self.old_state != self.new_state:
			self.notify_approver()
		else:
			frappe.msgprint(_("Email notifications not configured for workflow state {}").format(self.new_state))

def get_field_map():
	return {
		"Leave Encashment": ["approver","approver_name","approver_designation"],
		"Leave Application": ["leave_approver", "leave_approver_name", "leave_approver_designation"],
		"Travel Request": ["supervisor", "supervisor_name", "supervisor_designation"],
		"Employee Advance": ["advance_approver","advance_approver_name","advance_approver_designation"],
		"Overtime Application": ["approver", "approver_name", "approver_designation"],
		"Material Request": ["approver","approver_name","approver_designation"],
		"Asset Movement": ["approver", "approver_name", "approver_designation"],
		"Budget Reappropiation": ["approver", "approver_name", "approver_designation"],
		"Employee Transfer": ["supervisor", "supervisor_name", "supervisor_designation"],
		"Employee Benefits": ["benefit_approver","benefit_approver_name","benefit_approver_designation"],
		"Training Approval Request": [],
		"Employee Separation": ["approver","approver_name","approver_designation"],
		"Target Set Up": ["approver","approver_name","approver_designation"],
		"Imprest Advance": ["approver","approver_name","approver_designation"],
		"Imprest Recoup": ["approver","approver_name","approver_designation"],
		"Review": ["approver","approver_name","approver_designation"],
		"Performance Evaluation": ["approver","approver_name","approver_designation"],
		"Vehicle Request": ["approver_id", "approver"],
		"PMS Appeal":[],
		"Asset Issue Details": [],

	}

def validate_workflow_states(doc):
	wf = CustomWorkflow(doc)
	wf.apply_workflow()

def notify_workflow_states(doc):
	wf = NotifyCustomWorkflow(doc)
	wf.send_notification()

