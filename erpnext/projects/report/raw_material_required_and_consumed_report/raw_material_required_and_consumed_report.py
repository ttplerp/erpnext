# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import flt, cint, nowdate, getdate, formatdate

def execute(filters=None):
	columns = get_columns()
	cond = get_conditions(filters)
	query = construct_query(cond)
	data = get_data(query, filters)
	return columns, data

def construct_query(cond):
	query = """
		SELECT
			name, project_name, branch, status,
			project_type, percent_complete
		FROM
			`tabProject`
		WHERE
			is_active = 'Yes' {}
	""".format(cond)
	return query

def get_columns():
	return [
		{
			"fieldname": "project",
			"label": "Project",
			"fieldtype": "Link",
			"options": "Project",
			"width": 120
		},
		{
			"fieldname": "project_name",
			"label": "Project Name",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "project_branch",
			"label": "Project Branch",
			"fieldtype": "Link",
			"options": "Branch",
			"width": 120
		},
		# {
		# 	"fieldname": "project_type",
		# 	"label": "Project Type",
		# 	"fieldtype": "Data",
		# 	"width": 120
		# },
		{
			"fieldname": "per_comp",
			"label": "Percent Completed",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "project_status",
			"label": "Project Status",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "item",
			"label": "Item Code",
			"fieldtype": "Link",
			"options": "Item",
			"width": 120
		},
		{
			"fieldname": "item_name",
			"label": "Item Name",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "reqd_qty",
			"label": "Required Qty",
			"fieldtype": "Float",
			"width": 120
		},
		{
			"fieldname": "cons_qty",
			"label": "Consumed Qty",
			"fieldtype": "Float",
			"width": 120
		},
		{
			"fieldname": "bal_qty",
			"label": "Balance Qty",
			"fieldtype": "Float",
			"width": 100
		},
		{
			"fieldname": "con_percent",
			"label": "Consumed %",
			"fieldtype": "Percent",
			"width": 120
		}
	]

def get_conditions(filters):
	cond = ''
	# if filters.from_date > filters.to_date :
	# 	frappe.throw("From Date cannot be before than To Date")
	if filters.project:
		cond += " AND name = '{}'".format(filters.project)
	if filters.status:
		cond += " AND status = '{}'".format(filters.status)
	return cond

def get_data(query, filters):
	data = []
	active_projects = frappe.db.sql(query, as_dict=True)

	for project in active_projects:
		required_qty = frappe.db.sql("""
					SELECT bsr.item_code, bsr.item_name, SUM(bi.quantity * bsr.qty) AS total_req_qty,
					(SELECT SUM(sd.qty) FROM `tabStock Entry Detail` sd WHERE sd.item_code = bsr.item_code AND sd.project = %s AND sd.docstatus = 1) AS consumed
					FROM `tabBOQ` b
					JOIN `tabBOQ Item` bi ON bi.parent = b.name
					JOIN `tabBSR Raw Item` bsr ON bsr.parent = bi.boq_code
					WHERE b.docstatus = 1 AND b.workflow_state = 'Approved' AND b.project = %s
					GROUP BY bsr.item_code
			""", (project.name, project.name), as_dict=True)

		for row in required_qty:
			row = {
				"project": project.name,
				"project_name": project.project_name,
				"project_branch": project.branch,
				# "project_type": project.project_type,
				"per_comp": project.percent_complete,
				"project_status": project.status,
				"item": row.item_code,
				"item_name": row.item_name,
				"reqd_qty":  flt(row.total_req_qty) if row.total_req_qty else 0,
				"cons_qty":  flt(row.consumed) if row.consumed else 0,
				"bal_qty":  flt(row.total_req_qty) - flt(row.consumed),
				"con_percent":  flt(row.consumed) / flt(row.total_req_qty) * 100 if row.total_req_qty else 0,
			}
			data.append(row)
	return data

		


