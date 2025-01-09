# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.utils import flt

def execute(filters=None):
	data = get_data(filters)
	columns = get_columns(filters)
	return columns, data

def get_data(filters):
	return frappe.db.get_all(
		"Unvalued Asset",
		filters=filters,
		fields=[
			"name",
			"branch",
			"asset_name",
			"cost_center",
			"custodian",
			"custodian_name",
			"asset_station",
			"status",
		],
		order_by="name",
	)

def get_columns(filters):
	return [
		{"fieldtype": "Link",	"fieldname": "name", "label": _("Asset Code"), "options": "Unvalued Asset", "width": 200},
		{"fieldtype": "Data", 	"fieldname": "asset_name",	"label": _("Asset Name"), "width": 120},
		{"fieldtype": "Link",	"fieldname": "branch", "label": _("Branch"), "options": "Branch", "width": 200},
		# {"fieldtype": "Link",	"fieldname": "cost_center", "label": _("Cost Center"), "options": "Cost Center", "width": 180},
		{"fieldtype": "Link",	"fieldname": "custodian", "label": _("Custodian"), "options": "Employee", "width": 200},
		{"fieldtype": "Data",	"fieldname": "custodian_name", "label": _("Custodian Name"), "width": 200},
		{"fieldtype": "Link",	"fieldname": "asset_station", "label": _("Asset Station"), "options": "Asset Station", "width": 200},
		{"fieldtype": "Data",	"fieldname": "status", "label": _("Status"), "width": 200},
	]
