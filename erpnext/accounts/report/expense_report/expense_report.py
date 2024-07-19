# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	columns, data = get_columns(filters), get_data(filters)
	return columns, data

def get_columns(filters):
	return [
			{
				"fieldname":"cost_center",
				"label":"cost_center",
				"fieldtype":"data",
				"options":"",
				"width":160
			},
   {
				"fieldname":"total_expense",
				"label":"total_expense",
				"fieldtype":"data",
				"options":"",
				"width":160
			},
   {
				"fieldname":"total_income",
				"label":"total_income",
				"fieldtype":"data",
				"options":"",
				"width":160
			},
    {
				"fieldname":"profit",
				"label":"profit",
				"fieldtype":"data",
				"options":"",
				"width":160
			},
		]

def get_data(filters):
	data = []
	# data = frappe.db.sql('''
	# 					SELECT gl.cost_center, 
	#   SUM(gl.debit - gl.credit) AS net_expense 
	#   FROM `tabGL Entry` as gl 
	#   inner join 
	#   `tabAccount` as a 
	#   on 
	#   gl.account = a.name where 
	#   a.account_type="Expense Account" and gl.company="VAJRA BUILDERS PRIVATE LIMITED"  group by gl.cost_center''',as_dict=1)
	
	data = frappe.db.sql('''
						SELECT
	gl.cost_center,
	SUM(CASE WHEN a.root_type = "Income" THEN gl.credit - gl.debit ELSE 0 END) AS total_income,
	SUM(CASE WHEN a.root_type in ("Expense", "Depreciation","Stock Adjustment") THEN gl.debit - gl.credit ELSE 0 END) AS total_expense,
	SUM(CASE WHEN a.account_type = "Income Account" THEN gl.credit - gl.debit ELSE 0 END) -
	SUM(CASE WHEN a.account_type = "Expense Account" THEN gl.debit - gl.credit ELSE 0 END) AS profit
FROM
	`tabGL Entry` AS gl
INNER JOIN
	`tabAccount` AS a
ON
	gl.account = a.name
WHERE
	gl.company = "VAJRA BUILDERS PRIVATE LIMITED" and fiscal_year="2024"
GROUP BY
	gl.cost_center''',as_dict=1)
	
	return data
