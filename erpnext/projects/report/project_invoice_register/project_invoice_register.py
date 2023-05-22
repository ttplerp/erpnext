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
			("Invoice Date") + ":Date:80",
			("Cost Center") + ":Data:120",
			("Customer") + ":Data:120",
			("BOQ")+ ":Link/BOQ:120",
			("Invoice Type") + ":Data:120",
			("Invoice No.") + ":Link/Project Invoice:110",
			("Status") + ":Data:80",
			("Gross Invoice Amount") + ":Currency:120",
			("Price Adjustment(-/+)")+ ":Currency:120",
			("Net Invoice Amount") + ":Currency:120",
			("Invoice Amount Received") + ":Currency:120",
			("Balance Amount")+ ":Currency:120"
	]

def get_data(filters):
	query =  """
			select 
				p.project_name,
				pi.invoice_date, 
				pi.cost_center, 
				pi.customer, 
				pi.boq, 
				pi.invoice_type, 
				pi.name, 
				pi.status,
				pi.gross_invoice_amount, 
				pi.price_adjustment_amount, 
				pi.net_invoice_amount,
				pi.total_received_amount,
				pi.total_balance_amount, 
				pi.total_received_amount 
			from `tabProject Invoice` as pi, `tabProject` as p 
			where pi.docstatus =1
			and p.name = pi.project
		"""
	if filters.get("project"):
		query += ' and project = "{0}"'.format(str(filters.project))
	if filters.get("from_date") and filters.get("to_date"):
		query += " and invoice_date between \'" + str(filters.from_date) + "\' and \'"+ str(filters.to_date) + "\'"
	elif filters.get("from_date") and not filters.get("to_date"):
		query += " and invoice_date >= \'" + str(filters.from_date) + "\'"
	elif not filters.get("from_date") and filters.get("to_date"):
		query += " and invoice_date <= \'" + str(filters.to_date) + "\'"

	query += " order by invoice_date desc"
	return frappe.db.sql(query)

