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
	
	# select name, posting_date, qty, warehouse from `tabPOL Receive` where docstatus = 1 and receive_in_barrel = 1 {conditions}
	# 						'''.format(conditions= conditions),as_dict=1)

	# data = frappe.db.sql('''
	# 						 select pr.name, pr.posting_date, pr.qty, pr.warehouse, pi.name as issname,
	# 				   pi.total_quantity as issue_quantity from `tabPOL Receive` pr inner join `tabPOL Issue` 
	# 				   pi on pr.pol_type=pi.pol_type where 
	# 				   pr.docstatus = 1 and pr.receive_in_barrel = 1 {conditions}
	# 						 '''.format(conditions= conditions),as_dict=1)
	# 	return data
	barrel_value = filters.get('barrel')
	if barrel_value == 1:
		# frappe.throw(get_tanker_details(filters))
		# data1 = frappe.db.sql('''
		# 					 select name, posting_date, qty, warehouse from `tabPOL Receive`  where 
		# 			   docstatus = 1 and receive_in_barrel = 1 {conditions}
		# 					 '''.format(conditions= conditions),as_dict=1)
		
		
		data1 = frappe.db.sql('''
							SELECT MAX(posting_date) AS posting_date, SUM(qty) AS qty, warehouse
FROM `tabPOL Receive`
WHERE docstatus = 1 AND receive_in_barrel = 1 {conditions}
GROUP BY  warehouse'''.format(conditions= conditions),as_dict=1)

		
		# data2 = frappe.db.sql('''
		# 					select name , total_quantity as issue_quantity, posting_date, warehouse from `tabPOL Issue` where 
		# 			   docstatus = 1 and receive_in_barrel = 1 {conditions}
		# 					 '''.format(conditions= conditions),as_dict=1);
		data2 = frappe.db.sql('''
							select SUM(total_quantity) as issue_quantity, posting_date, warehouse from `tabPOL Issue` where 
					   docstatus = 1 and receive_in_barrel = 1 {conditions} GROUP BY warehouse 
							 '''.format(conditions= conditions),as_dict=1);
							
		data = data1 + data2
		merged_data = data
		max_len = max(len(data1), len(data2))

		# for i in range(max_len):
		# 	if i < len(data1):
		# 		merged_data.append(data1[i])
		# 	if i < len(data2):
		# 		merged_data.append(data2[i])
		#Initialize total quantities
		total_qty = 0
		total_issue_quantity = 0

		for row in merged_data:
			total_qty += flt(row.get('qty', 0))
			total_issue_quantity += flt(row.get('issue_quantity', 0))

		# Calculate the balance
		total_balance_qty = total_qty-total_issue_quantity  

		# Set 'balance_qty' to 0 for individual rows
		for row in merged_data:
			row['balance_qty'] = 0

		# Assign the calculated total_balance_qty to the 'balance_qty' field of the last row
		if merged_data:
			merged_data[-1]['balance_qty'] = total_balance_qty





		return merged_data
		return data
	else:
		for t in get_tanker_details(filters):
			opening_in_qty = opening_out_qty = in_qty = out_qty = balance_qty = 0
			for d in frappe.db.sql('''
					SELECT  pol_type, equipment,
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
	barrel_value = filters.get('barrel')
	if barrel_value == 1:
		conditions = []
		if filters.get("warehouse"):
			conditions.append("warehouse = '{}'".format(filters.get("warehouse")))
		if filters.get("to_date"):
			conditions.append("posting_date <= '{}'".format(filters.get("to_date")))
		if filters.get("from_date"):
			conditions.append("posting_date >= '{}'".format(filters.get("from_date")))
		if filters.get("branch"):
			conditions.append("branch = '{}'".format(filters.get("branch")))
		#tw
		

		return "and {}".format(" and ".join(conditions)) if conditions else ""
	else:
		conditions = []
		if filters.get("to_date"):
			conditions.append("posting_date <= '{}'".format(filters.get("to_date")))
		if filters.get("from_date"):
			conditions.append("posting_date >= '{}'".format(filters.get("from_date")))
		if filters.get("branch"):
			conditions.append("branch = '{}'".format(filters.get("branch")))
		
		#tw
		

		return "and {}".format(" and ".join(conditions)) if conditions else ""


def get_columns(filters):
	barrel_value = filters.get('barrel')
	if barrel_value == 1:
		return [
		# 	{
		# 		"fieldname":"name",
		# 		"label":_("POL Recieve/Issue ID"),
		# 		"fieldtype":"data",
		# 		"options":"",
		# 		"width":160
		# 	},
		# {
		# 		"fieldname":"posting_date",
		# 		"label":_("Posting date"),
		# 		"fieldtype":"data",
		# 		"options":"",
		# 		"width":130
		# 	},
		{
				"fieldname":"warehouse",
				"label":_("Warehouse"),
				"fieldtype":"data",
				"options":"Item",
				"width":160
			},
		# {
		# 		"fieldname":"issued_warehouse",
		# 		"label":_("Issued Warehouse"),
		# 		"fieldtype":"data",
		# 		"options":"Item",
		# 		"width":160
		# 	},
		{
				"fieldname":"qty",
				"label":_("In Qty"),
				"fieldtype":"data",
				"options":"Item",
				"width":100
			},
		
		# {
		# 		"fieldname":"",
		# 		"label":_(""),
		# 		"fieldtype":"data",
		# 		"options":"Item",
		# 		"width":100
		# 	},
		# {
		# 		"fieldname":"issname",
		# 		"label":_("POL Issue ID"),
		# 		"fieldtype":"data",
		# 		"options":"Item",
		# 		"width":160
		# 	},
		# {
		# 		"fieldname":"issued_posting_date",
		# 		"label":_("POL Issue date"),
		# 		"fieldtype":"data",
		# 		"options":"",
		# 		"width":130
		# 	},
		
		{
				"fieldname":"issue_quantity",
				"label":_("Out Qty"),
				"fieldtype":"data",
				"options":"Item",
				"width":100
			},
		
		{
				"fieldname":"balance_qty",
				"label":_("Balance Qty"),
				"fieldtype":"Float",
				"width":120
			}
		]
		
	else: 
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

			# {
			# 	"fieldname":"item_name",
			# 	"label":_("Item Name"),
			# 	"fieldtype":"Data",
			# 	"width":100
			# },
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