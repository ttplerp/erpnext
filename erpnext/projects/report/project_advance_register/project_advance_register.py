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
                ("Date") + ":Data:80",
                ("Cost Center") + ":Data:120",
                ("Customer")+ ":Data:100",
                ("Claimed") + ":Currency:140",
                ("Received (A)") + ":Currency:140",
                ("Adjusted (B)") + ":Currency:140",
                ("Balance (C=A-B)")+ ":Currency:140"
        ]

def get_data(filters):
        query =  """
			select 
				p.project_name,
				ad.advance_date, 
				ad.cost_center, 
				ad.customer, 
				ad.advance_amount, 
				ad.received_amount, 
				ad.adjustment_amount, 
				ad.balance_amount 
			from `tabProject Advance` as ad, `tabProject` p 
			where ad.docstatus = 1
			and   p.name = ad.project
	"""
        if filters.get("project"):
                query += " and project = \'" + str(filters.project) + "\'"

        if filters.get("from_date") and filters.get("to_date"):
                query += " and advance_date between \'" + str(filters.from_date) + "\' and \'"+ str(filters.to_date) + "\'"
        elif filters.get("from_date") and not filters.get("to_date"):
                query += " and advance_date >= \'" + str(filters.from_date) + "\'"
        elif not filters.get("from_date") and filters.get("to_date"):
                query += " and advance_date <= \'" + str(filters.to_date) + "\'"

        query += " order by advance_date desc"
        return frappe.db.sql(query)

