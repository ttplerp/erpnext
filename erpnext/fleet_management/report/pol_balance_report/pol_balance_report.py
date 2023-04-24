# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt

def execute(filters=None):
	columns, data = get_columns(filters), get_data(filters)
	return columns, data

def get_tanker_details(filters):
	if filters.get("equipment"):
		return frappe.get_list("Equipment", fields=["name","equipment_category","registeration_number"], filters={"company": filters.company, "is_container":1, "name":filters.get("equipment") })
	return frappe.get_list("Equipment", fields=["name","equipment_category","registeration_number"], filters={"company": filters.company, "is_container":1 })

def get_data(filters):
	data = []
	conditions = get_conditions(filters)

	for t in get_tanker_details(filters):
		opening_in_qty = opening_out_qty = in_qty = out_qty = balance_qty = 0
		for d in frappe.db.sql('''
				SELECT  pol_type, item_name, equipment,
						SUM(CASE WHEN posting_date < '{from_date}' AND type = 'Stock' THEN qty ELSE 0 END) AS opening_in_qty,
						SUM(CASE WHEN posting_date < '{from_date}' AND type = 'Issue' THEN qty ELSE 0 END) AS opening_out_qty,
						SUM(CASE WHEN posting_date BETWEEN '{from_date}' AND '{to_date}' AND type = 'Stock' THEN qty ELSE 0 END) AS in_qty,
						SUM(CASE WHEN posting_date BETWEEN '{from_date}' AND '{to_date}' AND type = 'Issue' THEN qty ELSE 0 END) AS out_qty
				FROM `tabPOL Entry` WHERE docstatus = 1 {conditions} AND equipment = '{equipment}'
				GROUP BY pol_type
			'''.format(from_date=filters.get("from_date"), to_date=filters.get("to_date"), conditions= conditions, equipment = t.name), as_dict=1):
			# opening_in_qty 	+= flt(d.opening_in_qty)
			# opening_out_qty += flt(d.opening_out_qty)
			# in_qty 			+= flt(d.in_qty)
			# out_qty 		+= flt(d.out_qty)
			d.update({
				"opening_qty": flt(d.opening_in_qty) - flt(d.opening_out_qty),
				"equipment_category":t.equipment_category,
				"balance_qty": flt(flt(d.opening_in_qty) - flt(d.opening_out_qty),2) + flt(flt(d.in_qty) - flt(d.out_qty),2)
			})
			data.append(d)
			# data.append({
			# 	"equipment":t.name,
			# 	"pol_type":
			# 	"equipment_category":t.equipment_category,
			# 	"opening_qty": flt(opening_in_qty) - flt(opening_out_qty),
			# 	"in_qty":in_qty,
			# 	"out_qty":out_qty,
			# 	"balance_qty": flt(flt(opening_in_qty) - flt(opening_out_qty)) + flt(flt(in_qty) - flt(out_qty))
			# })
	return data

def get_conditions(filters):
	conditions = []
	if filters.get("to_date"):
		conditions.append("posting_date <= '{}'".format(filters.get("to_date")))
	if filters.get("branch"):
		conditions.append("branch = '{}'".format(filters.get("branch")))

	return "and {}".format(" and ".join(conditions)) if conditions else ""

def get_columns(filters):
	return [
		{
			"fieldname":"equipment",
			"label":_("Tanker"),
			"fieldtype":"Link",
			"options":"Equipment",
			"width":130
		},
		{
			"fieldname":"pol_type",
			"label":_("POL Type"),
			"fieldtype":"Link",
			"options":"Item",
			"width":100
		},
		{
			"fieldname":"item_name",
			"label":_("Item Name"),
			"fieldtype":"Data",
			"width":100
		},
		{
			"fieldname":"equipment_category",
			"label":_("Tanker Category"),
			"fieldtype":"Link",
			"options":"Equipment Category",
			"width":200
		},
		{
			"fieldname":"opening_qty",
			"label":_("Opening Qty"),
			"fieldtype":"Float",
			"width":120
		},
		{
			"fieldname":"in_qty",
			"label":_("In Qty"),
			"fieldtype":"Float",
			"width":120
		},
		{
			"fieldname":"out_qty",
			"label":_("Out Qty"),
			"fieldtype":"Float",
			"width":120
		},
		{
			"fieldname":"balance_qty",
			"label":_("Balance Qty"),
			"fieldtype":"Float",
			"width":120
		}
	]