# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
	validate_filters(filters)
	columns = get_columns()
	data = get_data(filters)

	return columns, data

def get_data(filters):
	data = []
	if filters.did:
		data = frappe.db.sql("""SELECT desuung_id, days_attended, start_date, end_date,
								deployment_title, deployment_category, location
								from `tabDeployment`
								where desuung_id = '{did}'
								order by start_date
							""".format(did=filters.did), as_dict=True)
	if data:
		return data
	else:
		frappe.throw("No Deployment recorded for Desuup {}".format(filters.did))

def validate_filters(filters):
	if not filters.did:
		frappe.throw(_("Cohort is missing. Please select cohort"))

def get_columns():
	return [
		{
		  "fieldname": "desuung_id",
		  "label": "DID",
		  "fieldtype": "Link",
		  "options": "Desuup",
		  "width": 130
		},
		{
		  "fieldname": "days_attended",
		  "label": "Day Attended",
		  "fieldtype": "Data",
		  "width": 100
		},
		{
		  "fieldname": "start_date",
		  "label": "Start Date",
		  "fieldtype": "Date",
		  "width": 120
		},
		{
		  "fieldname": "end_date",
		  "label": "End Date",
		  "fieldtype": "Date",
		  "width": 120
		},
		{
		  "fieldname": "deployment_title",
		  "label": "Deployment Title",
		  "fieldtype": "Link",
		  "options": "Deployment Title",
		  "width": 250
		},
		{
		  "fieldname": "deployment_category",
		  "label": "Deployment Category",
		  "fieldtype": "Link",
		  "options": "Deployment Category",
		  "width": 250
		},
		{
		  "fieldname": "location",
		  "label": "Location",
		  "fieldtype": "data",
		  "width": 150
		},
	]