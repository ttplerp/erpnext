# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt


def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_data(filters):
	data = []

	result = frappe.db.sql("""
					select pri.item_code, pri.item_name, pri.qty, pri.base_rate, pri.cost_center, pr.status, pr.name purchase_receipt, (pri.base_rate * pri.qty) as amount, pri.name 'pri_name',
						a.name asset, a.asset_rate, a.asset_name, a.status asset_status, a.purchase_receipt asset_pr,
						(
							select sum(asset_rate) from tabAsset a2
							where a2.purchase_receipt = pr.name and a2.docstatus = 1 and a2.asset_rate = pri.base_rate and a2.item_code = pri.item_code
						) as issued_amount
					from `tabPurchase Receipt` pr join `tabPurchase Receipt Item` pri on pri.parent=pr.name
					left join tabAsset a on a.purchase_receipt = pr.name and a.asset_rate=pri.base_rate
					where pr.name = pri.parent and pr.docstatus=1
						and pri.is_fixed_asset = 1
						and pr.posting_date between '{from_date}' and '{to_date}'
					order by pr.status, pr.name, pri.item_code, pri.name """.format(from_date=filters.get('from_date'), to_date=filters.get('to_date')), as_dict=True)
	
	grouped_data = {}
	for r in result:
		emp_key = (r.pri_name)
		grouped_data.setdefault(emp_key, []).append(r)
	for key, items in grouped_data.items():
		first = items[0]
		data.append({
			"purchase_receipt": first.purchase_receipt,
			"item_code": first.item_code,
			"item_name": first.item_name,
			"base_rate": first.base_rate,
			"qty": first.qty,
			"amount": first.amount,
			"cost_center": first.cost_center,
			"purchase_status": first.status,
			"asset_code": first.asset,
			"asset_name": first.asset_name,
			"asset_status": first.asset_status,
			"asset_pr": first.asset_pr,
			"asset_rate": first.asset_rate,
			"balance_amount": flt(first.amount) - flt(first.issued_amount)
		})

		for itm in items[1:]:
			data.append({
				"purchase_receipt": "-",
				"item_code": "-",
				"item_name": "-",
				"base_rate": "",
				"qty": "",
				"amount": "",
				"cost_center": "-",
				"purchase_status": "-",
				"asset_code": itm.asset,
				"asset_name": itm.asset_name,
				"asset_status": itm.asset_status,
				"asset_pr": first.asset_pr,
				"asset_rate": first.asset_rate,
				"balance_amount": ""
			})

	return data
	# frappe.throw("<pre>{}</pre>".format(frappe.as_json(data)))


def get_columns():
	return [
		{
			"fieldname": "purchase_receipt",
			"label": "Purchase Receipt",
			"fieldtype": "Link",
			"options": "Purchase Receipt",
			"width": 120
		},
		{
			"fieldname": "item_name",
			"label": "Item Name",
			"fieldtype": "Data",
			"width": 200
		},
		{
			"fieldname": "item_code",
			"label": "Item Code",
			"fieldtype": "Link",
			"options": "Item",
			"width": 120
		},
		{
			"fieldname": "qty",
			"label": "Total Quantity",
			"fieldtype": "Float",
			"width": 120
		},
		{
			"fieldname": "base_rate",
			"label": "Rate",
			"fieldtype": "Float",
			"width": 150
		},
		{
			"fieldname": "amount",
			"label": "Amount",
			"fieldtype": "Float",
			"width": 150
		},
		{
			"fieldname": "balance_amount",
			"label": "Balance Asset Value",
			"fieldtype": "Float",
			"width": 150
		},
		{
			"fieldname": "cost_center",
			"label": "Cost Center",
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "purchase_status",
			"label": "PR Status",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "asset_code",
			"label": "Asset Code",
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "asset_name",
			"label": "Asset Name",
			"fieldtype": "Data",
			"width": 200
		},
		{
			"fieldname": "asset_rate",
			"label": "Asset Rate",
			"fieldtype": "Float",
			"width": 200
		},
		{
			"fieldname": "asset_status",
			"label": "Asset Status",
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "asset_pr",
			"label": "Asset (Purchase Receipt)",
			"fieldtype": "Data",
			"width": 150
		},
	]