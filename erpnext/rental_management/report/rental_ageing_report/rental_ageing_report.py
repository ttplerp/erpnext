# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import date_diff, getdate, flt, cint

def execute(filters=None):
	columns, data = [], []
	columns = get_columns(data)
	queries = construct_query(filters)
	data = get_data(queries,filters)

	return columns, data

def get_columns(data):
	return [
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
		{
			"fieldname": "rental_bill_id",
			"label": "Rental Bill",
			"fieldtype": "Link",
			"options": "Rental bill",
			"width": 150
		},
		{
			"fieldname": "zero",
			"label": "0 to 30 Days",
			"fieldtype": "Currency",
			"width":150
		},
		{
			"fieldname": "one",
			"label": "31 to 90 Days",
			"fieldtype": "Currency",
			"width":150
		},
		{
			"fieldname": "two",
			"label": "91 to 365 Days",
			"fieldtype": "Currency",
			"width":150
		},
		{
			"fieldname": "above_one",
			"label": "Above 1 Year",
			"fieldtype": "Currency",
			"width":150
		},
		{
			"fieldname": "balance",
			"label": "Balance",
			"fieldtype": "Currency",
			"width":100
		},
		{
			"fieldname": "status",
			"label": "Current Status",
			"fieldtype": "Data",
			"width":150
		},
	]
def construct_query(filters=None):
	conditions, filters = get_conditions(filters)
	query = ("""select name, posting_date, outstanding_amount, tenant, tenant_name
			from `tabRental Bill`
			where docstatus = 1
			and posting_date between '{0}' and '{1}'
			{2}
		""".format(filters.get("from_date"),filters.get("to_date"),conditions))
	return query	

def get_data(query, filters):
	data = []
	datas = frappe.db.sql(query, as_dict=True)
	# frappe.msgprint(str(datas))
	for d in datas:
		# frappe.throw(str(datas))
		if d.outstanding_amount <= 0:
			bill = frappe.db.sql("""select p.payment_date, p.received_amount from 
									`tabRental Bill` r
									inner join `tabRental Payment Details`p
									on p.parent=r.name
									where r.name='{}'
								""".format(d.name), as_dict=True)
			for x in bill:
				if str(x.payment_date) > str(filters.get("to_date")):
					zero = one = two = above_one = balance = 0
					count_days = date_diff(getdate(filters.get("to_date")), getdate(d.posting_date))
					if cint(count_days) >= 0 and cint(count_days) <= 30:
						zero = balance =x.received_amount
					elif cint(count_days) >= 31 and cint(count_days) <= 90:
						one = balance =x.received_amount
					elif cint(count_days) >= 91 and cint(count_days) <= 365:
						two = balance =x.received_amount
					elif cint(count_days) > 365: #more the 1 year
						above_one = balance =x.received_amount
					row = {
						"tenant": d.tenant,
						"tenant_name": d.tenant_name,
						"rental_bill_id": d.name,
						"zero": zero,
						"one": one,
						"two":two,
						"above_one":above_one,
						"balance":balance,
						"status": "Paid"
					}
					data.append(row)
		else:
			zero = one = two = above_one = balance = 0
			count_days = date_diff(getdate(filters.get("to_date")), getdate(d.posting_date))
			if cint(count_days) >= 0 and cint(count_days) <= 30:
				zero = balance =d.outstanding_amount
			elif cint(count_days) >= 31 and cint(count_days) <= 90:
				one = balance =d.outstanding_amount
			elif cint(count_days) >= 91 and cint(count_days) <= 365:
				two = balance =d.outstanding_amount
			elif cint(count_days) > 365: #more the 1 year
				above_one = balance =d.outstanding_amount
			row = {
				"tenant": d.tenant,
				"tenant_name": d.tenant_name,
				"rental_bill_id":d.name,
				"zero": zero,
				"one": one,
				"two":two,
				"above_one":above_one,
				"balance":balance,
				"status": "Unpaid"
			}
			data.append(row)
	return data
def get_conditions(filters):
	conditions = ""
	if filters.get("branch"):
		conditions += """and branch ='{}'""".format(filters.get("branch"))
	if filters.get("ministry_and_agency"):
		conditions += """and ministry_agency ='{}'""".format(filters.get("ministry_and_agency"))
	if filters.get("tenant"):
		conditions += """and tenant ='{}'""".format(filters.get("tenant"))
	return conditions, filters


