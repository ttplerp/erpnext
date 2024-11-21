# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt
from frappe import _

def execute(filters=None):
	columns, data = [], []
	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data

def get_columns(filters):
	return [
		{"fieldtype": "Link",	"fieldname": "boq", "label": _("BOQ"), "options": "BOQ", "width": 120},
		{"fieldtype": "Link",	"fieldname": "location", "label": _("Location"), "options": "Location", "width": 150},
		{"fieldtype": "Date",	"fieldname": "posting_date", "label": _("Posting Date"), "width": 120},
		{"fieldtype": "Link",	"fieldname": "bsr_code", "label": _("BSR Code"), "options": "Bhutan Schedule of Rates", "width": 120},
		{"fieldtype": "Data",	"fieldname": "description", "label": _("Description"), "width": 250},
		{"fieldtype": "Float",	"fieldname": "no", "label": _("No"), "width": 80},
		{"fieldtype": "Float",	"fieldname": "length", "label": _("Length"), "width": 80},
		{"fieldtype": "Float",	"fieldname": "breath", "label": _("Breath"), "width": 80},
		{"fieldtype": "Float",	"fieldname": "height", "label": _("Height"), "width": 80},
		{"fieldtype": "Float",	"fieldname": "coefficeient", "label": _("Coefficient"), "width": 100},
		{"fieldtype": "Float",	"fieldname": "rate", "label": _("Rate (Nu.)"), "width": 100},
		{"fieldtype": "Float",	"fieldname": "quantity", "label": _("Quantity"), "width": 80},
		{"fieldtype": "Float",	"fieldname": "amount", "label": _("Amount (Nu.)"), "width": 150},
		{"fieldtype": "Link",	"fieldname": "uom", "label": _("UOM"), "options": "UOM", "width": 80},
	]

def get_data(filters):
	cond = ""
	data = []
	rom_data = {}
	if filters.from_date:
		cond += " and t1.posting_date >= '{}'".format(filters.get("from_date"))
	if filters.to_date:
		cond += " and t1.posting_date <= '{}'".format(filters.get("to_date"))
	if filters.project:
		cond += " and t1.project = '{}'".format(filters.get("project"))
	data = frappe.db.sql("""
		select 
			t1.boq, t2.location,
			t1.posting_date, t1.bsr_code, t1.description,
			t2.no,
			t2.length,
			t2.breadth,
			t2.height,
			t2.coefficient,
			t2.quantity,
			t1.uom,
			t1.rate,
			t1.amount
		from `tabRecord Of Measurement` t1, `tabRecord Of Measurement Item` t2
		where t2.parent = t1.name
		and t1.docstatus = 1
		{}
		order by t1.bsr_code, t1.posting_date
	""".format(cond),as_dict=1)

	return data

