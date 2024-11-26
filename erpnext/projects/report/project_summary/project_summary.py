'''
--------------------------------------------------------------------------------------------------------------------------
Version		 	Author		  				CreatedOn		 	ModifiedOn		  	Remarks
------------ --------------- ------------------ -------------------  -----------------------------------------------------
1.0		      	Dawa Nyuehtyue Tshering		2024/11/20			2024/11/20			Original Version
--------------------------------------------------------------------------------------------------------------------------			
'''

import frappe
from frappe import _
from frappe.utils import flt

def execute(filters=None):
	project_list = get_project_list(filters)
	for project in project_list:
		project["total_tasks"] = frappe.db.count("Task", filters={"project": project.name})
		project["completed_tasks"] = frappe.db.count(
			"Task", filters={"project": project.name, "status": "Completed"}
		)
		project["working_tasks"] = frappe.db.count(
			"Task", filters={"project": project.name, "status": "Working"}
		)
	data = get_data(project_list)
	columns = get_columns(filters)	
	chart = get_chart_data(project_list)
	report_summary = get_report_summary(project_list)

	return columns, data, None, None, report_summary

def get_project_list(filters):
	return frappe.db.get_all(
		"Project",
		filters=filters,
		fields=[
			"name",
			"project_name",
			"project_value",
			"cost_center",
			"status",
			"percent_complete",
			"expected_start_date",
			"expected_end_date",
			"project_type",
		],
		order_by="expected_end_date",
	)

def get_data(project_list):
	data = []
	for project in project_list:
		total_expense_amount = total_income_amount = 0.0
		
		prj_income = get_total_income(project['cost_center'])
		prj_expense = get_total_expense(project['cost_center'])
		
		total_income_amount += flt(prj_income, 2)
		total_expense_amount += flt(prj_expense, 2)
		net_profit = flt(total_income_amount - total_expense_amount, 2)

		data.append({
			"project": project['name'],
			"project_name": project['project_name'],
			"cost_center": project['cost_center'],
			"project_type": project['project_type'],
			"expected_start_date": project['expected_start_date'],
			"expected_end_date": project['expected_end_date'],
			"total_tasks": project['total_tasks'],
			"completed_tasks": project['completed_tasks'],
			"working_tasks": project['working_tasks'],
			"percent_complete": project['percent_complete'],
			"status": project['status'],
			"project_value": project['project_value'],
			"project_income": total_income_amount,
			"project_expense": total_expense_amount,
			"net_profit": net_profit,
		})
	return data

def get_columns(filters):
	return [
		{"fieldtype": "Link",	"fieldname": "project", "label": _("Project"),  "options": "Project", "width": 200},
		{"fieldtype": "Data",	"fieldname": "project_name", "label": _("Project Name"), "width": 200},
		{"fieldtype": "Link",	"fieldname": "cost_center", "label": _("Cost Center"), "options": "Cost Center", "width": 180},
		{"fieldtype": "Float",	"fieldname": "project_value", "label": _("Project Value (Nu.)"),  "width": 200},
		{"fieldtype": "Float",	"fieldname": "project_income", "label": _("Income (Nu.)"), "width": 150},
		{"fieldtype": "Float",	"fieldname": "project_expense", "label": _("Expense (Nu.)"), "width": 150},
		{"fieldtype": "Float",	"fieldname": "net_profit", "label": _("Net Profit (Nu.)"), "width": 150},
		{"fieldtype": "Link", 	"fieldname": "project_type", "label": _("Type"),  "options": "Project Type", "width": 120},
		{"fieldtype": "Date",	"fieldname": "expected_start_date","label": _("Start Date"),  "width": 120},
		{"fieldtype": "Date",	"fieldname": "expected_end_date", "label": _("End Date"),  "width": 120},
		{"fieldtype": "Data", 	"fieldname": "total_tasks",	"label": _("Total Tasks"),  "width": 120},
		{"fieldtype": "Data", 	"fieldname": "completed_tasks",	"label": _("Tasks Completed"), "width": 120},
		{"fieldtype": "Data", 	"fieldname": "working_tasks",	"label": _("Tasks Inprogress"), "width": 120},
		{"fieldtype": "Data",	"fieldname": "percent_complete", "label": _("% Completion"),  "width": 120},
		{"fieldtype": "Data",	"fieldname": "status", "label": _("Status"),  "width": 120},
	]

def get_chart_data(data):
	labels = []
	total = []
	completed = []
	working = []

	for project in data:
		labels.append(project.name)
		total.append(project.total_tasks)
		completed.append(project.completed_tasks)
		working.append(project.working_tasks)

	return {
		"data": {
			"labels": labels[:30],
			"datasets": [
				{"name": "Completed", "values": completed[:30]},
				{"name": "Total Tasks", "values": total[:30]},
				{"name": "Working Tasks", "values": total[:30]},
			],
		},
		"type": "bar",
		"colors": ["#fc4f51", "#78d6ff", "#7575ff"],
		"barOptions": {"stacked": True},
	}

def get_report_summary(data):
	if not data:
		return None

	avg_completion = sum(project.percent_complete for project in data) / len(data)
	total = sum([project.total_tasks for project in data])
	working_tasks = sum([project.working_tasks for project in data])
	completed = sum([project.completed_tasks for project in data])

	return [
		{
			"value": avg_completion,
			"indicator": "Green" if avg_completion > 50 else "Red",
			"label": _("Average Completion"),
			"datatype": "Percent",
		},
		{
			"value": total,
			"indicator": "Blue",
			"label": _("Total Tasks"),
			"datatype": "Int",
		},
		{
			"value": completed,
			"indicator": "Green",
			"label": _("Completed Tasks"),
			"datatype": "Int",
		},
		{
			"value": working_tasks,
			"indicator": "Grey",
			"label": _("Working Tasks"),
			"datatype": "Int",
		},
	]

def get_total_income(cost_center):
	query = """
		SELECT
			SUM(t1.credit - t1.debit) AS total_amount
		FROM 
			`tabGL Entry` t1, `tabAccount` t2
		WHERE t1.account = t2.name
		and t2.root_type = 'Income'
		and t1.docstatus = 1
		AND t1.is_cancelled = 0
		AND t1.cost_center = %s
		GROUP BY t1.cost_center
	"""
	result = frappe.db.sql(query, (cost_center,), as_dict=True)
	if result:
		return result[0].get('total_amount', 0)
	else:
		return 0

def get_total_expense(cost_center):
	query = """
		SELECT
			SUM(t1.debit - t1.credit) AS total_amount
		FROM 
			`tabGL Entry` t1, `tabAccount` t2
		WHERE t1.account = t2.name
		and t2.root_type = 'Expense'
		and t1.docstatus = 1
		AND t1.is_cancelled = 0
		AND t1.cost_center = %s
		GROUP BY t1.cost_center
	"""
	result = frappe.db.sql(query, (cost_center,), as_dict=True)
	if result:
		return result[0].get('total_amount', 0)
	else:
		return 0