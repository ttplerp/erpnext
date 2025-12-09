# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import getdate, flt


def execute(filters=None):
	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data
def get_columns(filters):
	return [
		{
			"label": "Asset Movement",
			"fieldname": "Asset Movement",
			"fieldtype": "Link",
			"options": "Asset Movement",
			"width": 200,
		},
		{
			"label": "Transaction Date",
			"fieldname": "transaction_date",
			"fieldtype": "Date",
			"width": 120,
		},
		{
			"label": "Asset",
			"fieldname": "asset",
			"fieldtype": "Link",
			"options": "Asset",
			"width": 200,
		},
		{
			"label": "Asset Category",
			"fieldname": "asset_category",
			"fieldtype": "Link",
			"options": "Asset Category",
			"width": 200,
		},
		{
			"label": "Asset Value",
			"fieldname": "asset_value",
			"fieldtype": "Currency",
			"width": 150,
		},
		{
			"label": "Accumulated Depreciation",
			"fieldname": "accumulated_depreciation",
			"fieldtype": "Currency",
			"width": 180,
		},
		{
			"label": "Accumulated Account",
			"fieldname": "accumulated_account",
			"fieldtype": "Link",
			"options": "Account",
			"width": 200,
		},
	]

def get_data(filters):
	from_date = getdate("2025-01-01")
	to_date = getdate("2025-01-31")
	data = []
	for d in frappe.db.sql(""" 
		select b.asset, a.name 'Asset Movement', a.transaction_date, c.asset_category 
		from `tabAsset Movement Item` b, `tabAsset Movement` a, tabAsset c where a.name=b.parent and b.asset=c.name and a.name in (
			select distinct t1.voucher_no
			from `tabGL Entry` t1
			inner join `tabAccount` a on a.name = t1.account
			inner join `tabTransaction Mapping` t2 on t2.name = t1.voucher_type and t2.transaction_type in ('CASA', 'GL')
			left join `tabCurrency` c on c.name = a.account_currency
			where t1.posting_date between '{}' and '{}'
				and t1.cbs_enabled = 1
				and t1.is_cancelled = 0
				and t1.voucher_type = 'Asset Movement'
				and exists(select 1
					from `tabCBS Entry Upload` ceu
					where ceu.gl_entry = t1.name
					and ceu.docstatus != 2)

			order by posting_date, voucher_type, voucher_no
		) order by a.name
		""".format(from_date, to_date), as_dict=1):
		row = frappe._dict()
		row.update(d)
		
		asset = frappe.get_doc("Asset", d.asset)
		row.asset_value = asset.gross_purchase_amount
		income_tax_value_after_depreciation = 0.0
		if asset.schedules:
			for i in asset.schedules:
				if getdate(d.transaction_date) < getdate(to_date) and i.schedule_date == getdate(to_date):
					income_tax_value_after_depreciation = flt(i.income_accumulated_depreciation - i.income_depreciation_amount, 2)
				elif getdate(d.transaction_date) == getdate(to_date) and i.schedule_date == getdate(to_date):
					income_tax_value_after_depreciation = flt(i.income_accumulated_depreciation, 2)
			row.accumulated_depreciation = income_tax_value_after_depreciation
		row.accumulated_account = frappe.db.get_value("Asset Category Account", {"parent": d.asset_category}, "accumulated_depreciation_account")
		data.append(row)

	return data
