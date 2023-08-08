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
			"fieldname": "technical_sanction",
			"label": "Technical Sanction",
			"fieldtype": "Link",
			"options": "Technical Sanction",
			"width": 120
		},
		{
			"fieldname": "tenant",
			"label": "Tenant",
			"fieldtype": "Link",
			"options": "Tenant Information",
			"width": 120
		},
		{
			"fieldname": "tenant_name",
			"label": "Tenant Name",
			"fieldtype": "Data",
			"width": 200
		},
		{
			"fieldname": "block_no",
			"label": "Block No",
			"fieldtype": "Link",
			"options": "Block No",
			"width": 180
		},
		{
			"fieldname": "flat_no",
			"label": "Flat No",
			"fieldtype": "Link",
			"options": "Flat No",
			"width": 200
		},
		{
			"fieldname": "location",
			"label": "Location",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "service_name",
			"label": "Service Name",
			"fieldtype": "Data",
			"width": 200
		},
		{
			"fieldname": "qty",
			"label": "Qty",
			"fieldtype": "Data",
			"width": 80
		},
		{
			"fieldname": "rate",
			"label": "Rate",
			"fieldtype": "Data",
			"width": 80
		},
		{
			"fieldname": "amount",
			"label": "Amount",
			"fieldtype": "Data",
			"width": 80
		}
	]

def construct_query(filters=None):
	conditions, filters = get_conditions(filters)
	query = ("""
			select 
				t.name as name,t.tenant as tenant,t.tenant_name as tenant_name,t.block_no as block_no, t.flat_no as flat_no, t.location as location, ts.item_name as item_name, ts.qty as qty, ts.amount as rate, ts.total as amount
			from `tabTechnical Sanction` t
			inner join `tabTechnical Sanction Item` ts on ts.parent = t.name 
			where t.docstatus != 2
			{conditions}
			""".format(conditions=conditions))
	return query	
def get_data(query, filters):
	data = []
	datas = frappe.db.sql(query, as_dict=True)
	for d in datas:
		row = {
			"technical_sanction": d.name,
			"tenant": d.tenant,
			"tenant_name": d.tenant_name,
			"block_no": d.block_no,
			"flat_no": d.flat_no,
			"location": d.location,
			"service_name": d.item_name,
			"qty":d.qty,
			"rate":d.rate,
			"amount":d.amount
		}
		data.append(row)
	return data
def get_conditions(filters):
	conditions = ""
	if filters.get("branch"):
		conditions += """and t.branch ='{}'""".format(filters.get("branch"))
	if filters.get("from_date") and filters.get("to_date"):
		conditions += """and t.posting_date between '{from_date}' and '{to_date}'""".format(from_date=filters.get("from_date"),to_date=filters.get("to_date"))

	return conditions, filters
