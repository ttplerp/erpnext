# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.t

from __future__ import unicode_literals
import frappe
from frappe import _
from erpnext.cbs_integration.doctype.cbs import get_data
from frappe.utils import getdate
import json

def execute(filters=None):
	columns = get_columns(filters)
	data = get_report_data(filters)
	return columns, data

def get_report_data(filters):
	res, data = [], []

	if filters.get('cbs_entry'):
		if filters.get('voucher_type') and filters.get('voucher_no'):
			res = frappe.db.get_all('CBS Entry Upload', {'cbs_entry': filters.get('cbs_entry'), 'voucher_type': filters.get('voucher_type'), 'voucher_no': filters.get('voucher_no')}, ['*'])
		else:
			res = frappe.db.get_all('CBS Entry Upload', {'cbs_entry': filters.get('cbs_entry')}, ['*'])
	else:
		if filters.get('voucher_type') and filters.get('voucher_no') and frappe.db.exists('CBS Entry Upload', {'voucher_type': filters.get('voucher_type'), 'voucher_no': filters.get('voucher_no')}):
			res = frappe.db.get_all('CBS Entry Upload', {'voucher_type': filters.get('voucher_type'), 'voucher_no': filters.get('voucher_no')}, ['*'])
		else:
			res = get_data(doctype=filters.get("voucher_type"), docname=filters.get("voucher_no"), from_date=filters.get("from_date"), to_date=filters.get("to_date"))

	if filters.get('show_errors') and res:
		for i in res:
			row = frappe._dict(i)
			if row.error:
				data.append(row)
	else:
		data = res
	return data

def get_columns(filters):
	columns = [
		{
			"fieldname": "voucher_type",
			"label": _("Voucher Type"),
			"fieldtype": "Data",
			# "options": "DocType",
			"width": 100
		},
		{
			"fieldname": "voucher_no",
			"label": _("Voucher No"),
			"fieldtype": "Dynamic Link",
			"options": "voucher_type",
			"width": 100
		},
		{
			"fieldname": "account",
			"label": _("Account"),
			"fieldtype": "Link",
			"options": "Account",
			"width": 280
		},
		{
			"fieldname": "debit",
			"label": _("Debit"),
			"fieldtype": "Currency",
			"width": 120
		}, 
		{
			"fieldname": "credit",
			"label": _("Credit"),
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"fieldname": "remarks",
			"label": _("Remarks"),
			"fieldtype": "Data",
			"width": 250
		},
		{
			"fieldname": "cbs_entry",
			"label": _("CBS Entry"),
			"fieldtype": "Link",
			"options": "CBS Entry",
			"width": 140
		},
		{
			"fieldname": "gl_type",
			"label": _("GL Type"),
			"fieldtype": "Data",
			"width": 110
		},
		{
			"fieldname": "branch_code",
			"label": _("Initiating Branch"),
			"fieldtype": "Data",
			"width": 60
		},
		{
			"fieldname": "account_number",
			"label": _("GL Code"),
			"fieldtype": "Data",
			"width": 120
		}, 
		{
			"fieldname": "amount",
			"label": _("Amount"),
			"fieldtype": "Currency",
			"width": 120
		},  
		{
			"fieldname": "processing_branch",
			"label": _("Processing Branch"),
			"fieldtype": "Data",
			"width": 80
		},
		{
			"fieldname": "posting_date",
			"label": _("Posting Date"),
			"fieldtype": "Data",
			"width": 100
		},
		{
			"fieldname": "gl_entry",
			"label": _("GL Entry"),
			"fieldtype": "Link",
			"options": "GL Entry",
			"width": 100
		},
	]
	return columns

