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
			"fieldname": "location_name",
			"label": "Locations Name",
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "location",
			"label": "Locations ID",
			"fieldtype": "Link",
			"options": "Locations",
			"width": 120
		},
		{
			"fieldname": "block_no",
			"label": "Block No",
			"fieldtype": "Link",
			"options": "Block No",
			"width": 150
		},
		{
			"fieldname": "flat_id",
			"label": "Flat ID",
			"fieldtype": "Link",
			"options": "Flat No",
			"width": 200
		},
		{
			"fieldname": "flat_no",
			"label": "Flat No",
			"fieldtype": "Data",
			"width":70
		},
		{
			"fieldname": "b_category",
			"label": "Building Category",
			"fieldtype": "Link",
			"options": "Building Category",
			"width": 140
		},
		{
			"fieldname": "b_classification",
			"label": "Building Classification",
			"fieldtype": "Link",
			"options": "Building Classification",
			"width": 150
		},
		{
			"fieldname": "town_category",
			"label": "Town Category",
			"fieldtype": "Link",
			"options": "Town Category",
			"width": 120
		},
		{
			"fieldname": "status",
			"label": "Status",
			"fieldtype": "Data",
			"width": 120
		},
	]

def construct_query(filters=None):
	conditions, filters = get_conditions(filters)
	query = ("""
			select 
				f.name as name, f.block_no as block_no, f.flat_no as flat_no,f.building_category as building_category, f.status as status, f.town_category as town_category
			from `tabFlat No` f 
			where f.docstatus != 2
			{}
			""".format(conditions))
	return query	
def get_data(query, filters):
	conditions = ""
	data = []
	datas = frappe.db.sql(query, as_dict=True)
	for d in datas:
		location = frappe.db.get_value("Block No",d.block_no,"location")
		location_name = frappe.db.get_value("Block No",d.block_no,"location_name")
		building_classification = frappe.db.get_value("Block No",d.block_no,"building_classification")
		town_category = frappe.db.get_value("Block No",d.block_no,"town_category")

		row = {
			"location_name":location_name,
			"location":	location,
			"block_no": d.block_no,
			"flat_id": d.name,
			"flat_no": d.flat_no,
			"b_category": d.building_category,
			"b_classification":building_classification,
			"town_category": town_category,
			"status":d.status
		}
		data.append(row)
	return data
def get_conditions(filters):
	conditions = ""
	if filters.get("status"):
		conditions += """and f.status ='{}'""".format(filters.get("status"))
	if filters.get("block_no"):
		conditions += """and f.block_no ='{}'""".format(filters.get("block_no"))
	if filters.get("location"):
		conditions += """and f.location_name ='{}'""".format(filters.get("location"))

	return conditions, filters
