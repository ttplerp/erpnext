# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt
from frappe.utils import flt
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
		{
			"fieldname": "achieved_amount",
			"label": "Achieved Amount",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "balance_amount",
			"label": "Balance Amount",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "achieved_percent",
			"label": "Achieved Percent",
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
		from_date = filters.get('from_date')
		to_date = filters.get('to_date')
		achevied = frappe.db.sql("""
			select
				ifnull(sum(gl.debit) - sum(gl.credit), 0) as achieved_amount
				from `tabGL Entry` as gl
				where gl.docstatus = 1
				and gl.posting_date between '{from_date}' and '{to_date}'
				and gl.cost_center = '{cost_center}'
				and gl.account ='{account}'
			""".format(from_date=from_date, to_date=to_date, cost_center=d.cost_center, account=d.account),as_dict=True)
	
		achieved_amount = achevied[0]['achieved_amount']

		if not filters.monthly or not filters.month:
			
			achieved_percent = 0
			if achieved_amount > 0:
				achieved_percent =(flt(achieved_amount)/flt(d.target_amount))*100
			balance_amount = flt(d.target_amount)-flt(achieved_amount)
			row = {
				"cost_center": d.cost_center,
				"account": d.account,
				"account_number": d.account_number,
				"initial_target": d.target_amount,
				"adestment": d.adestment_amount,
				"final_target": d.net_target_amount,
				"achieved_amount":achieved_amount,
				"balance_amount":balance_amount,
				"achieved_percent":achieved_percent
			}
		else:
			achieved_percent = 0
			month = filters.get('month').lower()
			if month =="january":
				month_value =d.january
				balance_amount = flt(d.january)-flt(achieved_amount)
				if achieved_amount > 0:
					achieved_percent =(flt(achieved_amount)/flt(d.january))*100
			elif month =="february":
				month_value =d.february
				balance_amount = flt(d.february)-flt(achieved_amount)
				if achieved_amount > 0:
					achieved_percent =(flt(achieved_amount)/flt(d.february))*100
			elif month =="march":
				month_value =d.march
				balance_amount = flt(d.march)-flt(achieved_amount)
				if achieved_amount > 0:
					achieved_percent =(flt(achieved_amount)/flt(d.march))*100
			elif month =="april":
				month_value =d.april
				balance_amount = flt(d.april)-flt(achieved_amount)
				if achieved_amount > 0.0:
					achieved_percent =(flt(achieved_amount)/flt(d.april))*100
			elif month =="may":
				month_value =d.may
				balance_amount =flt(d.may)-flt(achieved_amount)
				if achieved_amount > 0:
					achieved_percent =(flt(achieved_amount)/flt(d.may))*100
			elif month =="june":
				month_value =d.june
				balance_amount = flt(d.june)-flt(achieved_amount)
				if achieved_amount > 0:
					achieved_percent =(flt(achieved_amount)/flt(d.june))*100
			elif month =="july":
				month_value =d.july
				balance_amount = flt(d.july)-flt(achieved_amount)
				if achieved_amount > 0:
					achieved_percent =(flt(achieved_amount)/flt(d.july))*100
			elif month =="august":
				month_value =d.august
				balance_amount = flt(d.august)-flt(achieved_amount)
				if achieved_amount > 0:
					achieved_percent =(flt(achieved_amount)/flt(d.august))*100
			elif month =="september":
				month_value =d.september
				balance_amount = flt(d.september)-flt(achieved_amount)
				if achieved_amount > 0:
					achieved_percent =(flt(achieved_amount)/flt(d.september))*100
			elif month =="october":
				month_value =d.october
				balance_amount =flt(d.october)-flt(achieved_amount)
				if achieved_amount > 0:
					achieved_percent =(flt(achieved_amount)/flt(d.october))*100
			elif month =="november":
				month_value =d.november
				balance_amount = flt(d.november)-flt(achieved_amount)
				if achieved_amount > 0:
					achieved_percent =(flt(achieved_amount)/flt(d.november))*100
			else:
				month_value =d.december
				balance_amount = flt(d.december)-flt(achieved_amount)
				if achieved_amount > 0:
					achieved_percent =(flt(achieved_amount)/flt(d.december))*100
			row = {
				"cost_center": d.cost_center,
				"account": d.account,
				"account_number": d.account_number,
				"initial_target": month_value,
				"adestment": d.adestment_amount,
				"final_target": month_value,
				"achieved_amount":achieved_amount,
				"balance_amount":balance_amount,
				"achieved_percent":achieved_percent
			}
		data.append(row)
	return data
def get_conditions(filters):
	conditions = ""
	if filters.get("cost_center"):
		cost_center = filters.get("cost_center")
		conditions += """and rt.cost_center ='{cost_center}'""".format(cost_center=cost_center)
	if filters.get("year"):
		year = filters.get("year")
		conditions += """and rt.fiscal_year = {year}""".format(year=year)

	return conditions, filters



	
