# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data

def get_columns(filters=None):
    if not filters.get("individual"):
        return [
		{
			"fieldname": "account",
			"label": "Account",
			"fieldtype": "Data",
			"width": 300
		},
		{
			"fieldname": "total_receivable",
			"label": "Total Receivable",
			"fieldtype": "Currency",
			"width": 300
		},
		{
			"fieldname": "total_received",
			"label": "Total Received",
			"fieldtype": "Currency",
			"width": 300
		},
		{
			"fieldname": "receivable_balance",
			"label": "Receivable Balance",
			"fieldtype": "Currency",
			"width": 300
			},
		
		]
    else:
        return [
		{
				"fieldname": "account",
				"label": "Account",
				"fieldtype": "Data",
				"width": 250
		},
		{
				"fieldname": "party",
				"label": "Party",
				"fieldtype": "Data",
				"width": 250
		},
		{
				"fieldname": "party_type",
				"label": "Party Type",
				"fieldtype": "Data",
				"width": 200
		},
			{
				"fieldname": "total_receivable",
				"label": "Total Receivable",
				"fieldtype": "Currency",
				"width": 150
		},
		{
				"fieldname": "total_received",
				"label": "Total Received",
				"fieldtype": "Currency",
				"width": 150
		},
		{
				"fieldname": "receivable_balance",
				"label": "Receivable Balance",
				"fieldtype": "Currency",
				"width": 150
		},
		]
		

def get_data(filters):
	conditions = get_conditions(filters)
	if not filters.get("individual"):
		query = '''
			SELECT gl.account, sum(gl.debit) as total_receivable, sum(gl.credit) as total_received, sum(gl.credit-gl.debit) as receivable_balance  
   			FROM  `tabGL Entry` AS gl INNER JOIN `tabAccount` AS a ON gl.account = a.name left join        
      		`tabCustomer` c on c.name=gl.party WHERE 
 			a.parent_account = "11.1 - Accounts Receivable"          
    		and gl.is_cancelled=0 {conditions} group by gl.account;
		'''.format(conditions=conditions)
		data = frappe.db.sql(query, as_dict=1)
		return data
	else:
		query='''
			SELECT gl.account,gl.party,gl.party_type, sum(gl.debit) as total_receivable, sum(gl.credit) as total_received, 
   			sum(gl.credit-gl.debit) as receivable_balance FROM  `tabGL Entry` AS gl INNER JOIN `tabAccount` AS a ON gl.account = a.name left join   
           `tabCustomer` c on c.name=gl.party WHERE a.parent_account = "11.1 - Accounts Receivable" and gl.is_cancelled=0 {conditions}
           group by gl.party;
		'''.format(conditions=conditions)
		data = frappe.db.sql(query, as_dict=1)
		return data
	 
def get_conditions(filters):
	conditions = []
	if filters and filters.get("customer"):
		conditions.append("c.name = '{}'".format(filters.get("customer")))
	if filters and filters.get("cost_center"):
		conditions.append("gl.cost_center = '{}'".format(filters.get("cost_center")))
	if filters and filters.get("fiscal_year"):
		conditions.append("gl.fiscal_year = '{}'".format(filters.get("fiscal_year")))
	if filters and filters.get("account"):
		conditions.append("gl.account = '{}'".format(filters.get("account")))
	

	return "AND {}".format(" AND ".join(conditions)) if conditions else ""
