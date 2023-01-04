# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import flt, get_datetime, nowdate

class VehicleRequest(Document):
	def validate(self):
		if get_datetime(self.from_date) > get_datetime(self.to_date):
			frappe.throw("To Date/Time cannot be earlier then From Date/Time")
		if not self.posting_date:
			self.posting_date = nowdate()
		self.check_duplicate()
		if self.workflow_state == "Rejected":
			if not self.rejection_reason:
				frappe.throw("Rejection Reason Is Mandatory")
		self.update_verifier_approver()

	def update_verifier_approver(self):
		if frappe.db.exists("Employee", {"user_id":frappe.session.user}):
			verifier_approver = frappe.db.get_value("Employee", {"user_id":frappe.session.user}, "employee_name")
			approver_designation = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "designation")
		else:
			verifier_approver = frappe.session.user

		if self.workflow_state == "Approved":
			self.approver = str(verifier_approver)
			self.approver_designation = str(approver_designation)
		elif self.workflow_state == "Verified By Supervisor":
			self.verifier = str(verifier_approver)

	def on_submit(self):
		self.check_if_free()
		self.send_email()

	def on_cancel(self):
		frappe.db.sql(""" delete from `tabEquipment Reservation Entry` where vehicle_request = '{0}'""".format(self.name)) 

	def check_duplicate(self):
		found = []
		for a in self.items:
			if a.employee in found:
				frappe.throw("Employee <b> '{0}' </b> already added in the list".format(a.employee))
			else:
				found.append(a.employee)

	def check_if_free(self):
		result = frappe.db.sql("""
										select equipment
										from `tabEquipment Reservation Entry`
										where equipment = '{0}'
										and docstatus = 1 and reason = 'On Duty'
										and ('{1}' between concat(from_date,' ',from_time) and concat(to_date,' ',to_time)
												or
												'{2}' between concat(from_date,' ',from_time) and concat(to_date,' ',to_time)
												or
												('{3}' <= concat(from_date,' ',from_time) and '{4}' >= concat(to_date,' ',to_time))
										)
								""".format(self.equipment, self.from_date, self.to_date, self.from_date, self.to_date), as_dict=True)
		if result:
			frappe.throw("<b> '{0}' </b> is currently in use".format(result[0]))

	def update_reservation_entry(self):
		import datetime
		from_time = datetime.datetime.strptime(self.from_date, '%Y-%m-%d %H:%M:%S')
		to_time = datetime.datetime.strptime(self.to_date, '%Y-%m-%d %H:%M:%S')
		doc = frappe.new_doc("Equipment Reservation Entry")
		doc.equipment = self.equipment
		doc.vehicle_request = self.name
		doc.reason = "On Duty"
		doc.ehf_name = "On Duty" 
		doc.from_date = self.from_date
		doc.to_date = self.to_date
		doc.from_time = from_time.time()
		doc.to_time = to_time.time()
		doc.submit()

	def send_email(self):
		email = self.owner
		subject = "Vehicle Request"
		message = "Your Vehicle Request <b> '{0}' </b> has been '{1}'".format(self.name, self.workflow_state)
		if self.workflow_state == 'Approved':
			message = "Your Vehicle Request <b> '{0}' </b> has been Approved".format(self.name)

		frappe.msgprint("{0}".format(message))
		try:
			frappe.sendmail(recipients=email, sender=None, subject=subject, message=message)
		except:
			pass

