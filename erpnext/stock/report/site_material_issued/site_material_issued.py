# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import msgprint, _


def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data

def get_columns():
	return [
		_("Site Name") + ":Link/Site Name:100", 
		_("Branch") + ":Link/Branch:100", 
		_("Requisition Type") + ":Data:100", 
		_("Creation Date") + ":Date:100",
		_("Material Code") + ":Link/Item:100",
		_("Item Name") + ":Data:100", 
		_("UOM")+":Link/UOM:100",
		_("Quantity") + ":Float:100", 
		_("Requesting Warehouse") + ":Link/Warehouse:100", 
		_("Delivery Date") + ":Date:100", 
		_("Cost Center") + ":Data:100", 

	]

def get_data(filters): 
	cond = get_conditions(filters)
	query = """ 
		SELECT 
			mr.site_name, 
			mr.branch, 
			mr.material_request_type, 
			mr.transaction_date, 
			mr_child.item_code, 
			mr_child.item_name, 
			mr_child.uom,
			mr_child.qty,
			mr_child.warehouse, 
			mr_child.schedule_date, 
			mr_child.cost_center
		FROM 
			`tabMaterial Request` as mr
		JOIN 
			`tabMaterial Request Item` as mr_child
		ON	
			mr.name = mr_child.parent
		WHERE
			mr.docstatus = 1 {conditions}
	""".format(conditions = cond)

	return (frappe.db.sql(query))

def get_conditions (filters):
	cond = ""
	if filters.get("site_name"): 
		cond += "and mr.site_name = '{}'".format(filters.get("site_name"))

	if filters.get("requisition_type"): 
		cond += "and mr.material_request_type = '{}'".format(filters.get("requisition_type"))
	
	if filters.get("branch"): 
		cond += "and mr.branch = '{}'".format(filters.get("branch"))

	if filters.get("item_code"): 
		cond += "and mr_child.item_code = {}".format(filters.get("item_code"))
	
	return cond
