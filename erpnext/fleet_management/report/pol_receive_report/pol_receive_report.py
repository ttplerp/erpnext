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
		return [
				("Equipment") + ":Link/Equipment:130",
				("Equipment Type") + ":Data:200",
				("Quantity") + ":Float:100",
				("Rate Per Unit") + ":Currency:130",
				("Amount") + ":Currency:150",
				("Mileage") + ":Float:100"
				]
	return [
		("POL Receive") + ":Link/POL Receive:120",
		("Equipment") + ":Link/Equipment:120",
		("Equipment Type") + ":Data:120",
		("Fuelbook Branch") + ":Data:120",
		("Fuelbook") + ":Data:120",
		("Supplier") + ":Data:120",
		("Fuel Type Item Code")+ ":Data:100",
		("Item Name")+ ":Data:130",
		("Posting Date") + ":Date:120",
		("Quantity") + ":Data:100",
		("Rate Per Unit") + ":Currency:100",
		("Amount") + ":Currency:120",
		("Mileage") + ":Float:100",
		("Cash Memo Number") + ":Data:120",
		("POL Slip No.") + ":Data:120",
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
								group by p.equipment""".format(conditions))
	else:
		query = frappe.db.sql("""select distinct 
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
						ifnull(p.amount,0),
						p.mileage,
						p.memo_number,
						p.pol_slip_no
					from 
						`tabPOL Entry` p 
					where docstatus = 1 {} 
					and type = 'Receive'
					ORDER BY p.posting_date DESC""".format(conditions))
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