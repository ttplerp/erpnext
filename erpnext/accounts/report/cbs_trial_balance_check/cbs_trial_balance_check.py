# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from erpnext.integrations.cbs_db import trial_balance_check

def execute(filters=None):
	columns, data = [], []
	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data

def get_data(filters):
	cond = ''
	data=[]
	if filters.get("report_date"):
		if filters.get("sol_id"):
			data = trial_balance_check(sol_id=filters.get("sol_id"), report_date=filters.get("report_date"))
		else:
			data = trial_balance_check(sol_id=None, report_date=filters.get("report_date"))

	return data

def get_columns(filters):
	columns = [
		{
			"fieldname": "sol_id",
			"label": _("SOL ID"),
			"fieldtype": "Data",
			"width": 100
		},
		{
			"fieldname": "debit",
			"label": _("Total Debit"),
			"fieldtype": "Currency",
			"width": 250
		}, 
		{
			"fieldname": "credit",
			"label": _("Total Credit"),
			"fieldtype": "Currency",
			"width": 250
		},
		{
            "fieldname": "variance",
            "label": _("Variance"),
            "fieldtype": "Data",
            "width": 250
        },
	]
	return columns
