# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data

def get_columns(filters):
	cols = [
		("Date") + ":date:100",
		("Entry Type") + ":data:100",
		("Material Code") + ":data:110",
		("Material Name")+":data:120",
		("Material Group")+":data:120",
		("Material Sub Group")+":data:150",
		("UOM") + ":data:50",
		("Qty")+":data:50",
		("Valuation Rate")+":data:120",
		("Amount")+":Currency:110",
	]
	if filters.purpose == "Material Issue":
		cols.append(("Cost Center")+":data:170")
		cols.append(("Issued To") + ":data:170")
		cols.append(("Desuup Name") + ":data:170")


	if filters.purpose == "Material Transfer":
		cols.append(("Source Warehouse")+":data:170")
		cols.append(("Receiving Warehouse")+":data:170")
		cols.append(("Stock Entry")+":Link/Stock Entry:170")
		cols.append(("Issued To") + "::100")
		cols.append(("Desuup Name") + "::150")

	return cols

def get_data(filters):
	if filters.purpose == 'Material Transfer':
		data = """
		SELECT 
			se.posting_date, se.entry_type, sed.item_code, sed.item_name, 
			(select i.item_group from tabItem i where i.item_code = sed.item_code) as item_group, 
			(select i.item_sub_group from tabItem i where i.item_code = sed.item_code) as item_sub_group, 
			sed.uom, sed.qty, sed.valuation_rate,sed.amount, se.from_warehouse, sed.t_warehouse, se.name,
			IFNULL(sed.issue_to_desuup, ''), IFNULL(sed.issued_desuup_name, '')
		FROM `tabStock Entry` se, `tabStock Entry Detail` sed 
		WHERE se.name = sed.parent and  se.docstatus = 1 and se.purpose = 'Material Transfer'"""
	
	elif filters.purpose == 'Material Issue':
		data = """
		SELECT 
			se.posting_date, se.entry_type, sed.item_code, sed.item_name, 
			(select i.item_group from tabItem i where i.item_code = sed.item_code) as item_group, 
			(select i.item_sub_group from tabItem i where i.item_code = sed.item_code) as item_sub_group, 
			sed.uom, sed.qty, sed.valuation_rate,sed.amount, sed.cost_center,
   			IFNULL(sed.issue_to_desuup, ''), IFNULL(sed.issued_desuup_name, '')
		FROM `tabStock Entry` se, `tabStock Entry Detail` sed 
		WHERE se.name = sed.parent and  se.docstatus = 1 and se.purpose = 'Material Issue'"""

	if filters.get("warehouse"):
		data += " and sed.s_warehouse = \'" + str(filters.warehouse) + "\'"
	if filters.get("item_code"):
		data += " and sed.item_code = \'" + str(filters.item_code) + "\'"
	if filters.get("from_date") and filters.get("to_date"):
		data += " and se.posting_date between \'" + str(filters.from_date) + "\' and \'"+ str(filters.to_date) + "\'"
	if filters.get("entry_type") and filters.get("entry_type") != "":
		data += " and se.entry_type = '{0}'".format(filters.get("entry_type"))
	return frappe.db.sql(data)
