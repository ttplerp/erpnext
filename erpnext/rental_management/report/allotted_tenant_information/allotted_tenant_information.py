# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _, _dict
from frappe.utils import cstr, today, getdate, flt


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
				"fieldname": "ministry_and_agency",
				"fieldtype": "Data",
				"width": 100,
			},
			{
				"label": _("Tenant Department"),
				"fieldname": "tenant_department",
				"fieldtype": "Link",
				"options": "Tenant Department",
				"width": 100,
			},
			{
				"label": _("Old Flat No"),
				"fieldname": "old_flat_no",
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
				"label": _("Land"),
				"fieldname": "land",
				"fieldtype": "Currency",
				"width": 100,
			},
			{
				"label": _("Building"),
				"fieldname": "building",
				"fieldtype": "Currency",
				"width": 100,
			},
			{
				"label": _("Garbage"),
				"fieldname": "garbage",
				"fieldtype": "Currency",
				"width": 100,
			},
			{
				"label": _("Amenities"),
				"fieldname": "amenities",
				"fieldtype": "Currency",
				"width": 100,
			},
			{
				"label": _("MTC"),
				"fieldname": "mtc",
				"fieldtype": "Currency",
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
				"label": _("Last Increment Date"),
				"fieldname": "increment_from_date",
				"fieldtype": "Date",
				"width": 100,
			},
			{
				"label": _("Next Increment Date"),
				"fieldname": "increment_to_date",
				"fieldtype": "Date",
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
	trc_cond=''
	if filters.get("from_date") and filters.get("to_date"):
		trc_cond = " and trc.from_date between '{0}' and '{1}'".format(filters.get("from_date"), filters.get("to_date"))
		cond = " and ha.application_date_time between '{0}' and '{1}'".format(filters.get("from_date"), filters.get("to_date"))
	if filters.get("ministry_agency"):
		cond += " and ti.ministry_and_agency='{}'".format(filters.get("ministry_agency"))
	if filters.get("dzongkhag"):
		cond += " and ti.dzongkhag='{}'".format(filters.get("dzongkhag"))
	if filters.get("building_classification"):
		cond += " and ti.building_classification='{}'".format(filters.get("building_classification"))
	if filters.get("locations"):
		cond += " and ti.locations='{}'".format(filters.get("location"))
	if filters.get("status"):
		cond += " and ti.status='{}'".format(filters.get("status"))
	if filters.get("flat_no"):
		cond += " and fn.name='{}'".format(filters.get("flat_no"))
	if filters.get("old_flat_no"):
		cond += " and fn.old_flat_no like '%{}%'".format(filters.get("old_flat_no"))

	query = """select 
				COALESCE(ha.applicant_name, ti.tenant_name) as tenant_name, ha.gender, ti.tenant_cid as cid, ha.employee_id, ha.grade, ha.designation, ti.ministry_and_agency, 
				ti.tenant_department, fn.old_flat_no, ti.initial_allotment_date, ti.total_floor_area, trc.rental_amount as current_rent, ti.rate_per_sqft, ti.block, ti.flat, 
				ti.flat_no, ti.block_no, ti.building_classification, ti.locations, ti.employment_type, ha.application_date_time, ha.gross_salary, ti.security_deposit, ha.mobile_no,
				ha.email_id, ha.marital_status, ha.work_station, COALESCE(trc.increment, 0) as last_increment, ti.status, ti.name as ti_name, trc.idx,
				CASE
					WHEN ha.marital_status = 'Divorced' THEN NULL
					ELSE ha.spouse_gross_salary
				END AS spouse_gross_salary,

				CASE
					WHEN ha.marital_status = 'Divorced' THEN NULL
					ELSE ha.spouse_name
				END AS spouse_name,

				CASE
					WHEN ha.marital_status = 'Divorced' THEN NULL
					ELSE ha.spouse_cid
				END AS spouse_cid,

				CASE
					WHEN ha.marital_status = 'Divorced' THEN NULL
					ELSE ha.spouse_dzongkhag
				END AS spouse_dzongkhag,

				CASE
					WHEN ha.marital_status = 'Divorced' THEN NULL
					ELSE ha.spouse_gewog
				END AS spouse_gewog,

				CASE
					WHEN ha.marital_status = 'Divorced' THEN NULL
					ELSE ha.spouse_dob
				END AS spouse_dob,

				CASE
					WHEN ha.marital_status = 'Divorced' THEN NULL
					ELSE ha.spouse_village
				END AS spouse_village,

				CASE
					WHEN ha.marital_status = 'Divorced' THEN NULL
					ELSE ha.spouse_employment_type
				END AS spouse_employment_type,

				ha.gross_salary +
				CASE
					WHEN ha.marital_status = 'Married'
						THEN IFNULL(ha.spouse_gross_salary, 0)
					ELSE 0
				END AS total_gross_salary
			from `tabTenant Information` ti
			left join `tabHousing Application` ha 
			on ha.name = ti.housing_application 
			left join `tabFlat No` fn
			on ti.flat_no = fn.name 
			left join `tabTenant Rental Charges` trc
			on ti.name = trc.parent {trc_cond}
			where ti.docstatus = 1 {cond} group by ti.name order by ti.name
		""".format(trc_cond=trc_cond, cond=cond)
	# frappe.msgprint(str(query))
	result = frappe.db.sql(query, as_dict=1)
	current_date = getdate(today())

	for i in result:
		# rental_charge = frappe.db.get_value(
		# 	"Tenant Rental Charges",
		# 	filters={
		# 		"parent": i.ti_name,
		# 		"idx": (i.idx or 0) + 1
		# 	},
		# 	fieldname=["increment", "from_date", "to_date"],
		# 	as_dict=True
		# )

		to_date = frappe.db.get_value(
			"Tenant Rental Charges",
			{
				"parent": i.ti_name,
				"from_date": ["<=", current_date],
				"to_date": [">=", current_date]
			},
			"to_date",
		)
		rental_charge = None
		if to_date:
			rental_charge = frappe.db.get_value(
				"Tenant Rental Charges",
				filters={
					"parent": i.ti_name,
					"from_date": [">=", to_date]
				},
				fieldname=["increment", "from_date", "to_date"],
				as_dict=True,
				order_by="from_date asc"
			)

		if rental_charge:
			i["next_increment"] = rental_charge.increment or 0
			i["increment_from_date"] = rental_charge.from_date
			i["increment_to_date"] = rental_charge.to_date
		else:
			i["next_increment"] = 0
			i["increment_from_date"] = None
			i["increment_to_date"] = None

		land = building = garbage = amenities = mtc = 0

		land = frappe.db.get_value("Property Management Item", filters={"parent": i.flat_no, "property_management_type": "Land"}, fieldname="amount")
		building = frappe.db.get_value("Property Management Item", filters={"parent": i.flat_no, "property_management_type": "Building/ under development"}, fieldname="amount")
		garbage = frappe.db.get_value("Property Management Item", filters={"parent": i.flat_no, "property_management_type": "Garbage collection"}, fieldname="amount")
		amenities = frappe.db.get_value("Property Management Item", filters={"parent": i.flat_no, "property_management_type": "Amenities service fee"}, fieldname="amount")
		mtc = frappe.db.get_value("Property Management Item", filters={"parent": i.flat_no, "property_management_type": "Mtc cost (Service Charge)"}, fieldname="amount")

		i["land"] = land
		i["building"] = building
		i["garbage"] = garbage
		i["amenities"] = amenities
		i["mtc"] = mtc

	return result
