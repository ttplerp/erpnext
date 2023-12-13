# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import flt

def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data

def get_columns():
	return [
		{
			"fieldname": "project",
			"label": "Project",
			"fieldtype": "Link",
			"options": "Project",
			"width": 160
		},
		{
			"fieldname": "project_name",
			"label": "Project Name",
			"fieldtype": "Data",
			"width": 200
		},
		{
			"fieldname": "branch",
			"label": "Branch",
			"fieldtype": "Link",
			"options": "Branch",
			"width": 160
		},
		{
			"fieldname": "status",
			"label": "Project Status",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "project_budget",
			"label": "Project Value",
			"fieldtype": "Currency",
			"width": 150
		},
		{
			"fieldname": "revenue_calculated",
			"label": "Revenue",
			"fieldtype": "Currency",
			"width": 150
		},
		{
			"fieldname": "party_type",
			"label": "Party Type",
			"fieldtype": "Link",
			"options": "Party Type",
			"width": 100
		},
		{
			"fieldname": "party",
			"label": "Party",
			"fieldtype": "Dynamic Link",
			"options": "party_type",
			"width": 160
		}
	]

def get_data(filters):
	cond = get_conditions(filters)
	data = frappe.db.sql("""
			SELECT name, project_name, branch, status, boq_value, consultancy_charge, party_type, party from `tabProject` where boq_value > 500000 {}
			""".format(cond))

	return data

def get_conditions(filters):
	conditions = ""
	if filters.get("project"):
		conditions += " and name = \'" + str(filters.project) + "\'"

	if filters.get("branch"):
		conditions += " and branch = \'" + str(filters.branch) + "\'"
	
	if filters.get("is_active"):
		conditions += " and is_active = \'" + str(filters.is_active) + "\'"
	
	return conditions



