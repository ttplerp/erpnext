# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data

def get_data(filters):
	cond = ""
	if filters.status:
		cond = " and asset.status = '{}'".format(filters.status)

	if filters.asset_category:
		cond += " and asset.asset_category = '{}'".format(filters.asset_category)

	entries = frappe.db.sql("""
		SELECT 
			asset.name,
			asset.asset_name,
			asset.asset_category,
			asset.item_code,
			asset.item_name,
			asset.custodian,
			asset.custodian_name,
			asset.department,				
			asset.cost_center,
			asset.disposal_date,
			asset.purchase_receipt,
			asset.purchase_invoice,
			asset.purchase_date,
			asset.status,
			asset.is_existing_asset
		FROM `tabAsset` asset 
		WHERE asset.docstatus = 1 {cond}
		""".format(cond = cond),as_dict=1)
		# as
		# WHERE asset.docstatus = 1
	return entries

def get_columns(filters):
	cols = [
		{
			"fieldname": "name",
			"fieldtype": "Link",
			"label": "Asset",
			"options": "Asset",
			"width": 150
		},
		{
			"fieldname": "asset_name",
			"fieldtype": "Data",
			"label": "Asset Name",
			"width": 150
		},
		{
			"fieldname": "asset_category",
			"fieldtype": "Data",
			"label": "Asset Category",
			"width": 150
		},
		{
			"fieldname": "item_code",
			"fieldtype": "Link",
			"label": "Item Code",
			"options": "Item",
			"width": 150
		},
		{
			"fieldname": "item_name",
			"fieldtype": "Data",
			"label": "Item Name",
			"width": 150
		},
		{
			"fieldname": "custodian",
			"fieldtype": "Link",
			"label": "Custodian",
			"options": "Employee",
			"width": 150
		},
		{
			"fieldname": "custodian_name",
			"fieldtype": "Data",
			"label": "Custodian Name",
			"width": 150
		},
		{
			"fieldname": "cost_center",
			"fieldtype": "Data",
			"label": "Cost Center",
			"width": 150
		},
		{
			"fieldname": "disposal_date",
			"fieldtype": "Data",
			"label": "Disposal Date",
			"width": 150
		},
		{
			"fieldname": "purchase_receipt",
			"fieldtype": "Link",
			"label": "Purchase Receipt",
			"options": "Purchase Receipt",
			"width": 150
		},
		{
			"fieldname": "purchase_invoice",
			"fieldtype": "Data",
			"label": "Purchase Invoice",
			"options": "Purchase Invoice",
			"width": 150
		},
		{
			"fieldname": "purchase_date",
			"fieldtype": "Data",
			"label": "Purchase Date",
			"width": 150
		},
		{
			"fieldname": "status",
			"fieldtype": "Data",
			"label": "Status",
			"width": 150
		},
		{
			"fieldname": "is_existing_asset",
			"fieldtype": "Checkbox",
			"label": "Is Existing",
			"width": 150
		},
	]
	return cols

	

