# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def execute(filters=None):
	filters = frappe._dict(filters or {})
	if filters.from_date > filters.to_date:
		frappe.throw(_("From Date cannot be greater than To Date"))

	columns = get_columns(filters)
	data = get_data(filters)

	return columns, data

def get_data(filters):

	data = []

	# customer_details = get_customer_details()
	item_details = get_item_details()
	sales_order_records = get_sales_order_details(filters)

	for record in sales_order_records:
		# customer_record = customer_details.get(record.customer)
		item_record = item_details.get(record.item_code)
		row = {
			"item_code": record.get("item_code"),
			"item_name": item_record.get("item_name"),
			"item_group": item_record.get("item_group"),
			"quantity": record.get("qty"),
			"uom": record.get("uom"),
			"rate": record.get("base_rate"),
			"amount": record.get("base_amount"),
			"posting_date": record.get("posting_date"),
			"customer": record.get("customer"),
			"pos_profile": record.get("pos_profile"),
			"pos_invoice": record.get("name")
		}
		data.append(row)

	return data


def get_conditions(filters):
	conditions = ""
	if filters.get("from_date"):
		conditions += "AND poi.posting_date >= '%s'" % filters.from_date

	if filters.get("to_date"):
		conditions += "AND poi.posting_date <= '%s'" % filters.to_date
	
	if filters.get("company"):
		conditions += "AND poi.company = '%s'" % filters.company

	if filters.get("item_code"):
		conditions += "AND poi_item.item_code = '%s'" % filters.item_code

	if filters.get("pos_profile"):
		conditions += "AND poi.pos_profile = '%s'" % filters.pos_profile

	return conditions


def get_customer_details():
	details = frappe.get_all("Customer", fields=["name", "customer_name", "customer_group"])
	customer_details = {}
	for d in details:
		customer_details.setdefault(
			d.name, frappe._dict({"customer_name": d.customer_name, "customer_group": d.customer_group})
		)
	return customer_details


def get_item_details():
	details = frappe.db.get_all("Item", fields=["name", "item_name", "item_group"])
	item_details = {}
	for d in details:
		item_details.setdefault(
			d.name, frappe._dict({"item_name": d.item_name, "item_group": d.item_group})
		)
	return item_details


def get_sales_order_details(filters):
	conditions = get_conditions(filters)

	return frappe.db.sql(
		"""
		SELECT
			poi_item.item_code, poi_item.qty,
			poi_item.uom, poi_item.base_rate, poi_item.base_amount,
			poi.name, poi.posting_date, poi.customer, poi.pos_profile
		FROM
			`tabPOS Invoice` poi, `tabPOS Invoice Item` poi_item
		WHERE
			poi.name = poi_item.parent
			AND poi.docstatus = 1 {0}
	""".format(
			conditions
		),
		as_dict=1,
	)

def get_columns(filters):
	return [
		{
			"label": _("Item Code"),
			"fieldtype": "Link",
			"fieldname": "item_code",
			"options": "Item",
			"width": 120,
		},
		{"label": _("Item Name"), "fieldtype": "Data", "fieldname": "item_name", "width": 140},
		{
			"label": _("Item Group"),
			"fieldtype": "Link",
			"fieldname": "item_group",
			"options": "Item Group",
			"width": 120,
		},
		{"label": _("Quantity"), "fieldtype": "Float", "fieldname": "quantity", "width": 150},
		{"label": _("UOM"), "fieldtype": "Link", "fieldname": "uom", "options": "UOM", "width": 100},
		{"label": _("Rate"), "fieldname": "rate", "options": "Currency", "width": 120},
		{"label": _("Amount"), "fieldname": "amount", "options": "Currency", "width": 120},
		{
			"label": _("Posting Date"),
			"fieldtype": "Date",
			"fieldname": "posting_date",
			"width": 110,
		},
		{
			"label": _("Customer"),
			"fieldtype": "Link",
			"fieldname": "customer",
			"options": "Customer",
			"width": 100,
		},
		{
			"label": _("POS Profile"),
			"fieldtype": "Link",
			"fieldname": "pos_profile",
			"options": "POS Profile",
			"width": 150,
		},
		{
			"label": _("POS Invoice"),
			"fieldtype": "Link",
			"fieldname": "pos_invoice",
			"options": "POS Invoice",
			"width": 200,
		}
	]