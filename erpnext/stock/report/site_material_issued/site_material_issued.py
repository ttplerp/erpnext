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
		_("Rental Site") + ":Data:100", 
		_("Site Name") + ":Dynamic Link/Rental Type:100",
		_("Posting Date") + ":Date:100", 
		_("Branch") + ":Link/Branch:100", 
		_("Material Code") + ":Link/Item:100",
		_("Item Name") + ":Data:100", 
		_("UOM")+":Link/UOM:100",
		_("Quantity") + ":Float:100", 
		_("Rate") + ":Currency:100", 
		_("Amount") + ":Currency:100", 
		_("Source Warehouse") + ":Link/Warehouse:100", 
		_("Receiving Warehouse") + ":Link/Warehouse:100", 
		_("Reference No") + ":Link/Stock Entry:100", 
	]

def get_data(filters): 
	cond = get_conditions(filters)
	query = """ 
		SELECT
			se.rental_site,
			se.site_name,
			se.posting_date,
			se.branch,
			sed.item_code,
			sed.item_name,
			sed.uom,
			sed.qty,
			sed.valuation_rate,
			sed.amount,
			se.from_warehouse,
			se.to_warehouse,
			se.name
		FROM
			`tabStock Entry` se
		INNER JOIN
			`tabStock Entry Detail` sed ON se.name = sed.parent
        WHERE
            se.docstatus = 1
            AND se.rental_site != ''
            {conditions}
	""".format(conditions = cond)

	return (frappe.db.sql(query))

def get_conditions (filters):
	cond = ""
	if filters.get("rental_type"): 
		cond += "and se.rental_site = '{}'".format(filters.get("rental_type"))
		
	if filters.get("site_name"): 
		cond += "and se.site_name = '{}'".format(filters.get("site_name"))

	if filters.get("entry_type"): 
		cond += "and se.stock_entry_type = '{}'".format(filters.get("entry_type"))
	
	if filters.get("branch"): 
		cond += "and se.branch = '{}'".format(filters.get("branch"))

	if filters.get("item_code"): 
		cond += "and sed.item_code = '{}'".format(filters.get("item_code"))
		
	if filters.get("from_date") and filters.get("to_date"): 
		cond += "and se.posting_date between '{}' and '{}'".format(filters.get("from_date"), filters.get("to_date"))
	
	return cond
