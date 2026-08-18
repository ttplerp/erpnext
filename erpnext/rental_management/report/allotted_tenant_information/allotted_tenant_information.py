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
				"label": _("Tenant Name"),
				"fieldname": "tenant_name",
				"fieldtype": "Data",
				"width": 120,
			},
			{
				"label": _("Gender"),
				"fieldname": "gender",
				"fieldtype": "Data",
				"width": 100,
			},
			{
				"label": _("CID"),
				"fieldname": "cid",
				"fieldtype": "Data",
				"width": 100,
			},
			{
				"label": _("EMP ID"),
				"fieldname": "employee_id",
				"fieldtype": "Data",
				"width": 100,
			},
			{
				"label": _("Grade"),
				"fieldname": "grade",
				"fieldtype": "Data",
				"width": 100,
			},
			{
				"label": _("Designation"),
				"fieldname": "designation",
				"fieldtype": "Data",
				"width": 100,
			},
			{
				"label": _("Ministry/Agency"),
				"fieldname": "ministry_agency",
				"fieldtype": "Data",
				"width": 100,
			},
			{
				"label": _("Department"),
				"fieldname": "department",
				"fieldtype": "Data",
				"width": 100,
			},
			{
				"label": _("Old Flat No"),
				"fieldname": "old_flat_no",
				"fieldtype": "Date",
				"width": 150,
			},
			{
				"label": _("Initial Allotment Date"),
				"fieldname": "initial_allotment_date",
				"fieldtype": "Date",
				"width": 120,
			},
			{
				"label": _("Floor Area"),
				"fieldname": "total_floor_area",
				"fieldtype": "Data",
				"width": 100,
			},
			{
				"label": _("Current Rent"),
				"fieldname": "current_rent",
				"fieldtype": "Data",
				"width": 100,
			},
			{
				"label": _("Rate"),
				"fieldname": "rate_per_sqft",
				"fieldtype": "Currency",
				"width": 100,
			},
			{
				"label": _("Block"),
				"fieldname": "block",
				"fieldtype": "Data",
				"width": 100,
			},
			{
				"label": _("Flat"),
				"fieldname": "flat",
				"fieldtype": "Data",
				"width": 100,
			},
			{
				"label": _("Flat No ID"),
				"fieldname": "flat_no",
				"fieldtype": "Link",
				"options": "Flat No",
				"width": 100,
			},
			{
				"label": _("Block No ID"),
				"fieldname": "block_no",
				"fieldtype": "Link",
				"options": "Block No",
				"width": 100,
			},
			{
				"label": _("Eligible Building Classification"),
				"fieldname": "building_classification",
				"fieldtype": "Link",
				"options": "Building Classification",
				"width": 100,
			},
			{
				"label": _("Location"),
				"fieldname": "locations",
				"fieldtype": "Link",
				"options": "Locations",
				"width": 100,
			},
			{
				"label": _("Employment Type"),
				"fieldname": "employment_type",
				"fieldtype": "Data",
				"width": 100,
			},
			{
				"label": _("Application Date Time"),
				"fieldname": "application_date_time",
				"fieldtype": "Datetime",
				"width": 150,
			},
			{
				"label": _("Gross Salary"),
				"fieldname": "gross_salary",
				"fieldtype": "Currency",
				"width": 160,
			},
			{
				"label": _("Spouse Gross Salary"),
				"fieldname": "spouse_gross_salary",
				"fieldtype": "Currency",
				"width": 160,
			},
			{
				"label": _("Total Gross Salary"),
				"fieldname": "total_gross_salary",
				"fieldtype": "Currency",
				"width": 160,
			},
			{
				"label": _("Security Deposit"),
				"fieldname": "security_deposit",
				"fieldtype": "Currency",
				"width": 120,
			},
			{
				"label": _("Mobile No"),
				"fieldname": "mobile_no",
				"fieldtype": "Data",
				"width": 150,
			},
			{
				"label": _("Email ID"),
				"fieldname": "email_id",
				"fieldtype": "Date",
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
				"label": _("Spouse Name"),
				"fieldname": "spouse_name",
				"fieldtype": "Data",
				"width": 100,
			},
			{
				"label": _("Spouse CID"),
				"fieldname": "spouse_cid",
				"fieldtype": "Data",
				"width": 100,
			},
			{
				"label": _("Spouse Employment Type"),
				"fieldname": "spouse_employment_type",
				"fieldtype": "Data",
				"width": 100,
			},
			{
				"label": _("Spouse EMPP ID"),
				"fieldname": "spouse_employee_id",
				"fieldtype": "Data",
				"width": 100,
			},
			{
				"label": _("Spouse Designation"),
				"fieldname": "spouse_designation",
				"fieldtype": "Data",
				"width": 100,
			},
			{
				"label": _("Spouse Grade"),
				"fieldname": "spouse_grade",
				"fieldtype": "Data",
				"width": 100,
			},
			{
				"label": _("Spouse Ministry/Agency"),
				"fieldname": "spouse_ministry",
				"fieldtype": "Data",
				"width": 100,
			},
			{
				"label": _("Spouse Department"),
				"fieldname": "spouse_department",
				"fieldtype": "Data",
				"width": 100,
			},
			{
				"label": _("Last Increment"),
				"fieldname": "last_increment",
				"fieldtype": "Currency",
				"width": 100,
			},
			{
				"label": _("Next Increment"),
				"fieldname": "next_increment",
				"fieldtype": "Currency",
				"width": 100,
			},
			{
				"label": _("Status"),
				"fieldname": "status",
				"fieldtype": "Data",
				"width": 100,
			},
		]
	
	return columns

def get_data(filters):
	cond=''
	# if filters.get("rental_official"):
	# 	cond = " and rb.rental_focal='{}'".format(filters.get("rental_official"))
	if filters.get("ministry_agency"):
		cond += " and ha.ministry_agency='{}'".format(filters.get("ministry_agency"))
	if filters.get("dzongkhag"):
		cond += " and ha.dzongkhag='{}'".format(filters.get("dzongkhag"))
	if filters.get("building_classification"):
		cond += " and ha.building_classification='{}'".format(filters.get("building_classification"))
	if filters.get("locations"):
		cond += " and ti.locations='{}'".format(filters.get("location"))
	# if filters.get("department"):
	# 	cond += " and rb.tenant_department='{}'".format(filters.get("department"))

	query = """select 
				COALESCE(ha.applicant_name, ti.tenant_name) as tenant_name, ha.gender, ha.cid, ha.employee_id, ha.grade, ha.designation, ha.ministry_agency, 
				ha.department, ha.old_flat_no, ti.initial_allotment_date, ti.total_floor_area, trc.rental_amount as current_rent, ti.rate_per_sqft,
				ti.block, ti.flat, ti.flat_no, ti.block_no, ha.building_classification, ti.locations, ha.employment_type, ha.application_date_time, ha.gross_salary,
				ha.spouse_gross_salary, ha.total_gross_salary, ti.security_deposit, ha.mobile_no, ha.email_id, ha.marital_status, ha.work_station, ha.spouse_name,
				ha.spouse_cid, ha.spouse_employment_type, ha.spouse_employee_id, ha.spouse_designation, ha.spouse_grade, ha.spouse_ministry, ha.spouse_department, 
				trc.increment as last_increment, ti.status, ti.name as ti_name, trc.idx
			from `tabHousing Application` ha
			left join `tabTenant Information` ti 
			on ha.name=ti.housing_application 
			left join `tabTenant Rental Charges` trc
			on ti.name = trc.parent and trc.from_date between '{from_date}' and '{to_date}'
			where ha.application_date_time between '{from_date}' and '{to_date}' {cond} group by ha.name order by ha.name
		""".format(from_date=filters.get("from_date"), to_date=filters.get("to_date"), cond=cond)
	
	result = frappe.db.sql(query, as_dict=1)
	for i in result:
		next_increment = frappe.db.get_value(
			"Tenant Rental Charges",
			filters={
				"parent": i.ti_name,
				"idx": (i.idx or 0) + 1
			},
			fieldname="increment"
		)
		i["next_increment"] = next_increment if next_increment else 0

	return result
