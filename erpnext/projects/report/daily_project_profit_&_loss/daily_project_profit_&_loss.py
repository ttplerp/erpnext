# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt

def execute(filters=None):
	data = get_data(filters)
	columns = get_columns(filters)
	return columns, data

def get_data(filters):
	data = []
	cond = cond1 = ""
	if filters.cost_center:
		cond += " and cost_center = '{}'".format(filters.cost_center)
		cond1 += " and t1.cost_center = '{}'".format(filters.cost_center)
	if filters.project:
		cond += " and name = '{}'".format(filters.project)

	project_lsit = frappe.db.sql("""
				select name, cost_center, project_name, project_value
				from `tabProject`
				where status = "Open"	
				{}	
			""".format(cond), as_dict=True)
	
	record_measurement_query = """
		SELECT
			t1.project,
			t1.cost_center,
			SUM(t1.amount) AS amount
		FROM `tabRecord Of Measurement` t1
		WHERE t1.docstatus = 1
		AND t1.posting_date = '{}' {}
		GROUP BY t1.cost_center
	""".format(filters.date, cond1)
	
	income_data = frappe.db.sql(record_measurement_query, as_dict=True)

	mess_expense 		= get_mess_data(filters)
	hsd_expense 		= get_hsd_data(filters)
	material_expense 	= get_material_data(filters)
	piu_expense 		= get_piu_data(filters)
	labour_expense 		= get_labour_expense(filters)

	for project in project_lsit:
		total_expense = total_income = 0.0

		income = next((item for item in income_data if item['project'] == project['name']), None)
		if income:
			total_income += income.get('amount', 0.0)
		
		mess = next((item for item in mess_expense if item['cost_center'] == project['cost_center']), None)
		if mess:
			total_expense += mess.get('expense_amount', 0.0)
		
		hsd = next((item for item in hsd_expense if item['cost_center'] == project['cost_center']), None)
		if hsd:
			total_expense += hsd.get('expense_amount', 0.0)
		
		material = next((item for item in material_expense if item['cost_center'] == project['cost_center']), None)
		if material:
			total_expense += material.get('expense_amount', 0.0)

		piu = next((item for item in piu_expense if item['cost_center'] == project['cost_center']), None)
		if piu:
			total_expense += piu.get('daily_rate', 0.0)

		labour = next((item for item in labour_expense if item['cost_center'] == project['cost_center']), None)
		if labour:
			total_expense += labour.get('amount', 0.0)
		
		profit_loss = flt(total_income - total_expense, 2)
		
		data.append({
			"project": project['name'],
			"project_name": project['project_name'],
			"cost_center": project['cost_center'],
			"project_value": project['project_value'],
			"income": total_income,
			"expense": total_expense,
			"profit_loss": profit_loss
		})
	
	return data

def get_mess_data(filters):
	cond = ""
	if filters.cost_center:
		cond += " and cost_center = '{}'".format(filters.cost_center)

	query = """
		SELECT 
			cost_center,
			SUM(amount) AS expense_amount
		FROM `tabProject Mess Management`
		WHERE docstatus = 1
		AND posting_date = '{}' {}
		GROUP BY cost_center
	""".format(filters.date, cond)
	return frappe.db.sql(query, as_dict=True)

def get_hsd_data(filters):
	cond = ""
	if filters.cost_center:
		cond = "AND t1.cost_center = '{}'".format(filters.cost_center)
	query = """
		SELECT 
			t1.cost_center,
			SUM(t2.amount) AS expense_amount
		FROM `tabPOL Issue` t1, `tabPOL Issue Items` t2
		WHERE t1.name = t2.parent
		AND t1.docstatus = 1
		AND t1.posting_date = '{}' {}
		GROUP BY t1.cost_center
	""".format(filters.date, cond)
	return frappe.db.sql(query, as_dict=True)

def get_material_data(filters):
	cond = ""
	if filters.cost_center:
		cond += " AND sed.cost_center = '{}'".format(filters.cost_center)
	query = """
		SELECT
			sed.cost_center,
			SUM(sed.amount) AS expense_amount
		FROM `tabStock Entry` se
		JOIN `tabStock Entry Detail` sed ON se.name = sed.parent
		WHERE se.docstatus = 1
		AND se.posting_date = '{}' {}
		GROUP BY sed.cost_center
	""".format(filters.date, cond)
	return frappe.db.sql(query, as_dict=True)

def get_piu_data(filters):
	cond = ""
	if filters.cost_center:
		cond = "AND t1.cost_center='{0}'".format(filters.cost_center)
	query = """
				SELECT 
					t1.cost_center,
					sum(t3.amount / 30) AS daily_rate
				FROM 
					`tabEmployee` t1
				JOIN 
					`tabSalary Structure` t2 ON t1.employee = t2.employee
				JOIN 
					`tabSalary Detail` t3 ON t2.name = t3.parent
				WHERE 
					t1.status = 'Active'
					AND t3.salary_component = 'Basic Pay' {}
				GROUP BY t1.cost_center
			""".format(cond)
	return frappe.db.sql(query, as_dict=True)

def get_labour_expense(filters):
	cond = ""
	if filters.cost_center:
		cond += " AND mre.cost_center='{0}'".format(filters.cost_center)

	regular_query = """
		SELECT
			mre.cost_center,
			SUM(
				(CASE WHEN mra.status = 'Present' THEN 1 ELSE 0 END) * mre.rate_per_day
			) AS amount
		FROM 
			`tabMuster Roll Employee` mre
		JOIN
			`tabMuster Roll Attendance` mra ON mre.name = mra.mr_employee
		WHERE
			mre.status = 'Active'
			AND mra.date = '{0}' {1}
		GROUP BY
			mre.cost_center
	""".format(filters.date, cond)

	overtime_query = """
		SELECT
			mre.cost_center,
			SUM(mroe.number_of_hours * mre.rate_per_hour) AS amount
		FROM
			`tabMuster Roll Employee` mre
		JOIN
			`tabMuster Roll Overtime Entry` mroe ON mre.name = mroe.mr_employee
		WHERE
			mre.status = 'Active'
			AND mroe.docstatus = 1
			AND mroe.date = '{0}' {1}
		GROUP BY
			mre.cost_center
	""".format(filters.date, cond)

	regular_expense_data = frappe.db.sql(regular_query, as_dict=True)
	overtime_expense_data = frappe.db.sql(overtime_query, as_dict=True)

	total_expense_by_cost_center = {}

	for row in regular_expense_data:
		cost_center = row['cost_center']
		if cost_center not in total_expense_by_cost_center:
			total_expense_by_cost_center[cost_center] = 0.0
		total_expense_by_cost_center[cost_center] += row['amount']

	for row in overtime_expense_data:
		cost_center = row['cost_center']
		if cost_center not in total_expense_by_cost_center:
			total_expense_by_cost_center[cost_center] = 0.0
		total_expense_by_cost_center[cost_center] += row['amount']

	labour_expense = []
	for cost_center, total_amount in total_expense_by_cost_center.items():
		labour_expense.append({
			"cost_center": cost_center,
			"amount": total_amount
		})

	return labour_expense


def get_columns(filters):
	columns = [
		{"fieldname": "project", 		"fieldtype": "Link",	"label": _("Project"), 	"options": "Project", "width": 250},
		{"fieldname": "project_name",	"fieldtype": "Data",	"label": _("Project Name"), "width": 250},
		{"fieldname": "cost_center", 	"fieldtype": "Link",	"label": _("Cost Center"), "options": "Cost Center", "width": 250},
		{"fieldname": "project_value",	"fieldtype": "Float",	"label": _("Project Value (Nu)"), "width": 200},
		{"fieldname": "income", 		"fieldtype": "Float",	"label": _("Income/Work Done (Nu)"), "width": 200},
		{"fieldname": "expense",		"fieldtype": "Float",	"label": _("Expense (Nu)"),	"width": 150},
		{"fieldname": "profit_loss",	"fieldtype": "Data",	"label": _("Profit/Loss (Nu)"),	"width": 200},
	]
	return columns

