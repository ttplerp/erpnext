# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data

def get_columns():
	return [
		{
			"fieldname": "item_name",
			"label": _("Particulars"),
			"fieldtype": "Data",
			"options": "",
			"width": 250
		},
		{
			"fieldname": "qty",
			"label": _("Qty"),
			"fieldtype": "Float",
			"width": 90
		},
		{
			"fieldname": "date",
			"label": _("Date"),
			"fieldtype": "Data",
			"width": 250
		},
		{
			"fieldname": "description",
			"label": _("Remarks"),
			"fieldtype": "Data",
			"width": 300
		}
	]

def get_data(filters):
	if not filters.desuupid and not filters.others:
		return []
	condition = get_condition(filters)
	query = frappe.db.sql(""" 
			Select sed.item_name, ifnull(sum(sed.qty),0),
				GROUP_CONCAT(se.posting_date SEPARATOR '; ') date,
				GROUP_CONCAT(sed.description SEPARATOR '; ') remarks
			From `tabStock Entry` se
			Inner Join `tabStock Entry Detail` sed On sed.parent = se.name 
			Where se.docstatus = 1 and se.purpose = 'Material Issue' and se.entry_type = 'Soelra' {0}
			group by item_code order by item_code""".format(condition))
	return query

def get_condition(filters):
	condition = ''
	if filters.desuupid:
		condition = " and issue_to_desuup = '{0}'".format(filters.desuupid)
	
	if filters.others:
		condition = " and issue_to_others like '%{0}%'".format(filters.others)

	return condition