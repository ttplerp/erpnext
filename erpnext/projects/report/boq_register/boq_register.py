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
		("Project") + ":Link/Project:180",
		("Cost Center") + ":Data:120",
		("Branch") + ":Data:120",
		("BOQ Type")+ ":Data:80",
		("BOQ Date") + ":Data:80",
		("Name") + ":Link/BOQ:110",
		("Total Amount (A)") + ":Currency:130",
                ("Price Adjustment (B)")+ ":Currency:150",
                ("Invoice Amount Claimed") + ":Currency:120",
                ("Invoice Amount Received (C)") + ":Currency:190",
		("Balance Amount (D=A+B-C)")+ ":Currency:190"
	]

def get_data(filters):
	query =  """
			select 
				p.project_name, 
				b.cost_center, 
				b.branch, 
				b.boq_type, 
				b.boq_date, 
				b.name, 
				b.total_amount, 
				b.price_adjustment, 
				b.claimed_amount, 
				b.received_amount, 
				b.balance_amount 
			from `tabBOQ` as b, `tabProject` as p 
			where b.docstatus =1
			and   p.name = b.project
	""" 
	if filters.get("project"):
		query += ' and project = "{0}"'.format(str(filters.project))

	if filters.get("from_date") and filters.get("to_date"):
		query += " and boq_date between \'" + str(filters.from_date) + "\' and \'"+ str(filters.to_date) + "\'"
	elif filters.get("from_date") and not filters.get("to_date"):
		query += " and boq_date >= \'" + str(filters.from_date) + "\'"
	elif not filters.get("from_date") and filters.get("to_date"):
		query += " and boq_date <= \'" + str(filters.to_date) + "\'"

	query += " order by boq_date desc"
	return frappe.db.sql(query)
