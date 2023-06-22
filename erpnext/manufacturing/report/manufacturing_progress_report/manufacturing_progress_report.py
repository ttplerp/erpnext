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
			"fieldname": "item",
			"label": "Item",
			"fieldtype": "Link",
			"options": "Item",
			"width": 200
		},
		{
			"fieldname": "item_name",
			"label": "Item Name",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "planed_qty",
			"label": "Planed Qty",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "manufactured_qty",
			"label": "Manufactured Qty",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "warehouse",
			"label": "Warehouse",
			"fieldtype": "Link",
			"options": "Warehouse",
			"width": 200
		},
		{
			"fieldname": "branch",
			"label": "Branch",
			"fieldtype": "Link",
			"options": "Branch",
			"width": 200
		},
		{
			"fieldname": "production_id",
			"label": "Production ID",
			"fieldtype": "Link",
			"options": "Production Plan",
			"width": 200
		}
	]

def construct_query(filters=None):
	conditions, filters = get_conditions(filters)
	query = ("""
			select 
				p.name as name,p.branch as branch,pi.item_code as item_code,pi.planed_qty as planed_qty, pi.warehouse as warehouse
			from `tabProduction Plan` p 
			inner join `tabProduction Plan Item` pi on pp.parent = p.name 
			where p.docstatus != 2
			{conditions}
			""".format(conditions=conditions))
	return query	
def get_data(query, filters):
	data = []
	datas = frappe.db.sql(query, as_dict=True)
	for d in datas:
		from_date = filters.get('from_date')
		to_date = filters.get('to_date')

		row = {
			"item": d.cost_center,
			"item_name": d.account,
			"planed_qty": d.account_number,
			"manufactured_qty": d.target_amount,
			"warehouse": d.adestment_amount,
			"branch": d.net_target_amount,
			"production_id":achieved_amount
		}
		data.append(row)
	return data
def get_conditions(filters):
	conditions = ""
	if filters.get("branch"):
		conditions += """and p.branch ='{}'""".format(filters.get("branch"))
	if filters.get("year"):
		year = filters.get("year")
		conditions += """and rt.fiscal_year = {year}""".format(year=year)

	return conditions, filters
