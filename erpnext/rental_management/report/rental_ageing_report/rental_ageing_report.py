# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import formatdate, date_diff, today, nowdate, getdate, flt


def execute(filters=None):
	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data

def get_data(filters):
	fiscal_year = formatdate(filters.get("date"), "YYYY")
	month = formatdate(filters.get("date"), "MM")

	data = []
	rental_map = frappe._dict()
	os_lists = get_os_lists(filters, fiscal_year, month)
	# frappe.throw("<pre>{}</pre>".format(frappe.as_json(os_lists)))
	for osl in os_lists:
		if filters.get("based_on") == "Dzongkhag":
			rental_map.setdefault(osl.get("dzongkhag"), []).append(osl)
		else:
			rental_map.setdefault(osl.get("tenant"), []).append(osl)

	for key, value in rental_map.items():
		if filters.get("based_on") == "Dzongkhag":
			filter_data = frappe._dict({
					"dzongkhag": key,
					"employee_name": frappe.db.get_value("Employee", key, "employee_name"),
				})
		else:
			filter_data = frappe._dict({
					"tenant": key,
					"tenant_name": frappe.db.get_value("Tenant Information", key, "tenant_name"),
				})

		filter_data.update({
			"one_month_os": 0.0,
			"two_to_three_month_os": 0.0,
			"more_than_three_month_os": 0.0,
			"above_one_year_os": 0.0,
			"balance_os": 0.0
		})

		for d in value:
			count_days = date_diff(nowdate(), getdate(d.posting_date)) + 1
			if count_days >= 0 and count_days <= 30:
				filter_data['one_month_os'] = flt(filter_data['one_month_os'] + d.outstanding_amount, 2)
			elif count_days >= 31 and count_days <= 90:
				filter_data['two_to_three_month_os'] = flt(filter_data['two_to_three_month_os'] + d.outstanding_amount, 2)
			elif count_days >= 91 and count_days <= 365:
				filter_data['more_than_three_month_os'] = flt(filter_data['more_than_three_month_os'] + d.outstanding_amount, 2)
			else: #more the 1 year
				filter_data['above_one_year_os'] = flt(filter_data['above_one_year_os'] + d.outstanding_amount, 2)
				
			filter_data['balance_os'] = flt(filter_data['balance_os'] + d.outstanding_amount, 2)
		data.append(filter_data)

	return data

def get_os_lists(filters, fiscal_year, month):
	cond = ''
	if filters.get('based_on') == 'Tenant' and filters.get('dzongkhag'):
		cond += " and dzongkhag='{}'".format(str(filters.get('dzongkhag')))
	if filters.get('department'):
		cond += " and tenant_department='{}'".format(filters.get("department"))

	result = frappe.db.sql("""select * from `tabRental Bill` 
		where docstatus=1 and gl_entry=1 and outstanding_amount > 0 and fiscal_year <= '{fiscal_year}' and month <= '{month}' {cond} order by tenant, posting_date""".format(fiscal_year=fiscal_year, month=month, cond=cond), as_dict=1)
	return result

def get_columns(filters):
	if filters.get("based_on") == "Dzongkhag":
		columns = [
			{
				"fieldname": "dzongkhag",
				"label": "Dzongkhag",
				"fieldtype": "Link",
				"options": "Dzongkhag",
				"width": 100
			},
		]
	else:
		columns = [
			{
				"fieldname": "tenant",
				"label": "Tenant",
				"fieldtype": "Link",
				"options": "Tenant Information",
				"width": 100
			},
			{
				"fieldname": "tenant_name",
				"label": "Tenant Name",
				"fieldtype": "Data",
				"width": 150
			},
		]
	
	columns.extend(
		[	
			{
				"fieldname": "one_month_os",
				"label": "0 to 30 Days",
				"fieldtype": "Currency",
				"width": 120
			},
			{
				"fieldname": "two_to_three_month_os",
				"label": "31 to 90 Days",
				"fieldtype": "Currency",
				"width": 120
			},
			{
				"fieldname": "more_than_three_month_os",
				"label": "91 to 365 Days",
				"fieldtype": "Currency",
				"width": 120
			},
			{
				"fieldname": "above_one_year_os",
				"label": "Above 1 Year",
				"fieldtype": "Currency",
				"width": 120
			},
			{
				"fieldname": "balance_os",
				"label": "Balance",
				"fieldtype": "Currency",
				"width": 120
			},
		]
	)

	return columns

