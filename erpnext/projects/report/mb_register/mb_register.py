# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt
from __future__ import unicode_literals
import frappe

def execute(filters=None):	
	columns = get_columns()
	data = get_data(filters)

	return columns, data

def get_columns():
	return [
		("Project") + ":Link/Project:210",
		("Transaction #") + ":Link/MB Entry:120",
		("Date") + ":Data:80",
		("Cost Center") + ":Data:150",
		("Customer") + ":Data:120",
		("Status") + ":Data :80",
		("BOQ") + ":Link/BOQ:110",
		("Booked Amount (A)") + ":Currency:120",
		("Invoice Amount(B)") + ":Currency:120",
		("Balance Amount(A-B)") + ":Currency: 120"
		]

def get_data(filters):
	query = """ 
			select 
				p.project_name, 
				mb.name,
				mb.entry_date, 
				mb.cost_center, 
				mb.customer,
				mb.status, 
				mb.boq, 
				mb.total_entry_amount, 
				mb.total_invoice_amount, 
				mb.total_balance_amount 
			from  `tabMB Entry` as mb, `tabProject` p
			where  mb.docstatus = 1
			and p.name = mb.project
	"""

	if filters.get("project"):
				query += " and project = \'" + str(filters.project) + "\'"

	if filters.get("from_date") and filters.get("to_date"):
			query += " and entry_date between \'" + str(filters.from_date) + "\' and \'"+ str(filters.to_date) + "\'"

	elif filters.get("from_date") and not filters.get("to_date"):
			query += " and entry_date >= \'" + str(filters.from_date) + "\'"

	elif not filters.get("from_date") and filters.get("to_date"):
			query += " and entry_date <= \'" + str(filters.to_date) + "\'"

	query += " order by entry_date desc"

	return frappe.db.sql(query)

