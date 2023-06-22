# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt
def execute(filters=None):
	columns, data = [], []
	columns = get_columns(data)
	queries = construct_query(filters)
	data = get_data(queries,filters)
	
	return columns, data

def get_columns(data):
	return [
		{
			"fieldname": "work_order",
			"label": "Work Order",
			"fieldtype": "Link",
			"options": "Work Order",
			"width": 200
		},
		{
			"fieldname": "item_code",
			"label": "Item Code",
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
			"fieldname": "bom",
			"label": "BOM",
			"fieldtype": "Link",
			"options": "BOM",
			"width": 200
		},
		{
			"fieldname": "qty_to_man",
			"label": "Qty To Manufacture",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "man_qty",
			"label": "Manufactured Qty",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "req_qty",
			"label": "Required Qty",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "con_qty",
			"label": "Consumed Qty",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "rate",
			"label": "Rate",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "req_amount",
			"label": "Required Amount",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "con_amount",
			"label": "Consumed Amount",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "branch",
			"label": "Branch",
			"fieldtype": "Link",
			"options":"Branch",
			"width": 120
		},
	]

def construct_query(filters=None):
	conditions, filters = get_conditions(filters)
	query = ("""
			select 
			wo.name as name, wo.production_item as production_item, wo.item_name as item_name, wo.bom_no as bom_no, wo.qty as qty, wo.produced_qty as produced_qty, rq.required_qty as required_qty, rq.consumed_qty as consumed_qty, rq.rate as rate, wo.branch
			from `tabWork Order` wo 
			inner join `tabWork Order Item` rq on rq.parent = wo.name 
			where wo.docstatus = 1
			and wo.status = 'Completed' 
			or wo.status = 'In Process'
			{conditions}
			""".format(conditions=conditions))
	return query	
def get_data(query, filters):
	data = []
	datas = frappe.db.sql(query, as_dict=True)
	for d in datas:
		required_amount = flt(d.rate)*flt(d.required_qty)
		consumed_amount	= flt(d.rate)*flt(d.consumed_qty)
		row = {
			"work_order": d.name,
			"item_code": d.production_item,
			"item_name": d.item_name,
			"bom": d.bom_no,
			"qty_to_man": d.qty,
			"man_qty": d.produced_qty,
			"req_qty": d.required_qty,
			"con_qty": d.consumed_qty,
			"rate": d.rate,
			"req_amount": required_amount,
			"con_amount": consumed_amount,
			"branch": d.branch
		}
		data.append(row)
	return data
def get_conditions(filters):
	conditions = ""
	if filters.get("item"):
		conditions += """and wo.production_item = '{item}'""".format(item=filters.get("item"))
	if filters.get("branch"): 
		conditions += """and wo.branch = '{branch}'""".format(branch=filters.get("branch"))
	if filters.get("from_date") and filters.get("to_date"):
		if filters.get("from_date") > filters.get("to_date"):
			frappe.throw("From Date cannot be after To Date")
		else:
			conditions += """and wo.actual_start_date between {0} and {1}""".format(filters.get("from_date"),filters.get("to_date"))
	# frappe.throw(str(conditions))
	return conditions, filters
	