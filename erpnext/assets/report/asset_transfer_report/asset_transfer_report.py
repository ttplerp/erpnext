# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
	columns = get_columns(filters)
	data = get_data(filters)

	return columns, data

def get_data(filters):
	cond = ''
	if filters.purpose:
		cond = " and am.purpose = '{}'".format(filters.purpose) 
	entries = frappe.db.sql("""
		SELECT 
			ami.asset, 
			am.purpose, 
			ami.asset_name, 
			ami.from_employee, 
			ami.from_employee_name,
			ami.to_employee, 
			ami.to_employee_name,
			am.transaction_date, 
			ami.target_cost_center 
		FROM `tabAsset Movement` am, 
			 `tabAsset Movement Item` ami 
		WHERE am.docstatus = 1 
			AND am.name = ami.parent {cond}
		""".format(cond=cond), as_dict=1)
	return entries

# def validate_filters(filters):
# 	if filters.from_date > filters.to_date:
# 		frappe.throw(_("From Date cannot be greater than To Date"))

def get_columns(filters):
	cols = [
		{
		  "fieldname": "asset",
		  "label": "Asset",
		  "fieldtype": "Link",
		  "width": 150,
		  "options": "Asset",
		},
		{
		  "fieldname": "purpose",
		  "label": "Purpose",
		  "fieldtype": "Data",
		  "width": 150,
		},
		{
			"fieldname": "asset_name",
			"label": "Asset Name",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "from_employee",
			"label": "From Employee",
			"fieldtype": "link",
			"width": 120
		},
		{
			"fieldname": "from_employee_name",
			"label": "From Employee Name",
			"fieldtype": "link",
			"width": 150
		},
		{
			"fieldname": "to_employee",
			"label": "To Employee",
			"fieldtype": "link",
			"width": 120
		},
		{
			"fieldname": "to_employee_name",
			"label": "To Employee Name",
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "transaction_date",
			"label": "Transaction Date",
			"fieldtype": "Date",
			"width": 150
		},
		{
			"fieldname": "target_cost_center",
			"label": "Target Cost Center",
			"fieldtype": "Data",
			"width": 150
		},     
	]
	return cols