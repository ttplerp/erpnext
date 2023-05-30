# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt

def execute(filters=None):
	columns = get_columns()
	data    = get_data(filters)

	return columns, data

def get_data(filters):
	cond = get_conditions(filters)

	query = """
		SELECT
			name as tran_no,
			posting_date as tran_date,
			'Receipt' as tran_type,
			imprest_type as imprest_type,
			amount as opening_balance,
			adjusted_amount as amount,
			balance_amount as closing_balance,
			title as title,
			remarks as remarks,
			branch as branch,
			owner as createby,
			creation as createdt,
			modified_by as modifyby,
			modified as modifydt
		FROM `tabImprest Advance`
		WHERE docstatus != 2
		{}
		UNION ALL
		SELECT
			name as tran_no,
			posting_date as tran_date,
			'Purchase' as tran_type,
			imprest_type as imprest_type,
			opening_balance as opening_balance,
			total_amount as amount,
			balance_amount as closing_balance,
			title as title,
			remarks as remarks,
			branch as branch,
			owner as createby,
			creation as createdt,
			modified_by as modifyby,
			modified as modifydt
		FROM `tabImprest Recoup`
		WHERE docstatus != 2
		{}
		ORDER BY branch, imprest_type, tran_date
	""".format(cond, cond)

	result = frappe.db.sql(query, as_dict=True)

	return result

def get_conditions(filters):
	cond = []

	if filters.get('branch'):
		cond.append('branch = "{0}"'.format(filters.get('branch')))
	
	if filters.get('imprest_type'):
		cond.append('imprest_type = "{0}"'.format(filters.get('imprest_type')))

	if filters.get('from_date') and filters.get('to_date'):
		cond.append('date(posting_date) between "{0}" and "{1}"'.format(filters.from_date, filters.to_date))
	
	if cond:
		return 'and '+ str(' and '.join(cond))
	else:
		return ""
		
def get_columns():
	return [
		{
			"fieldname": "tran_no",
			"label": _("Transaction#"),
			"fieldtype": "Data",
			"width": 120,
		},
		{
			"fieldname": "tran_date",
			"label": "Date",
			"fieldtype": "Date",
			"width": 120
		},
		{
			"fieldname": "tran_type",
			"label": _("Type"),
			"fieldtype": "Data",
			"width": 80,
		},
		{
			"fieldname": "imprest_type",
			"label": _("Imprest Type"),
			"fieldtype": "Data",
			"width": 120,
		},
		{
			"fieldname": "opening_balance",
			"label": _("Opening Balance"),
			"fieldtype": "Currency",
			"width": 120,
		},
		{
			"fieldname": "amount",
			"label": _("Amount"),
			"fieldtype": "Currency",
			"width": 120,
		},
		{
			"fieldname": "closing_balance",
			"label": _("Closing Balance"),
			"fieldtype": "Currency",
			"width": 120,
		},
		{
			"fieldname": "status",
			"label": _("Status"),
			"fieldtype": "Data",
			"width": 120,
		},
		{
			"fieldname": "title",
			"label": _("Title"),
			"fieldtype": "Data",
			"width": 180,
		},
		{
			"fieldname": "imprest_type",
			"label": _("Imprest Type"),
			"fieldtype": "Data",
			"width": 120,
		},
		{
			"fieldname": "remarks",
			"label": _("Remarks"),
			"fieldtype": "Data",
			"width": 180
		},
		{
			"fieldname": "branch",
			"label": _("Branch"),
			"fieldtype": "Link",
			"options": "Branch",
			"width": 180
		},
		{
			"fieldname": "createby",
			"label": _("Created By"),
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "createdt",
			"label": _("Created Date"),
			"fieldtype": "Date",
			"width": 120
		},
		{
			"fieldname": "modifyby",
			"label": _("Modified By"),
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "modifydt",
			"label": _("Modified Date"),
			"fieldtype": "Date",
			"width": 120
		},
	]        
