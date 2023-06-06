# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	columns, data = [], []
	data = get_data(filters)
	if not data:
		return columns, data
	columns = get_columns(data)
	return columns, data

def get_columns(data):
	columns = [
		("Work Order") + ":Link/Work Order:180",
		("Item Code") + ":Link/Item:120",
		("Item Name") + ":Data:120",
		("BOM") + ":Link/BOM:180",
		("Qty To Manufacture") + ":Data:120",
		("Manufactured Qty") + ":Data:120",
		("Required Qty") + ":Data:120",
		("Consumed Qty") + ":Data:120",
		("Rate") + ":Data:80",
		("Amount") + ":Data:150",
		("Branch") + ":Link/Branch:150",
	]
	return columns

def get_data(filters):
	conditions, filters = get_conditions(filters)
	data = frappe.db.sql("""
		select 
			wo.name, wo.production_item, wo.item_name, wo.bom_no, wo.qty, wo.produced_qty, rq.required_qty, rq.consumed_qty, rq.rate, rq.amount, wo.branch
		from `tabWork Order` wo 
		inner join `tabWork Order Item` rq on rq.parent = wo.name 
		where wo.docstatus = 1 %s
		and wo.status = 'Completed' 
		or wo.status = 'In Process'
		"""% conditions, filters)
	return data

def get_conditions(filters):
	conditions = ""
	if filters.get("item"): 
		conditions += " and wo.production_item = %(item)s"
	if filters.get("branch"): 
		conditions += " and wo.branch = %(branch)s"

	return conditions, filters
