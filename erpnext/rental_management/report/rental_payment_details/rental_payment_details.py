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
			"width": 100
		},
		{
			"fieldname": "branch",
			"label": "Branch",
			"fieldtype": "Link",
			"options": "Branch",
			"width": 150
		},
		{
			"fieldname": "tenant",
			"label": "Tenant",
			"fieldtype": "Link",
			"options": "Tenant Information",
			"width": 120
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
			"width": 70
		},
		{
			"fieldname": "payment_mode",
			"label": "Payment Mode",
			"fieldtype": "Data",
			"width":70
		},
		{
			"fieldname": "tds_amount",
			"label": "TDS Amount",
			"fieldtype": "Data",
			"width":70
		},
		{
			"fieldname": "penalty_amount",
			"label": "Penalty Amount",
			"fieldtype": "Data",
			"width":70
		},
		{
			"fieldname": "pre_rent_amount",
			"label": "Pre-Rent Amount",
			"fieldtype": "Data",
			"width":70
		},
		{
			"fieldname": "excess_amount",
			"label": "Excess Amount",
			"fieldtype": "Data",
			"width":70
		},
		{
			"fieldname": "total_bill_amount",
			"label": "Total Bill Amount",
			"fieldtype": "Data",
			"width":100
		},
		{
			"fieldname": "total_amount_received",
			"label": "Total Amount Received",
			"fieldtype": "Data",
			"width":70
		},
		{
			"fieldname": "outstanding_amount",
			"label": "Outstanding Amount",
			"fieldtype": "Data",
			"width":70
		},
		
	]

def construct_query(filters=None):
	conditions, filters = get_conditions(filters)
	query = ("""
			select 
				r.name as name, r.branch as branch, r.tenant as tenant,r.tenant_name as tenant_name, r.posting_date as posting_date, r.payment_mode as payment_mode, r.tds_amount as tds_amount, r.penalty_amount as penalty_amount, r.pre_rent_amount as pre_rent_amount, r.excess_amount as excess_amount, r.total_bill_amount as total_bill_amount, r.total_amount_received as total_amount_received
			from `tabRental Payment` r
			where r.docstatus = 1
			{}
			""".format(conditions))
	return query	
def get_data(query, filters):
	conditions = ""
	data = []
	datas = frappe.db.sql(query, as_dict=True)
	for d in datas:
		outstanding = flt(d.total_amount_received)-flt(d.total_bill_amount)
		row = {
			"rp_id":d.name,
			"branch":d.branch,
			"tenant":d.tenant,
			"tenant_name": d.tenant_name,
			"posting_date": d.posting_date,
			"payment_mode": d.payment_mode,
			"tds_amount": d.tds_amount,
			"penalty_amount":d.penalty_amount,
			"pre_rent_amount": d.pre_rent_amount,
			"excess_amount":d.excess_amount,
			"total_bill_amount":d.total_bill_amount,
			"total_amount_received": d.total_amount_received,
			"outstanding_amount":outstanding
		}
		data.append(row)
	return data
def get_conditions(filters):
	conditions = ""
	if filters.get("branch"):
		conditions += """and r.branch ='{}'""".format(filters.get("branch"))

	return conditions, filters

