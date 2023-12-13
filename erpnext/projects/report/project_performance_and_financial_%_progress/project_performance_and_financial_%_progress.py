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
			"fieldname": "performance_progress",
			"label": "Performance Progress",
			"fieldtype": "Percent",
			"width": 150
		},
		{
			"fieldname": "financial_progress",
			"label": "Financial Progress",
			"fieldtype": "Percent",
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
	data = []
	project_list = frappe.db.sql("""
			SELECT name, project_name, branch, status, boq_value, percent_complete, party_type, party from `tabProject` where boq_value > 500000 {}
			""".format(cond), as_dict = True)
	
	for d in project_list:
		financial_amt = frappe.db.sql("select IFNULL(SUM(gross_invoice_amount),0) from `tabProject Invoice` where docstatus = 1 and project = %s", (d.name))[0][0]

		row = {
			"project": d.name,
			"project_name": d.project_name,
			"branch": d.branch,
			"status": d.status,
			"performance_progress": d.percent_complete,
			"financial_progress": financial_amt / d.boq_value * 100,
			"party_type": d.party_type,
			"party": d.party,
			}

		data.append(row)

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



