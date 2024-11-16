# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	columns, data = get_columns(filters), get_data(filters)
	return columns, data

def get_columns(filters):
	if not filters.get("cash_in_hand"):
		return [
		{
					"fieldname":"name1",
					"label":"Name",
					"fieldtype":"data",
					"options":"",
					"width":160
				},
		{
					"fieldname":"cash_in_hand",
					"label":"Cash in Hand",
					"fieldtype":"Currency",
					"options":"",
					"width":160
				},
		{
					"fieldname":"bob_cd",
					"label":"BOB CD",
					"fieldtype":"Currency",
					"options":"",
					"width":160
				},
		{
					"fieldname":"pnb_cd",
					"label":"PNB CD",
					"fieldtype":"Currency",
					"options":"",
					"width":160
				},
		{
					"fieldname":"bnb_cd",
					"label":"BNB CD",
					"fieldtype":"Currency",
					"options":"",
					"width":160
				},
		#  {
		# 			"fieldname":"project_imprest",
		# 			"label":"project_imprest",
		# 			"fieldtype":"data",
		# 			"options":"",
		# 			"width":160
		# 		},
		
	
	
		
	
	
			]
	else:
		return [
      
		
		{
					"fieldname":"name2",
					"label":"Account",
					"fieldtype":"data",
					"options":"",
					"width":160
				},
		{
					"fieldname":"cash",
					"label":"Amount",
					"fieldtype":"Currency",
					"options":"",
					"width":160
				},
		
		{
					"fieldname":"matched_name2",
					"label":"Foriegn Currency Value",
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
	if not filters.get("cash_in_hand"):
		data = frappe.db.sql(
					'''
					SELECT  SUM(CASE WHEN a.parent_account = "11.300 - Cash In Hand Account"  THEN gl.debit - gl.credit ELSE 0 END) AS cash_in_hand, 
		SUM(CASE WHEN (a.name = "11.201 - BOB - 100896320 - CD" or a2.name = "11.201 - BOB - 100896320 - CD" or a3.name = "11.201 - BOB - 100896320 - CD")  THEN gl.debit - gl.credit ELSE 0 END) AS bob_cd,
		SUM(CASE WHEN (a.name = "11.202 - BNB - 0000057046001 - CD" or a2.name = "11.202 - BNB - 0000057046001 - CD" or a3.name = "11.202 - BNB - 0000057046001 - CD")  THEN gl.debit - gl.credit ELSE 0 END) AS bnb_cd,
		SUM(CASE WHEN (a.name = "11.204 - PNB - 110210010626 - CD" or a2.name = "11.204 - PNB - 110210010626 - CD" or a3.name = "11.204 - PNB - 110210010626 - CD")  THEN gl.debit - gl.credit ELSE 0 END) AS pnb_cd
					FROM `tabGL Entry` AS gl INNER JOIN `tabAccount` AS a ON gl.account = a.name INNER JOIN `tabAccount` AS a2 ON a.parent_account = a2.name INNER JOIN `tabAccount` AS a3 ON a2.parent_account = a3.name and gl.is_cancelled = 0;

			'''.format(conditions=conditions),as_dict=1)
	else:
		data2 = frappe.db.sql(
					'''
					SELECT SUM(CASE WHEN fe.exchange_type = 'Buy' THEN fe.amount WHEN fe.exchange_type = 'Sell' 
     				THEN -fe.amount ELSE 0 END ) AS name2, currency as cash FROM
         			`tabForeign Exchange` AS fe GROUP BY  fe.currency;
				'''.format(conditions=conditions),as_dict=1)
		data = frappe.db.sql(
					'''
					SELECT      a.name AS name2,      SUM(CASE WHEN a.parent_account = "11.300 - Cash In Hand Account" THEN gl.debit - gl.credit ELSE 0 END) AS cash FROM      
     				`tabGL Entry` AS gl INNER JOIN      `tabAccount` AS a ON gl.account = a.name WHERE      
         			a.parent_account = "11.300 - Cash In Hand Account" GROUP BY      a.name;
				'''.format(conditions=conditions),as_dict=1)
		accounts = frappe.db.sql(
					'''
					select name, account from `tabCurrency` ;	
		'''.format(conditions=conditions),as_dict=1)
		# Iterate and match data, adding columns where matches are found
		for row in data:
			for acc in accounts:
				if row['name2'] == acc['account']:
					for d2 in data2:
						if acc['name'] == d2['cash']:
							
							# Add the matched `name2` from `data2` to `data`
							row['matched_name2'] = d2['name2']
							

	# frappe.throw(str(data))
		
	for row in data:
		row["name1"] = "Accounts"
	
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

