# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from frappe.utils import flt
from frappe.utils import flt, get_datetime, nowdate, cint, datetime, date_diff, time_diff
from erpnext.custom_workflow import validate_workflow_states, notify_workflow_states

class VehicleRequest(Document):
	def validate(self):
		validate_workflow_states(self)
		self.check_duplicate_entry()
		self.calculate_time()
		self.check_date()
		self.fetch_departrure_time()
		if self.kilometer_reading:
			if flt(self.previous_km) > flt(self.kilometer_reading):
				frappe.throw("Kilometer reading must be greater than previous kilometer reading.")
		if self.workflow_state != "Approved":
			notify_workflow_states(self)

	def on_submit(self):
		self.check_vehicle()
		notify_workflow_states(self)

	def check_duplicate_entry(self):
		data = frappe.db.sql("""
			SELECT vehicle, employee
			FROM `tabVehicle Request`
			WHERE vehicle = '{0}'
			AND docstatus = 1 AND status = 'Booked'
		""".format(self.vehicle), as_dict=1)
		
		if data:
			frappe.throw("Vehicle <b>{}</b> is already booked by Employee <b>{}</b>".format(self.vehicle_number, data[0].employee))

	def check_vehicle(self):
		if not self.vehicle:
			frappe.throw("Vehicle is Mandatory")
	
	def calculate_time(self):
		time = time_diff(self.to_date, self.from_date)
		self.total_days_and_hours=time
		return time  

	def fetch_departrure_time(self):
		if self.workflow_state == "Waiting Approval":
			get_time = self.from_date
			self.time_of_departure = get_time  

	def  check_date(self):
		if self.from_date > self.to_date:
			frappe.throw("From Date cannot be before than To Date")
	
	@frappe.whitelist()
	def open_the_vehicle_for_booking(self):
		if self.docstatus == 1 and self.status == "Booked":
			self.db_set("status", "Closed")

@frappe.whitelist()  
def check_form_date_and_to_date(from_date, to_date):
	if from_date > to_date:
		frappe.throw("From Date cannot be before than To Date")

@frappe.whitelist()
def create_logbook(source_name, target_doc=None):
	doclist = get_mapped_doc("Vehicle Request", source_name, {
		"Vehicle Request": {
			"doctype": "Vehicle Logbook"
		},
	}, target_doc)

	return doclist

@frappe.whitelist()
def get_previous_km(vehicle, vehicle_number):
	return frappe.db.sql(""" 
		SELECT 
			vr.kilometer_reading as km
		FROM `tabVehicle Request` vr 
		WHERE vr.vehicle ='{}' and vr.vehicle_number='{}' 
		ORDER BY vr.creation DESC LIMIT 1 """.format(vehicle, vehicle_number),as_dict=1)

@frappe.whitelist()
def get_operator(equipment, posting_date):
    return frappe.db.sql(""" 
        SELECT 
            eo.operator as driver
        FROM `tabEquipment` e
        JOIN `tabEquipment Operator` eo ON eo.parent = e.name
        WHERE e.name = %s AND eo.start_date <= %s AND (eo.end_date IS NULL OR eo.end_date >= %s)
        LIMIT 1 
    """, (equipment, posting_date, posting_date), as_dict=1)

@frappe.whitelist()
def create_vr_extension(source_name, target_doc=None):
	doclist = get_mapped_doc("Vehicle Request", source_name, {
		"Vehicle Request": {
			"doctype": "Vehicle Request Extension",
			"field_map": {
				"vehicle_request": "name",
				"from_date":"from_date",
				"to_date":"to_date"
			}
		},
	}, target_doc)

	return doclist

def get_permission_query_conditions(user):
	if not user: user = frappe.session.user
	user_roles = frappe.get_roles(user)

	if user == "Administrator" or "System Manager" in user_roles: 
		return
		
	if "Fleet Manager" in user_roles:
		return

	if "ADM User" in user_roles or "Fleet User" in user_roles:
		return """(
			exists(select 1
				from `tabEmployee` as e
				where e.branch = `tabVehicle Request`.branch
				and e.user_id = '{user}')
			or
			exists(select 1
				from `tabEmployee` e, `tabAssign Branch` ab, `tabBranch Item` bi
				where e.user_id = '{user}'
				and ab.employee = e.name
				and bi.parent = ab.name
				and bi.branch = `tabVehicle Request`.branch)
		)""".format(user=user)
	else:
		return """(
			exists(select 1
				from `tabEmployee` as e
				where e.name = `tabVehicle Request`.employee
				and e.user_id = '{user}')
		)""".format(user=user)