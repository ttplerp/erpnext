# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt
import frappe
from frappe.model.document import Document
from erpnext.custom_utils import check_future_date
from frappe.utils import flt, cint,getdate,time_diff_in_hours
from frappe import _, qb, throw
from frappe.model.mapper import get_mapped_doc

class Logbook(Document):
	def validate(self):
		check_future_date(self.posting_date)
		self.check_date_validity()
		self.calculate_hours()
		self.check_duplicate_entry()
	
	def on_submit(self):
		self.update_ehf_status()
	
	def on_cancel(self):
		self.update_ehf_status()

	def update_ehf_status(self):
		ehf = frappe.get_doc("Equipment Hiring Form", self.equipment_hiring_form)
		ehf.run_method("validate")
		ehf.save(ignore_permissions=True)

	def check_duplicate_entry(self):
		if self.from_date and self.to_date:
			query = """select name, equipment_hiring_form from `tabLogbook` where equipment = '{equipment}' and 
						docstatus in (1, 0) and ('{from_date}' between from_date and to_date OR 
						'{to_date}' between from_date and to_date OR ('{from_date}' <= from_date AND 
						'{to_date}' >= to_date)) and name != '{vl_name}'
						""" .format(from_date=self.from_date, to_date=self.to_date, vl_name=self.name, equipment=self.equipment)
			
			result = frappe.db.sql(query, as_dict=1)

		for a in result:
			frappe.throw("The logbook for the same Equipment and date has been created at <b>{}</b>".format(frappe.get_desk_link("Logbook", a.name)))

	def check_date_validity(self):
		if self.from_date and self.to_date:
			if getdate(self.from_date) > getdate(self.to_date):
				frappe.throw("Logbook From Date cannot be greater than To Date")

			from_date, to_date = frappe.db.get_value("Equipment Hiring Form", self.equipment_hiring_form, ["start_date", "end_date"])
			
			if getdate(self.from_date) < getdate(from_date):
				frappe.throw("Log From Date cannot be less than equipment hiring From date <b>{0}</b>".format(from_date))
			
			if getdate(self.to_date) > getdate(to_date):
				frappe.throw("Log To Date cannot be greater than equipment hiring To date <b>{0}</b>".format(to_date))
	
	def check_target_hour(self):
		if self.equipment_hiring_form:
			self.target_hours = frappe.db.get_value("Equipment Hiring Form", self.equipment_hiring_form, "target_hour")
		if flt(self.scheduled_working_hour) <= 0:
			frappe.throw("Scheduled Working Hour is mandatory")
		if flt(self.target_hours) <= 0:
			frappe.throw("Target Hour is mandatory")
	
	def calculate_hours(self):
		total_hours = tot_idle = 0
		total_km =  0
		for a in self.items:
			a.equipment = self.equipment
			if (flt(a.initial_hour) >= 0 and flt(a.final_hour) >= 0) or (flt(a.initial_km) >= 0 and flt(a.final_km)):
				if flt(a.initial_hour) > flt(a.final_hour):
					frappe.throw("Final reading should be greater than inital reading")
				elif flt(a.initial_km) > flt(a.final_km):
					frappe.throw("Final KM should be greater than inital KM")
				
				a.hours = flt(a.final_hour) - flt(a.initial_hour) - flt(a.idle_time)
				a.total_km = flt(a.final_km) - flt(a.initial_km)
				total_hours += flt(round(a.hours,1))
				total_km += flt(round(a.total_km,1))
				tot_idle += flt(round(a.idle_time,1))
			else:
				frappe.throw("Initial and Final Readings are mandatory")

		self.total_hours = round(total_hours,1)
		self.total_km_reading = round(total_km,1)
		self.total_idle_hour = round(tot_idle,1)
	
