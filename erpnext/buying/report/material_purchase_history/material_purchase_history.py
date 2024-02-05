# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import flt

def execute(filters=None):
	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data
	
def get_columns(filters):
	columns = [
		{
			"fieldname": "item_code",
			"label": "Item Code",
			"fieldtype": "Link",
			"options": "Item",
			"width": 200
		},
		{
			"fieldname": "item_name",
			"label": "Item Name",
			"fieldtype": "Data",
			"width": 200
		},
		{
			"fieldname": "item_group",
			"label": "Item Group",
			"fieldtype": "Link",
			"options": "Item Group",
			"width": 100
		},
		{
			"fieldname": "item_sub_group",
			"label": "Item Sub Group",
			"fieldtype": "Link",
			"options":"Item Group",
			"width": 150
		},
		{
			"fieldname": "qty",
			"label": "PO QTY",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"fieldname": "uom",
			"label": "UOM",
			"fieldtype": "Link",
			"options": "UOM",
			"width": 150
		},
		{
			"fieldname": "rate",
			"label": "Rate",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 100
		},
		{
			"fieldname": "amount",
			"label": "Amount",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 100
		},
		{
			"fieldname": "po",
			"label": "Purchase Order",
			"fieldtype": "Link",
			"options": "Purchase Order",
			"width": 100
		},
		{
			"fieldname": "po_date",
			"label": "PO Date",
			"fieldtype": "Date",
			"width": 100
		},
		{
			"fieldname": "cost_center",
			"label": "Cost Center",
			"fieldtype": "Link",
			"options": "Cost Center",
			"width": 200
		},
		{
			"fieldname": "warehouse",
			"label": "Warehouse",
			"fieldtype": "Link",
			"options": "Warehouse",
			"width": 200
		},
		{
			"fieldname": "vendor_name",
			"label": "vendor Name",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"fieldname": "vendor_type",
			"label": "Vendor Type",
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "received_qty",
			"label": "Received Qty",
			"fieldtype": "Data",
			"width": 150
		},

	]
	return columns
def get_data(filters):
	data = []
	row = []
	cond = get_conditions(filters)
	po_list = frappe.db.sql("""
			select
				po_item.item_code as item_code,
				po_item.item_name as item_name,
				po_item.item_group as item_group,
				po_item.qty as qty,
				po_item.uom as uom,
				po_item.base_rate rate,
				po_item.base_amount as base_amount,
				po.name as name,
				po_item.cost_center as cost_center,
				po_item.warehouse as warehouse,
				po.transaction_date as transaction_date,
				po.supplier as supplier,
				po_item.project as project,
				po_item.received_qty as received_qty,
				po.company as company
			from
				`tabPurchase Order` po
			INNER JOIN `tabPurchase Order Item` po_item ON po.name=po_item.parent				
			where
				po.docstatus = 1
			and po.transaction_date between '{0}' and '{1}'
			{cond}
		""".format(filters.from_date,filters.to_date,cond=cond),as_dict=True)
	for q in po_list:
		item_sub_group =frappe.db.get_value("Item",q.item_code,"item_sub_group")
		supplier_type =frappe.db.get_value("Supplier",q.supplier,"supplier_name")
		row =[q.item_code, q.item_name, q.item_group, item_sub_group,q.qty,q.uom,q.rate,q.base_amount,q.name,q.transaction_date,q.cost_center,q.warehouse,q.supplier, supplier_type,q.received_qty]
		data.append(row)
	return data

def get_conditions(filters):
	cond =""
	if filters.get("cost_center"):
		cond +="""and po.cost_center ='{cost_center}'""".format(cost_center=filters.get("cost_center"))
	if filters.get("warehouse"): 
		cond += """and po_item.warehouse = '{warehouse}'""".format(warehouse=filters.get("warehouse"))
	if filters.get("item_code"): 
		cond += """and po_item.item_code = '{item_code}'""".format(item_code=filters.get("item_code"))
	if filters.get("item_group"): 
		cond += """and po_item.item_group = '{item_group}'""".format(item_group=filters.get("item_group"))
	
	return cond

	