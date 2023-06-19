# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

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
			"fieldname": "cost_center",
			"label": "Cost Center",
			"fieldtype": "Link",
			"options": "Cost Center",
			"width": 200
		},
		{
			"fieldname": "account",
			"label": "Account",
			"fieldtype": "Link",
			"options": "Account",
			"width": 200
		},
		{
			"fieldname": "account_number",
			"label": "Account Number",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "initial_target",
			"label": "Initial Target",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "adestment",
			"label": "Adestment",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "final_target",
			"label": "Final Target",
			"fieldtype": "Data",
			"width": 120
		},
	]

def construct_query(filters=None):
	conditions, filters = get_conditions(filters)
	query = ("""
			select 
				rt.cost_center as cost_center,rta.account as account,rta.account_number as account_number,rta.target_amount as target_amount,rta.adjustment_amount as adjustment_amount,rta.net_target_amount as net_target_amount,rta.january as january,rta.february as february,rta.march as march,rta.april as april,rta.may as may,rta.june as june,rta.july as july,rta.august as august,rta.september as september,rta.october as october,rta.november as november,rta.december as december
			from `tabRevenue Target` rt 
			inner join `tabRevenue Target Account` rta on rta.parent = rt.name 
			where rt.docstatus = 1
			{conditions}
			""".format(conditions=conditions))
	return query	
def get_data(query, filters):
	data = []
	datas = frappe.db.sql(query, as_dict=True)
	for d in datas:
		if not filters.monthly:
			row = {
				"cost_center": d.cost_center,
				"account": d.account,
				"account_number": d.account_number,
				"initial_target": d.target_amount,
				"adestment": d.adestment_amount,
				"final_target": d.net_target_amount
			}
		else:
			month = filters.get('month').lower()
			if month =="january":
				month_value =d.january
			elif month =="february":
				month_value =d.february
			elif month =="march":
				month_value =d.march
			elif month =="april":
				month_value =d.april
			elif month =="may":
				month_value =d.may
			elif month =="june":
				month_value =d.june
			elif month =="july":
				month_value =d.july
			elif month =="august":
				month_value =d.august
			elif month =="september":
				month_value =d.september
			elif month =="october":
				month_value =d.october
			elif month =="november":
				month_value =d.november
			else:
				month_value =d.december
			
			row = {
				"cost_center": d.cost_center,
				"account": d.account,
				"account_number": d.account_number,
				"initial_target": month_value,
				"adestment": d.adestment_amount,
				"final_target": month_value
			}
		data.append(row)
	return data
def get_conditions(filters):
	conditions = ""
	if filters.get("cost_center"): 
		conditions += " and rt.cost_center = %(cost_center)s"
	if filters.get("year"): 
		conditions += " and rt.year = %(year)s"

	return conditions, filters



	
