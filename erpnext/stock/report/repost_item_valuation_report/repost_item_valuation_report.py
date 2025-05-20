# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt


import frappe
from frappe import _
from frappe.query_builder.functions import CombineDatetime
from frappe.utils import cint, flt
from pypika.terms import ExistsCriterion

from erpnext.stock.doctype.inventory_dimension.inventory_dimension import get_inventory_dimensions
from erpnext.stock.doctype.serial_no.serial_no import get_serial_nos
from erpnext.stock.doctype.stock_reconciliation.stock_reconciliation import get_stock_balance_for


def execute(filters=None):
	# is_reposting_item_valuation_in_progress()
	# include_uom = filters.get("include_uom")
	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data


def get_columns(filters):
	columns = [
		{"label": _("Date"), "fieldname": "posting_date", "fieldtype": "Date", "width": 150},
		{"label": _("Repost ID"), "fieldname": "id", "fieldtype": "Data", "width": 100},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 100},
		{
			"label": _("Item Code"),
			"fieldname": "item_code",
			"fieldtype": "Link",
			"options": "Item",
			"width": 100,
		},
		{"label": _("Item Name"), "fieldname": "item_name", "width": 100},
		{
			"label": _("Item Group"),
			"fieldname": "item_group",
			"fieldtype": "Link",
			"options": "Item Group",
			"width": 100,
		},
		{
			"label": _("Item Sub Group"),
			"fieldname": "item_sub_group",
			"fieldtype": "Link",
			"options": "Item Sub Group",
			"width": 120,
		},
		{
			"label": _("Stock UOM"),
			"fieldname": "stock_uom",
			"fieldtype": "Link",
			"options": "UOM",
			"width": 90,
		},
		{
			"label": _("Warehouse"),
			"fieldname": "warehouse",
			"fieldtype": "Link",
			"options": "Warehouse",
			"width": 150,
		},
		{"label": _("Voucher Type"), "fieldname": "voucher_type", "width": 110},
		{
			"label": _("Voucher #"),
			"fieldname": "voucher_no",
			"fieldtype": "Dynamic Link",
			"options": "voucher_type",
			"width": 100,
		},
	]

	return columns

def get_data(filters):
	cond = get_cond(filters)
	data = []
	for a in frappe.db.sql("""
		select name as id, status, posting_date, voucher_type, voucher_no from `tabRepost Item Valuation`
		{}
	""".format(cond), as_dict=1):
		a.posting_date = str(a.posting_date).split(" ")[0]
		doc = frappe.get_doc(a.voucher_type, a.voucher_no)
		if a.voucher_type in ("Delivery Note", "Purchase Receipt Item", "Stock Reconciliation"):
			for dni in doc.items:
				data.append({
					"item_code": dni.item_code, 
					"item_name": dni.item_name, 
					"item_group": dni.item_group, 
					"item_sub_group": frappe.db.get_value("Item", dni.item_code, "item_sub_group"),  
					"stock_uom": frappe.db.get_value("Item", dni.item_code, "stock_uom"), 
					"warehouse": dni.warehouse, 
					"id": a.id, 
					"status": a.status, 
					"posting_date": a.posting_date, 
					"voucher_type": a.voucher_type,
					"voucher_no": a.voucher_no,
					})
		elif a.voucher_type == "Stock Entry":
			for sed in doc.items:
				if not sed.s_warehouse:
					sed.s_warehouse = ""
				if not sed.t_warehouse:
					sed.t_warehouse = ""
				data.append({
					"item_code": sed.item_code, 
					"item_name": sed.item_name, 
					"item_group": sed.item_group, 
					"item_sub_group": frappe.db.get_value("Item", sed.item_code, "item_sub_group"),  
					"stock_uom": frappe.db.get_value("Item", sed.item_code, "stock_uom"), 
					"warehouse": sed.s_warehouse+", "+sed.t_warehouse, 
					"id": a.id, 
					"status": a.status, 
					"posting_date": a.posting_date, 
					"voucher_type": a.voucher_type,
					"voucher_no": a.voucher_no,
					})
		# data.append(a)
	return data

def get_cond(filters):
	if not filters.get("from_date"):
		frappe.throw("Please set from date")
	if not filters.get("to_date"):
		frappe.throw("Please set to date")
	cond = f"""where docstatus = 1 and based_on = 'Transaction' and posting_date between '{filters.get("from_date")}' and '{filters.get("to_date")}'"""
	if filters.get("status") and filters.get("status") != "":
		cond += f""" and status = '{filters.get("status")}'"""
	return cond

