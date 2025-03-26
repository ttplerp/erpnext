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
			#frappe.throw("hi")
		else:
			res = frappe.db.get_all('CBS Entry Upload', {'cbs_entry': filters.get('cbs_entry')}, ['*'])
			#frappe.throw('hi1')
	else:
		if filters.get('voucher_type') and filters.get('voucher_no') and frappe.db.exists('CBS Entry Upload', {'voucher_type': filters.get('voucher_type'), 'voucher_no': filters.get('voucher_no')}):
			res = frappe.db.get_all('CBS Entry Upload', {'voucher_type': filters.get('voucher_type'), 'voucher_no': filters.get('voucher_no')}, ['*'])
			#frappe.throw("hi2")
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
			"fieldname": "journal_entry_type",
			"label": _("Journal Entry Type"),
			"fieldtype": "Data",
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

@frappe.whitelist()
def check_against_linked_docs(transaction_list):
	list_transactions = []
	transaction_list = json.loads(transaction_list)
	# frappe.throw(str(transaction_list))
	for trnx in set(transaction_list):
		trn = trnx.split("||")
		voucher_type = trn[0]
		voucher_no = trn[1]
		cbs_doctypes = []
		for doc in frappe.db.get_all("Transaction Mapping", filters={"transaction_type": ["not in", ("IGNORE",  "", None)]}, fields=["name"]):
			cbs_doctypes.append(doc.name)
		if frappe.db.exists("GL Entry", {"voucher_no": voucher_no, "is_cancelled": 0}):
			#Checking Forward Linked Transactions-----
			for f_link in frappe.db.get_all("GL Entry", filters={"voucher_type": voucher_type, "is_cancelled": 0, "against_voucher": voucher_no, "voucher_no": ["!=", voucher_no]}, fields=["voucher_type", "voucher_no"], group_by="voucher_no"):
				if not frappe.db.exists("CBS Entry Upload", {"voucher_no": f_link.voucher_no}) and f_link.voucher_type in cbs_doctypes:
					list_transactions.append(f_link.voucher_type+"||"+f_link.voucher_no)
			#Checking Backward Linked Transactions----
			for b_link in frappe.db.get_all("GL Entry", filters={"voucher_type": voucher_type, "is_cancelled": 0, "voucher_no": voucher_no, "against_voucher": ["!=", voucher_no]}, fields=["against_voucher_type", "against_voucher"], group_by="against_voucher"):
				if not frappe.db.exists("CBS Entry Upload", {"voucher_no": b_link.against_voucher}) and (b_link.against_voucher_type in cbs_doctypes) and frappe.db.exists("GL Entry", {"voucher_no": b_link.against_voucher}):
					list_transactions.append(b_link.against_voucher_type+"||"+b_link.against_voucher)
				# if frappe.db.exists("GL Entry", {"voucher_no": b_link.against_voucher}):
					
	return list_transactions


