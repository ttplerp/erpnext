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
					"label":"name1",
					"fieldtype":"data",
					"options":"",
					"width":160
				},
		{
					"fieldname":"cash_in_hand",
					"label":"Cash in Hand",
					"fieldtype":"data",
					"options":"",
					"width":160
				},
		{
					"fieldname":"bob_cd",
					"label":"BOB CD",
					"fieldtype":"data",
					"options":"",
					"width":160
				},
		{
					"fieldname":"pnb_cd",
					"label":"PNB CD",
					"fieldtype":"data",
					"options":"",
					"width":160
				},
		{
					"fieldname":"bnb_cd",
					"label":"BNB CD",
					"fieldtype":"data",
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
					"label":"Cash",
					"fieldtype":"data",
					"options":"",
					"width":160
				},
		{
					"fieldname":"currency",
					"label":"Currency",
					"fieldtype":"data",
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
	# 
	data = frappe.db.sql(
					'''
				SELECT  SUM(CASE WHEN a.parent_account = "11.300 - Cash In Hand Account"  THEN gl.debit - gl.credit ELSE 0 END) AS cash_in_hand, 
	SUM(CASE WHEN (a.name = "11.201 - BOB - 100896320 - CD" or a2.name = "11.201 - BOB - 100896320 - CD" or a3.name = "11.201 - BOB - 100896320 - CD")  THEN gl.debit - gl.credit ELSE 0 END) AS bob_cd,
	SUM(CASE WHEN (a.name = "11.202 - BNB - 0000057046001 - CD" or a2.name = "11.202 - BNB - 0000057046001 - CD" or a3.name = "11.202 - BNB - 0000057046001 - CD")  THEN gl.debit - gl.credit ELSE 0 END) AS bnb_cd,
	SUM(CASE WHEN (a.name = "11.204 - PNB - 110210010626 - CD" or a2.name = "11.204 - PNB - 110210010626 - CD" or a3.name = "11.204 - PNB - 110210010626 - CD")  THEN gl.debit - gl.credit ELSE 0 END) AS pnb_cd
				FROM `tabGL Entry` AS gl INNER JOIN `tabAccount` AS a ON gl.account = a.name INNER JOIN `tabAccount` AS a2 ON a.parent_account = a2.name INNER JOIN `tabAccount` AS a3 ON a2.parent_account = a3.name and gl.is_cancelled = 0;
		'''.format(conditions=conditions),as_dict=1)
	# else:
	# 	data = frappe.db.sql(
	# 				'''
	# 				SELECT a.name as name2, SUM(CASE WHEN a.parent_account = "11.300 - Cash In Hand Account"  THEN gl.debit - gl.credit ELSE 0 END
	# 				) AS cash, sum(fe.amount) as currency if fe.exchange_type='buy'  FROM `tabGL Entry` AS gl left JOIN `tabAccount` AS a ON gl.account = a.name inner join `tabForeign Exchange` as fe on
	# 				fe.journal_entry=gl.voucher_no where a.parent_account="11.300 - Cash In Hand Account" group by a.name ;
	# 		'''.format(conditions=conditions),as_dict=1)
		
		
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

