# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from frappe.utils import flt, date_diff
import frappe
def execute(filters=None):
	columns, data = [], []
	columns = get_columns(data)
	queries = construct_query(filters)
	data = get_data(queries,filters)
	
	return columns, data

def get_columns(data):
	return [
		{
			"fieldname": "project",
			"label": "Project ID",
			"fieldtype": "Link",
			"options": "Project",
			"width": 200
		},
		{
			"fieldname": "task",
			"label": "Task ID",
			"fieldtype": "Link",
			"options": "Task",
			"width": 200
		},
		{
			"fieldname": "e_start_date",
			"label": "Expected Start Date",
			"fieldtype": "Date",
			"width": 120
		},
		{
			"fieldname": "e_end_date",
			"label": "Expected End Date",
			"fieldtype": "Date",
			"width": 120
		},
		{
			"fieldname": "e_days",
			"label": "Expected Days",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "a_start_date",
			"label": "Actual Start Date",
			"fieldtype": "Date",
			"width": 120
		},
		{
			"fieldname": "a_end_date",
			"label": "Actual End Date",
			"fieldtype": "Date",
			"width": 120
		},
		{
			"fieldname": "a_days",
			"label": "Actual Days",
			"fieldtype": "Data",
			"width": 120
		},
	]

def construct_query(filters=None):
	conditions, filters = get_conditions(filters)
	query = ("""
			select 
				t.project as project, t.name as task, t.exp_start_date as e_start_date, t.exp_end_date as e_end_date, t.act_start_date as a_start_date,t.act_end_date as a_end_date
			from `tabTask` t 
			where t.docstatus != 2
			{conditions}
			""".format(conditions=conditions))
	return query	
def get_data(query, filters):
	data = []
	datas = frappe.db.sql(query, as_dict=True)
	for d in datas:
		e_days = date_diff(d.e_end_date, d.e_start_date)
		a_days = date_diff(d.a_end_date, d.a_start_date)
		if filters.get("branch"):
			branch = frappe.db.sql("""
					select branch as branch 
					from `tabProject` 
					where name ='{0}' 
				""".format(d.project),as_dict=True)
			in_branch = [d.branch for d in branch]
			if filters.get("branch") in in_branch:
				row = {
					"project": d.project,
					"task": d.task,
					"e_start_date": d.e_start_date,
					"e_end_date": d.e_end_date,
					"e_days": e_days,
					"a_start_date": d.a_start_date,
					"a_end_date":d.a_end_date,
					"a_days":a_days
				}
				data.append(row)
		else:
			row = {
				"project": d.project,
				"task": d.task,
				"e_start_date": d.e_start_date,
				"e_end_date": d.e_end_date,
				"e_days": e_days,
				"a_start_date": d.a_start_date,
				"a_end_date":d.a_end_date,
				"a_days":a_days
			}
			data.append(row)
	return data
def get_conditions(filters):
	conditions = ""
	if filters.get("from_date"):
		conditions += """and t.exp_start_date >='{}'""".format(filters.get("from_date"))
	if filters.get("to_date"):
		conditions += """and t.exp_end_date <= '{}'""".format(filters.get("to_date"))
	return conditions, filters

