# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from frappe.utils import flt
import frappe
import calendar

def execute(filters=None):
	columns, data = [], []
	columns = get_columns()
	queries = construct_query(filters)
	data = get_data(queries,filters)
	
	return columns, data

def get_columns():
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
			"fieldname": "target_amount",
			"label": "Target Amount",
			"fieldtype": "Currency",
			"width": 160
		},
		{
			"fieldname": "achieved_amount",
			"label": "Achieved Amount",
			"fieldtype": "Currency",
			"width": 160
		},
		{
			"fieldname": "balance_amount",
			"label": "Balance Amount",
			"fieldtype": "Currency",
			"width": 160
		},
		{
			"fieldname": "achieved_percent",
			"label": "Achieved Percent",
			"fieldtype": "Percent",
			"width": 160
		},
	]

def construct_query(filters=None):
	conditions, filters = get_conditions(filters)
	month_lower = filters.get("month").lower()

	query = ("""
			select 
				rt.cost_center as cost_center, rta.account as account, 
		  		rta.account_number as account_number,
		  		rta.{month} as monthly_amt
			from `tabRevenue Target` rt, `tabRevenue Target Account` rta 
			where rta.parent = rt.name and rt.docstatus = 1 
			{conditions}
			""".format(month=month_lower, conditions=conditions))
	return query
	
def get_data(query, filters):
	data = []
	datas = frappe.db.sql(query, as_dict=True)
	month_name = filters.get("month")
	year = filters.get("fiscal_year")
	month_number = list(calendar.month_name).index(month_name.capitalize())
	_, end_day = calendar.monthrange(int(year), month_number)

	start_date = f"{year}-{month_number:02d}-01"
	end_date = f"{year}-{month_number:02d}-{end_day}"

	for d in datas:
		achieved = frappe.db.sql("""
			select
				ifnull(sum(gl.debit) - sum(gl.credit), 0) as achieved_amount
				from `tabGL Entry` as gl
				where gl.docstatus = 1
				and gl.posting_date between '{from_date}' and '{to_date}'
				and gl.cost_center = '{cost_center}'
				and gl.account ='{account}'
			""".format(from_date=start_date, to_date=end_date, cost_center=d.cost_center, account=d.account),as_dict=True)
	
		achieved_amount = achieved[0]['achieved_amount']

		achieved_percent = 0
		balance_amount = flt(d.monthly_amt) - flt(abs(achieved_amount))
		if d.monthly_amt != 0:
			achieved_percent = (flt(achieved_amount) / flt(d.monthly_amt)) * 100
		row = {
			"cost_center": d.cost_center,
			"account": d.account,
			"account_number": d.account_number,
			"target_amount": d.monthly_amt,
			"achieved_amount": abs(achieved_amount),
			"balance_amount": balance_amount,
			"achieved_percent": abs(achieved_percent)
		}
		data.append(row)
	return data

def get_conditions(filters):
	conditions = ""
	if filters.get("cost_center"):
		conditions += """ and rt.cost_center ='{cost_center}'""".format(cost_center=filters.get("cost_center"))
	if filters.get("fiscal_year"):
		conditions += """ and rt.fiscal_year = '{year}'""".format(year=filters.get("fiscal_year"))

	return conditions, filters



	
