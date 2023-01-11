# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
	columns, data = get_columns(filters), get_data(filters)
	return columns, data

def get_columns(filters):
	columns = [
			 _("Branch") + ":Link/Branch:100", 
			 _("Cost Center") + ":Data:100",
			 _("Posting Date") + ":Date:100",
			 _("Desuup Name") + ":Data:100",
			 _("Desuup ID") + ":Link/Desuup:100",
			 _("Credit Account") + ":Link/Account:100",
			 _("Debit Account") + ":Link/Account:100",
			 _("Type") + ":Link/Item Group:100",
			 _("Material Code") + ":Link/Item:100",
			 _("Material Name") + ":Data:100",
			 _("Quantity") + ":Int:100",
			 _("Rate") + ":Float:100",
			 _("Amount") + ":Float:100",
			 _("Delivery Warehouse") + ":Link/Warehouse:150",
			 _("Remarks") + ":Data:200",
			 _("Journal No.") + ":Data:100",
			 _("Journal Date") + ":Date:100"

	]
	return columns

def get_data(filters):
	cond = get_conditions(filters)
	data = frappe.db.sql(
		"""
		SELECT 
			ds.branch, ds.cost_center, ds.posting_date, ds.customer_name, ds.customer, ds.credit_account, ds.debit_account, ds.naming_series, 
			soi.item_code, soi.item_name, soi.qty, soi.rate, soi.amount, soi.warehouse, ds.remarks, ds.journal_no, ds.journal_date
		FROM `tabDesuung Sales` ds, `tabSales Order Item` soi 
		WHERE ds.name = soi.parent and ds.docstatus = 1 and ds.posting_date between '{from_date}' and '{to_date}'
		{condition}
		""".format(from_date=filters.from_date, to_date=filters.to_date, condition=cond))

	return data

def get_conditions(filters):
	cond = ""
	if filters.desuupid:
		cond += "and customer='{}'".format(filters.desuupid)
	return cond
