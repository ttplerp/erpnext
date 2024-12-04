# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import getdate, get_first_day, get_last_day


def execute(filters=None):
	columns, data = get_columns(filters), get_data(filters)
	return columns, data

def get_data(filters):
	frappe.publish_progress(15, title = _("Preparing Report..."))
	query = ''
	data = []
	if filters.get('report_type') == 'Monthly Summary':
		query = get_query_monthly_summary(filters)
	else:
		query = get_query_schedule_details(filters)
	if query:
		data = frappe.db.sql(query, as_dict=True)
	frappe.publish_progress(75, title = _("Preparing Report..."))
	frappe.publish_progress(100, title = _("Preparing Report..."))
	return data

def get_query_monthly_summary(filters):
	from_date = "-".join([str(filters.get('fiscal_year')), "01", "01"])
	to_date = "-".join([str(filters.get('fiscal_year')), "12", "31"])

	query = """
			select schedule_date, 
					count(distinct(parent)) noof_assets,
					count(*) noof_schedules,
					sum(ifnull(depreciation_amount,0)) depreciation_amount,
					sum((case when ifnull(journal_entry,'') != '' then ifnull(depreciation_amount,0)
						else 0 end)) journal_entry_amount,
					sum((case when ifnull(depreciation_entry,'') != '' then ifnull(depreciation_amount,0)
						else 0 end)) depreciation_entry_amount,
					sum((case when ifnull(journal_entry,'') != '' or ifnull(depreciation_entry,'') != '' then ifnull(depreciation_amount,0)
						else 0 end)) total_posted_amount,
					sum(ifnull(ds.depreciation_amount) - 
						(case when ifnull(journal_entry,'') != '' or ifnull(depreciation_entry,'') != '' then ifnull(depreciation_amount,0)
							else 0 end) 
					) difference_amount
			from `tabDepreciation Schedule` ds
			where ds.schedule_date between "{from_date}" and "{to_date}"
			group by ds.schedule_date
		""".format(from_date=from_date, to_date=to_date)
	return query

def get_query_schedule_details(filters):
	months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
	month = str(int(months.index(filters.get('month')))+1).rjust(2,"0")

	month_start_date = "-".join([str(filters.get('fiscal_year')), month, "01"])
	month_end_date   = get_last_day(month_start_date)
	# frappe.throw(str(month_end_date))
	query = """
			select d.schedule_date, d.depreciation_amount, d.accumulated_depreciation_amount, d.depreciation_income_tax, d.accumulated_depreciation_income_tax,
				a.name, a.asset_name, a.asset_category, a.asset_sub_category
			from `tabDepreciation Entry Detail` d, `tabAsset` a
			where d.parent = a.name
			and d.schedule_date = '{end_date}'
   		""".format(end_date=month_end_date)
	 
	return query

def get_columns(filters):
	if filters.get('report_type') == 'Monthly Summary':
		return get_columns_monthly_summary()
	else:
		return get_columns_schedule_details()

def get_columns_monthly_summary():
	columns = [
		{
			"fieldname": "schedule_date",
			"label": _("Schedule"),
			"fieldtype": "Date",
			"width": 100
		},
		{
			"fieldname": "noof_assets",
			"label": _("No.of Assets"),
			"fieldtype": "Int",
			"width": 100
		},
		{
			"fieldname": "noof_schedules",
			"label": _("No.of Schedules"),
			"fieldtype": "Int",
			"width": 100
		},
		{
			"fieldname": "depreciation_amount",
			"label": _("Depreciation (A)"),
			"fieldtype": "Currency",
			"width": 150
		},
		{
			"fieldname": "journal_entry_amount",
			"label": _("Journal Entry"),
			"fieldtype": "Currency",
			"width": 150
		},
		{
			"fieldname": "depreciation_entry_amount",
			"label": _("Depreciation Entry"),
			"fieldtype": "Currency",
			"width": 150
		},
  		{
			"fieldname": "total_posted_amount",
			"label": _("Total Posted Amount (B)"),
			"fieldtype": "Currency",
			"width": 150
		},
		{
			"fieldname": "difference_amount",
			"label": _("Difference (A-B)"),
			"fieldtype": "Currency",
			"width": 150
		},
	]
	return columns

def get_columns_schedule_details():
	columns = [
		{
			"fieldname": "name",
			"label": _("Asset Code"),
			"fieldtype": "Link",
			"options": "Asset",
			"width": 150
		},
		{
			"fieldname": "asset_name",
			"label": _("Asset"),
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "asset_category",
			"label": _("Asset Category"),
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "asset_sub_category",
			"label": _("Asset Sub Category"),
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "schedule_date",
			"label": _("Schedule Date"),
			"fieldtype": "Date",
			"width": 100
		},
		{
			"fieldname": "depreciation_amount",
			"label": _("Dep. Amount"),
			"fieldtype": "Currency",
			"width": 90
		},
		{
			"fieldname": "accumulated_depreciation_amount",
			"label": _("Accumulated Dep. Amount"),
			"fieldtype": "Currency",
			"width": 150
		},
		{
			"fieldname": "depreciation_income_tax",
			"label": _("Mgt. Depreciation Amount"),
			"fieldtype": "Currency",
			"width": 150
		},
		{
			"fieldname": "accumulated_depreciation_income_tax",
			"label": _("Mgt. Accumulated Depreciation"),
			"fieldtype": "Currency",
			"width": 150
		},
	]
	return columns
