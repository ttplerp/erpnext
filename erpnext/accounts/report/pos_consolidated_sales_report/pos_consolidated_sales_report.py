# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import cstr, getdate, flt, now

def execute(filters=None):
	columns = get_column()
	data = get_data(filters)
	return columns, data

def get_data(filters):
	from_date = now() if not filters.get("from_date") else filters.get("from_date")
	to_date = now() if not filters.get("to_date") else filters.get("to_date")

	if getdate(from_date) > getdate(to_date):
		frappe.throw("From Date cannot be greater than To Date.")
		
	data = frappe.db.sql(""" SELECT pos_profile, sum(grand_total) as total_amount FROM `tabPOS Closing Entry` WHERE company='{}' AND posting_date BETWEEN 
			'{}' AND '{}' GROUP BY pos_profile""".format(filters.get("company"), getdate(from_date), getdate(to_date)), as_dict=1)

	return [] if len(data) == 0 else data

def get_column():
	return [
		{
			"label": _("POS Profile"),
			"fieldname": "pos_profile",
			"fieldtype": "Link",
			"options": "POS Profile",
			"width": 250,
		},
		{
			"label": _("Total Amount"),
			"fieldname": "total_amount",
			"fieldtype": "Currency",
			"options": "company:currency",
			"width": 120
		}
	]