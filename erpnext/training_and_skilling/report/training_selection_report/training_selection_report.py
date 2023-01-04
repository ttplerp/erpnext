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
	if filters.cohort and filters.course:	
		data = frappe.db.sql("""SELECT t.domain, t.course_name as course, 
								i.did, i.desuup_name, i.email, i.mobile, i.status, i.final_point, 
								i.selection_rank, i.confirmation_status, i.confirmation_remark
								FROM `tabTraining Selection` t
								inner join `tabTraining Selection Item` i
								on t.name = i.parent
								where t.cohort = '{cohort}'
								and t.course = '{course}'
								order by confirmation_status, selection_rank
							""".format(cohort=filters.cohort, course=filters.course), as_dict=True)
	if data:
		return data
	else:
		frappe.throw("No such Training Selection for {} and {}".format(filters.cohort, filters.course))

def validate_filters(filters):
	if not filters.cohort:
		frappe.throw(_("Cohort is missing. Please select cohort"))

	if not filters.course:
		frappe.throw("Please select course to generate report")

def get_columns():
	return [
		{
		  "fieldname": "domain",
		  "label": "Domain",
		  "fieldtype": "Link",
		  "options": "Cost Center",
		  "width": 110
		},
		{
		  "fieldname": "course",
		  "label": "Course",
		  "fieldtype": "Link",
		  "options": "Course",
		  "width": 200
		},
		{
		  "fieldname": "did",
		  "label": "Desuung ID",
		  "fieldtype": "Link",
		  "options": "Desuup",
		  "width": 130
		},
		{
		  "fieldname": "desuup_name",
		  "label": "Name",
		  "fieldtype": "Data",
		  "width": 150
		},
		{
		  "fieldname": "final_point",
		  "label": "Total Point",
		  "fieldtype": "Data",
		  "width": 100
		},
		{
		  "fieldname": "selection_rank",
		  "label": "Rank",
		  "fieldtype": "Data",
		  "width": 60
		},
		{
		  "fieldname": "status",
		  "label": "Status",
		  "fieldtype": "Data",
		  "width": 110
		},
		{
		  "fieldname": "confirmation_status",
		  "label": "Confirmation Status",
		  "fieldtype": "data",
		  "width": 70
		},
				{
		  "fieldname": "email",
		  "label": "Email",
		  "fieldtype": "Data",
		  "width": 200
		},
		{
		  "fieldname": "mobile",
		  "label": "Mobile",
		  "fieldtype": "Data",
		  "width": 120
		},
		{
		  "fieldname": "confirmation_remark",
		  "label": "Confirmation Remark",
		  "fieldtype": "data",
		  "width": 200
		},
	]
