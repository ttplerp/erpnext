# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt

def execute(filters=None):
	if not filters:
		filters = {}
	columns, data = [], []
	data = get_data(filters)
	if not data:
		return columns, data
	columns = get_columns(filters)
	return columns, data

def get_conditions(filters):
	conditions = ""
	if filters.get("company"):
		conditions += " and company = %(company)s"
	
	if filters.get("currency"):
		conditions += " and currency = %(currency)s"

	return conditions, filters

def get_data(filters):
	data = []
	conditions, filters = get_conditions(filters)
	
	query = """
		select posting_date, branch, cost_center, currency, exchange_rate, amount, base_amount, exchange_type
		from `tabForeign Exchange`
		where docstatus = 1 {conditions}
		order by posting_date asc
	""".format(conditions=conditions)
	
	fetched_data = frappe.db.sql(query, filters, as_dict=True)
	
	balance = 0.0
	for d in fetched_data:
		if d.exchange_type == "Buy":
			d.buy = flt(d.amount)
			d.sell = 0.0
			balance += d.buy
		elif d.exchange_type == "Sell":
			d.sell = flt(d.amount)
			d.buy = 0.0 
			balance -= d.sell
		else:
			d.buy = 0.0
			d.sell = 0.0
		d.balance = balance  # Store the running balance for the current record
		data.append(d)
		
	return data

def get_columns(filters):
	return [
		{"label": _("Posting Date"), "fieldname": "posting_date", "fieldtype": "Date", "width": 120},
		{"label": _("Currency"), "fieldname": "currency", "fieldtype": "Link", "options": "Currency", "width": 90},
		{"label": _("Buy"), "fieldname": "buy", "fieldtype": "Data", "width": 120},
		{"label": _("Sell"), "fieldname": "sell", "fieldtype": "Data", "width": 120},
		{"label": _("Balance"), "fieldname": "balance", "fieldtype": "Data", "width": 120},
		{"label": _("Rate (Nu.)"), "fieldname": "exchange_rate", "fieldtype": "Data", "width": 120},
		{"label": _("Amount (BTN)"), "fieldname": "base_amount", "fieldtype": "Currency", "width": 150},
	]