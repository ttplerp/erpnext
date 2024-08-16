# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import cstr, getdate, flt, now

def execute(filters=None):
	columns = get_column()
	data = get_data(filters)
	return columns, data

def get_data(filters):
	from_date = now() if not filters.get("from_date") else filters.get("from_date")
	to_date = now() if not filters.get("to_date") else filters.get("to_date")

	if getdate(from_date) > getdate(to_date):
		frappe.throw("From Date cannot be greater than To Date.")
		
	data = get_pos_entries(filters, getdate(from_date), getdate(to_date))
	if len(data):
		data = prepare_pos_entries(data)

	return [] if len(data) == 0 else data

def get_pos_entries(filters, from_date, to_date):
	# data = frappe.db.sql(""" SELECT ce.pos_profile, ce.grand_total, ced.mode_of_payment, ced.closing_amount FROM `tabPOS Closing Entry` ce, `tabPOS Closing Entry Detail` ced 
	# 		WHERE ce.name=ced.parent and ce.company='{}' AND ce.posting_date BETWEEN '{}' AND '{}' cd.docstatus=1
	# 		ORDER BY ce.pos_profile""".format(filters.get("company"), getdate(from_date), getdate(to_date)), as_dict=1)
	
	data = frappe.db.sql("""
			SELECT
				p.pos_profile, sip.mode_of_payment, sum(sip.base_amount) base_amount
			FROM
				`tabPOS Invoice` p, `tabSales Invoice Payment` sip
			WHERE
				p.docstatus = 1 and
				sip.parent = p.name AND ifnull(sip.base_amount, 0) != 0 AND
				p.posting_date BETWEEN '{}' AND '{}' AND p.company = '{}'
			GROUP BY
				sip.mode_of_payment, p.pos_profile
			ORDER BY
				p.pos_profile
			""".format(from_date, to_date, filters.get("company")),
			as_dict=1,
		)

	return [] if len(data) == 0 else data

def prepare_pos_entries(pos_entries):
	data, row = {}, []
	for d in pos_entries:
		data.setdefault(d.get("pos_profile"), []).append(d)

	for key, value in data.items():
		new_data = frappe._dict({
					"pos_profile": key,
					"cash": 0.0,
					"online": 0.0,
					"grand_total": 0.0,
				})
		for d in value:
			if cstr(d.mode_of_payment) == 'Cash':
				new_data['cash'] = new_data['cash'] + d.base_amount
				new_data['grand_total'] = new_data['grand_total'] + new_data['cash']
			if cstr(d.mode_of_payment) == 'Online':
				new_data['online'] = new_data['online'] + d.base_amount
				new_data['grand_total'] = new_data['grand_total'] + new_data['online']
		
		row.append(new_data)
	return row

def get_column():
	return [
		{
			"label": _("POS Profile"),
			"fieldname": "pos_profile",
			"fieldtype": "Link",
			"options": "POS Profile",
			"width": 250,
		},
		{
			"label": _("Cash"),
			"fieldname": "cash",
			"fieldtype": "Currency",
			"options": "company:currency",
			"width": 120,
		},
		{
			"label": _("Online"),
			"fieldname": "online",
			"fieldtype": "Currency",
			"options": "company:currency",
			"width": 120,
		},
		{
			"label": _("Total Amount"),
			"fieldname": "grand_total",
			"fieldtype": "Currency",
			"options": "company:currency",
			"width": 120
		}
	]