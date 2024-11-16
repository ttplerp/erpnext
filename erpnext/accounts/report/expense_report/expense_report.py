# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	columns, data = get_columns(filters), get_data(filters)
	return columns, data

def get_columns(filters):
    if filters.get("is_gross_profit"):
        return [
		{
					"fieldname":"cost_center",
					"label":"Cost Center",
					"fieldtype":"data",
					"options":"",
					"width":160
				},
		{
					"fieldname":"total_expense",
					"label":"Total Expense",
					"fieldtype":"Currency",
					"options":"",
					"width":160
				},
		{
					"fieldname":"total_income",
					"label":"Income",
					"fieldtype":"Currency",
					"options":"",
					"width":160
				},
		{
					"fieldname":"total_direct_expense",
					"label":"Direct Expense",
					"fieldtype":"Currency",
					"options":"",
					"width":160
				},
	
				{
					"fieldname":"gross_profit",
					"label":"Gross Profit",
					"fieldtype":"Currency",
					"options":"",
					"width":160
				},
	
	
		
	
	
			]
    else:
        return [
		{
					"fieldname":"cost_center",
					"label":"Cost Center",
					"fieldtype":"data",
					"options":"",
					"width":160
				},
		{
					"fieldname":"total_expense",
					"label":"Total Expense",
					"fieldtype":"Currency",
					"options":"",
					"width":160
				},
		{
					"fieldname":"total_income",
					"label":"Income",
					"fieldtype":"Currency",
					"options":"",
					"width":160
				},
		{
					"fieldname":"total_direct_expense",
					"label":"Direct Expense",
					"fieldtype":"Currency",
					"options":"",
					"width":160
				},
		{
					"fieldname":"total_indirect_expense",
					"label":"Indirect Expense",
					"fieldtype":"Currency",
					"options":"",
					"width":160
				},
				{
					"fieldname":"gross_profit",
					"label":"Gross Profit",
					"fieldtype":"Currency",
					"options":"",
					"width":160
				},
	
	
		{
					"fieldname":"profit",
					"label":"Net Profit",
					"fieldtype":"Currency",
					"options":"",
					"width":160
				},
	
	
			]

def get_data(filters):
	conditions = get_conditions(filters)
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
	
	data = frappe.db.sql(
	 			'''
				SELECT
					gl.cost_center,
					SUM(CASE WHEN a.root_type = "Income" THEN gl.credit - gl.debit ELSE 0 END) AS total_income,
					SUM(CASE WHEN a.root_type IN ("Expense", "Depreciation", "Stock Adjustment") THEN gl.debit - gl.credit ELSE 0 END) AS total_expense,
					SUM(CASE WHEN a.root_type = "Income" THEN gl.credit - gl.debit ELSE 0 END) -
					SUM(CASE WHEN a.root_type IN ("Expense", "Depreciation", "Stock Adjustment") THEN gl.debit - gl.credit ELSE 0 END) AS profit,
					SUM(
						CASE 
							WHEN (a2.parent_account = "51 - Direct Expenses" or a3.parent_account = "51 - Direct Expenses")
							THEN gl.debit - gl.credit 
							ELSE 0 
						END
					) AS total_direct_expense,
					SUM(
						CASE 
							WHEN (a2.parent_account = "60 - Indirect Expense" or a3.parent_account = "60 - Indirect Expense")
							THEN gl.debit - gl.credit 
							ELSE 0 
						END
					) AS total_indirect_expense,
					SUM(CASE WHEN a.root_type = "Income" THEN gl.credit - gl.debit ELSE 0 END) - 
					SUM(
						CASE 
							WHEN (a2.parent_account = "51 - Direct Expenses" or a3.parent_account = "51 - Direct Expenses") 
							THEN gl.debit - gl.credit 
							ELSE 0 
						END
					) AS gross_profit
				FROM
					`tabGL Entry` AS gl
				INNER JOIN
					`tabAccount` AS a ON gl.account = a.name
				INNER JOIN
					`tabAccount` AS a2 ON a.parent_account = a2.name
				INNER JOIN
					`tabAccount` AS a3 ON a2.parent_account = a3.name
				WHERE
					gl.company = "VAJRA BUILDERS PRIVATE LIMITED" 
					and gl.cost_center is not null
					{conditions}
				GROUP BY 
					gl.cost_center;

 		'''.format(conditions=conditions),as_dict=1)
	
	return data


def get_conditions(filters):
	conditions = []
	if filters and filters.get("fiscal_year"):
		conditions.append("fiscal_year = '{}'".format(filters.get("fiscal_year")))
	if filters.get("monthly"):
		conditions.append("MONTH(gl.posting_date) = '{}'".format(filters.get("monthly")))
	if filters and filters.get("cost_center"):
		conditions.append("gl.cost_center = '{}'".format(filters.get("cost_center")))

	return "AND {}".format(" AND ".join(conditions)) if conditions else ""

