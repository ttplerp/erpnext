# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data

def get_data(filters):
	data=[]
	schedule_date = filters.get("schedule_date")
	conditions = get_conditions(filters)
	
	assets = frappe.db.sql("""Select a.* From tabAsset a, `tabDepreciation Schedule` ds Where a.name=ds.parent and a.docstatus=1 
					and ds.income_depreciation_amount > 0 and ds.schedule_date='{s_date}' {cond} order by a.asset_category""".format(s_date=schedule_date, cond=conditions), as_dict=1)
	for d in assets:
		row = frappe._dict()
		max_idx = frappe.db.sql("""select max(idx) idx from `tabDepreciation Schedule` where parent='{asset}' and income_depreciation_amount > 0""".format(asset=d.name), as_dict=1)
		if not max_idx:
			continue
		# frappe.throw(str(max_idx[0].idx))
		dep_schedule = frappe.db.sql("""select * from `tabDepreciation Schedule` where parent='{asset}' and income_depreciation_amount > 0 and idx={idx} and schedule_date='{s_date}'""".format(asset=d.name, idx=max_idx[0].idx, s_date=schedule_date), as_dict=1)
		if dep_schedule:
			row.update(d)
			row.scheudle_date = dep_schedule[0].schedule_date
			row.income_depreciation_amount = dep_schedule[0].income_depreciation_amount
			data.append(row)
	return data

def get_conditions(filters):
	conditions = ""
	if filters.get("asset_category"):
		conditions += " and a.asset_category='{0}' ".format(filters.get("asset_category"))
	
	return conditions

def get_columns(filters):
	return [
		{
			"label": _("Asset"),
			"fieldname": "name",
			"fieldtype": "Link",
			"options": "Asset",
			"width": 190,
		},
		{
			"label": _("Asset Category"),
			"fieldname": "asset_category",
			"fieldtype": "Link",
			"options": "Asset Category",
			"width": 190,
		},
		{
			"label": _("Status"),
			"fieldname": "status",
			"fieldtype": "Data",
			"options": "",
			"width": 150,
		},
		{
			"label": _("Gross Purchase Amount"),
			"fieldname": "gross_purchase_amount",
			"fieldtype": "Float",
			"options": "",
			"width": 120,
		},
		{
			"label": _("Schedule Date"),
			"fieldname": "scheudle_date",
			"fieldtype": "Date",
			"options": "",
			"width": 120,
		},
		{
			"label": _("Income Depreciation Amount"),
			"fieldname": "income_depreciation_amount",
			"fieldtype": "Float",
			"options": "",
			"width": 120,
		},
	]
	