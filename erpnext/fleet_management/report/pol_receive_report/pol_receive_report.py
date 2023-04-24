# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt
from __future__ import unicode_literals
import frappe
from frappe import _

def execute(filters=None):
	data = get_data(filters)
	columns = get_columns(filters)
	return columns, data

def get_columns(filters):
	if filters.aggregate:
		return [{"fieldname":"equipment","label":_("Equipment"),"fieldtype":"Link","options":"Equipment","width":120},
				{"fieldname":"equipment_type","label":_("Equipment Type"),"fieldtype":"Link","options":"Equipment Type","width":130},
				{"fieldname":"qty","label":_("Qty"),"fieldtype":"Float","width":120},
				{"fieldname":"rate","label":_("Rate"),"fieldtype":"Currency","width":120},
				{"fieldname":"amount","label":_("Amount"),"fieldtype":"Currency","width":150},
				{"fieldname":"mileage","label":_("Mileage"),"fieldtype":"Float","width":120}]
	return [
		{"fieldname":"reference_type","label":_("Reference Type"),"fieldtype":"Data","width":120},
		{"fieldname":"reference","label":_("Reference"),"fieldtype":"Dynamic Link","options":"reference_type","width":130},
		{"fieldname":"equipment","label":_("Equipment"),"fieldtype":"Link","options":"Equipment","width":130},
		{"fieldname":"equipment_type","label":_("Equipment Type"),"fieldtype":"Link","options":"Equipment Type","width":130},
		{"fieldname":"branch","label":_("Branch"),"fieldtype":"Link","options":"Branch","width":130},
		{"fieldname":"fuelbook","label":_("Fuelbook"),"fieldtype":"Link","options":"Fuelbook","width":120},
		{"fieldname":"supplier","label":_("Supplier"),"fieldtype":"Link","options":"Supplier","width":120},
		{"fieldname":"pol_type","label":_("Item Code"),"fieldtype":"Link","options":"Item","width":120},
		{"fieldname":"item_name","label":_("Item Name"),"fieldtype":"Data","width":120},
		{"fieldname":"posting_date","label":_("Posting Date"),"fieldtype":"Date","width":120},
		{"fieldname":"qty","label":_("Qty"),"fieldtype":"Float","width":120},
		{"fieldname":"rate","label":_("Rate"),"fieldtype":"Currency","width":120},
		{"fieldname":"amount","label":_("Amount"),"fieldtype":"Currency","width":150},
		{"fieldname":"mileage","label":_("Mileage"),"fieldtype":"Float","width":120},
		{"fieldname":"memo_number","label":_("Cash Memo Number"),"fieldtype":"Data","width":120},
		{"fieldname":"pol_slip_no","label":_("POL Slip No."),"fieldtype":"Data","width":120}
	]

def get_data(filters):
	conditions = get_conditions(filters)
	if filters.aggregate:
		query = frappe.db.sql("""select 
									p.equipment, 
									p.equipment_type,
									SUM(p.qty) as qty,  
									ROUND(SUM(p.rate * p.qty)/ SUM(p.qty),2) as rate, 
									SUM(ifnull(p.amount,0)),
									ROUND(AVG(p.mileage),2) as mileage
								from 
									`tabPOL Entry` p 
								where docstatus = 1 {} 
								and type = 'Receive'
								group by p.equipment""".format(conditions), as_dict=True)
	else:
		query = frappe.db.sql("""select distinct 
						p.reference_type,
						p.reference, 
						p.equipment, 
						p.equipment_type, 
						p.branch, 
						p.fuelbook, 
						p.supplier, 
						p.pol_type, 
						p.item_name, 
						p.posting_date, 
						p.qty,  
						p.rate, 
						ifnull(p.amount,0) as amount,
						p.mileage,
						p.memo_number,
						p.pol_slip_no
					from 
						`tabPOL Entry` p 
					where docstatus = 1 {} 
					and type = 'Receive'
					ORDER BY p.posting_date DESC""".format(conditions),as_dict=True)
	return query

def get_conditions(filters):
	conditions = ""
	if filters.get("branch"): 
		conditions += " and p.branch = '{}'".format(filters.get("branch"))

	if filters.get("from_date") and filters.get("to_date"):
		conditions += "and p.posting_date between '{0}' and '{1}'".format(filters.get("from_date"),filters.get("to_date"))
	
	if filters.get("item_name"):
		conditions += "and p.item_name = '{}'".format(filters.get("item_name"))

	if filters.get("equipment"):
		conditions += "and p.equipment = '{}'".format(filters.get("equipment"))
		
	return conditions