# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from frappe.utils import flt
import frappe
def execute(filters=None):
	columns, data = [], []
	columns = get_columns(data)
	queries = construct_query(filters)
	data = get_data(queries,filters)
	
	return columns, data

def get_columns(data):
	return [
		{
			"fieldname": "rp_id",
			"label": "Rental Payment ID",
			"fieldtype": "Link",
			"options": "Rental Payment",
			"width": 200
		},
		{
			"fieldname": "branch",
			"label": "Branch",
			"fieldtype": "Link",
			"options": "Branch",
			"width": 200
		},
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
			"fieldname": "posting_date",
			"label": "Posting Date",
			"fieldtype": "Date",
			"width": 120
		},
		{
			"fieldname": "month",
			"label": "Month",
			"fieldtype": "Data",
			"width": 70
		},
		{
			"fieldname": "payment_mode",
			"label": "Payment Mode",
			"fieldtype": "Data",
			"width":120
		},
		{
			"fieldname": "tds_amount",
			"label": "TDS Amount",
			"fieldtype": "Data",
			"width":120
		},
		{
			"fieldname": "penalty_amount",
			"label": "Penalty Amount",
			"fieldtype": "Data",
			"width":130
		},
		{
			"fieldname": "pre_rent_amount",
			"label": "Pre-Rent Amount",
			"fieldtype": "Data",
			"width":150
		},
		{
			"fieldname": "excess_amount",
			"label": "Excess Amount",
			"fieldtype": "Data",
			"width":120
		},
		{
			"fieldname": "total_bill_amount",
			"label": "Total Bill Amount",
			"fieldtype": "Data",
			"width":150
		},
		{
			"fieldname": "total_amount_received",
			"label": "Total Amount Received",
			"fieldtype": "Data",
			"width":180
		},
		{
			"fieldname": "outstanding_amount",
			"label": "Outstanding Amount",
			"fieldtype": "Data",
			"width":160
		},
		
	]

def construct_query(filters=None):
	conditions, filters = get_conditions(filters)
	query = ("""
			select 
				r.name as name, r.branch as branch, r.posting_date as posting_date, r.payment_mode as payment_mode
			from `tabRental Payment` r
			where r.docstatus = 1
			{}
			""".format(conditions))
	
	return query	
def get_data(query, filters):
	cond = ""
	if filters.get("month"):
		cond += """and ri.month ='{}'""".format(filters.get("month"))
	data = []
	datas = frappe.db.sql(query, as_dict=True)
	for d in datas:
		rental_item = frappe.db.sql("""
			select 
				ri.tenant as tenant,ri.tenant_name as tenant_name, ri.month as month, ri.tds_amount as tds_amount, ri.penalty as penalty, ri.pre_rent_amount as pre_rent_amount, ri.excess_amount as excess_amount, ri.bill_amount as bill_amount, ri.total_amount_received as total_amount_received, ri.balance_rent as balance_rent
			from `tabRental Payment Item` ri 
			where ri.parent = '{0}'
			{1}
			""".format(d.name, cond), as_dict=True)
		for raw in rental_item:
			row = {
				"rp_id":d.name,
				"branch":d.branch,
				"tenant":raw.tenant,
				"tenant_name": raw.tenant_name,
				"posting_date": d.posting_date,
				"month": raw.month,
				"payment_mode": d.payment_mode,
				"tds_amount": raw.tds_amount,
				"penalty_amount":raw.penalty,
				"pre_rent_amount": raw.pre_rent_amount,
				"excess_amount":raw.excess_amount,
				"total_bill_amount":raw.bill_amount,
				"total_amount_received": raw.total_amount_received,
				"outstanding_amount":raw.balance_rent
			}
			data.append(row)
	return data
def get_conditions(filters):
	conditions = ""
	if filters.get("branch"):
		conditions += """and r.branch ='{}'""".format(filters.get("branch"))
	if filters.get("fiscal_year"):
		conditions += """and r.fiscal_year ='{}'""".format(filters.get("fiscal_year"))
	if filters.get("from_date") and filters.get("to_date"):
		conditions += """and r.posting_date between '{from_date}' and '{to_date}'""".format(from_date=filters.get("from_date"),to_date=filters.get("to_date"))
	return conditions, filters

