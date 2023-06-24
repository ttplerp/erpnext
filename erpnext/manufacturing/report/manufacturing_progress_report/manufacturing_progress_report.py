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
				p.name as name,p.branch as branch,pi.item_code as item_code,pi.planned_qty as planned_qty, pi.warehouse as warehouse
			from `tabProduction Plan` p 
			inner join `tabProduction Plan Item` pi on pi.parent = p.name 
			where p.docstatus != 2
			{conditions}
			""".format(conditions=conditions))
	return query	
def get_data(query, filters):
	data = []
	datas = frappe.db.sql(query, as_dict=True)
	for d in datas:
		qty = frappe.db.sql("""
			select
				sum(produced_qty)as qty
			from
				`tabWork Order`
			where production_item = '{0}'
			and production_plan = '{1}'
		""".format(d.item_code,d.name),as_dict=True)
		manufactured_qty = qty[0]['qty']
		item_name = frappe.db.get_value("Item",d.item_code,"item_name")
		row = {
			"item": d.item_code,
			"item_name": item_name,
			"planed_qty": d.planned_qty,
			"manufactured_qty": manufactured_qty,
			"warehouse":d.warehouse,
			"branch": d.branch,
			"production_id":d.name
		}
		data.append(row)
	return data
def get_conditions(filters):
	conditions = ""
	if filters.get("branch"):
		conditions += """and p.branch ='{}'""".format(filters.get("branch"))
	if filters.get("from_date") and filters.get("to_date"):
		conditions += """and p.posting_date between '{from_date}' and '{to_date}'""".format(from_date=filters.get("from_date"),to_date=filters.get("to_date"))

	return conditions, filters
