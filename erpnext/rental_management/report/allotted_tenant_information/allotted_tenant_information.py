# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _, _dict
from frappe.utils import cstr, getdate, flt


def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data

def get_columns():
	columns = [
			{
				"label": _("Housing Application Item"),
				"fieldname": "housing_application_id",
				"fieldtype": "Link",
				"options": "Housing Application",
				"width": 120,
			},
			{
				"label": _("Application Date"),
				"fieldname": "application_date_time",
				"fieldtype": "Date",
				"width": 150,
			},
			{
				"label": _("CID"),
				"fieldname": "cid",
				"fieldtype": "Data",
				"width": 100,
			},
			{
				"label": _("Gender"),
				"fieldname": "gender",
				"fieldtype": "Data",
				"width": 100,
			},
			{
				"label": _("Marital Status"),
				"fieldname": "marital_status",
				"fieldtype": "Data",
				"width": 100,
			},
			{
				"label": _("Place of Application (Work Station)"),
				"fieldname": "work_station",
				"fieldtype": "Data",
				"width": 100,
			},
			{
				"label": _("Employment Type"),
				"fieldname": "employment_type",
				"fieldtype": "Data",
				"width": 100,
			},
			{
				"label": _("Tenant ID"),
				"fieldname": "tenant_id",
				"fieldtype": "Link",
				"options": "Tenant Information",
				"width": 150,
			},
			{
				"label": _("Location Id"),
				"fieldname": "locations",
				"fieldtype": "Link",
				"options": "Locations",
				"width": 160,
			},
			{
				"label": _("Block No"),
				"fieldname": "block_no",
				"fieldtype": "Data",
				"width": 120,
			},
			{
				"label": _("Flat No"),
				"fieldname": "flat_no",
				"fieldtype": "Data",
				"width": 150,
			},
			{
				"label": _("Initial Allotment Date"),
				"fieldname": "initial_allotment_date",
				"fieldtype": "Date",
				"width": 120,
			},
			{
				"label": _("Allocated Date"),
				"fieldname": "allocated_date",
				"fieldtype": "Date",
				"width": 100,
			},
			{
				"label": _("Inital Rental Amount"),
				"fieldname": "initial_rental_amount",
				"fieldtype": "Currency",
				"width": 100,
			},
			{
				"label": _("Rental Term Year"),
				"fieldname": "rental_term_year",
				"fieldtype": "Date",
				"width": 100,
			},
			
		]
	
	return columns

def get_data(filters):
	cond=''
	# if filters.get("rental_official"):
	# 	cond = " and rb.rental_focal='{}'".format(filters.get("rental_official"))
	# if filters.get("ministry_agency"):
	# 	cond += " and rb.ministry_agency='{}'".format(filters.get("ministry_agency"))
	# if filters.get("dzongkhag"):
	# 	cond += " and rb.dzongkhag='{}'".format(filters.get("dzongkhag"))
	# if filters.get("building_category"):
	# 	cond += " and rb.building_category='{}'".format(filters.get("building_category"))
	# if filters.get("location"):
	# 	cond += " and rb.location_id='{}'".format(filters.get("location"))
	# if filters.get("department"):
	# 	cond += " and rb.tenant_department='{}'".format(filters.get("department"))

	query = """select 
				ha.name as housing_application_id, ha.application_date_time, ha.cid,
				ha.gender, ha.marital_status, ha.work_station, ha.employment_type,
				ti.name as tenant_id, ti.locations, ti.block_no, ti.flat_no,
				ti.initial_allotment_date, ti.allocated_date, ti.initial_rental_amount,
				ti.rental_term_year
			from `tabHousing Application` ha
			left join `tabTenant Information` ti 
			on ha.name=ti.housing_application 
			where ha.docstatus=1 and ha.application_status = "Allotted" and ha.application_date_time between '{from_date}' and '{to_date}' {cond} group by ha.name order by ha.name
		""".format(from_date=filters.get("from_date"), to_date=filters.get("to_date"), cond=cond)
	
	result = frappe.db.sql(query, as_dict=1)
	return result
