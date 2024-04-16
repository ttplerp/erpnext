# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from frappe.utils import flt
import frappe
from datetime import datetime
from calendar import monthrange
from frappe.utils import cint
def execute(filters=None):
	columns, data = [], []
	columns = get_columns(data)
	queries = construct_query(filters)
	data = get_data(queries,filters)
	
	return columns, data

def get_columns(data):
	return [
		{
			"fieldname": "payment_id",
			"label": "Payment ID",
			"fieldtype": "Link",
			"options": "Rental Payment",
			"width": 150
		},
		{
			"fieldname": "tenant_id",
			"label": "Tenant ID",
			"fieldtype": "Link",
			"options": "Tenant Information",
			"width": 150
		},
		{
			"fieldname": "tenant_cid",
			"label": "Tenant CID",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "tenant_name",
			"label": "Tenant Name",
			"fieldtype": "Data",
			"width": 150
		},
		
		{
			"fieldname": "allotment_date",
			"label": "Allottment Date",
			"fieldtype": "Date",
			"width":150
		},
		{
			"fieldname": "sd_amount",
			"label": "SD Amount",
			"fieldtype": "Data",
			"width":100
		},
		{
			"fieldname": "dzongkhag",
			"label": "Dzongkhag",
			"fieldtype": "Data",
			"width":100
		},
		{
			"fieldname": "received_date",
			"label": "Received Date",
			"fieldtype": "Date",
			"width":150
		},
	]

def construct_query(filters=None):
	conditions, filters = get_conditions(filters)
	query = ("""
			select 
				name, tenant, tenant_name, security_deposit_amount, posting_date, dzongkhag
			from `tabRental Payment`
			where docstatus = 1
		  	and security_deposit_amount > 0
			{}
			""".format(conditions))
	return query	
def get_data(query, filters):
	data = []
	datas = frappe.db.sql(query, as_dict=True)
	for d in datas:
		allotment_date = frappe.db.get_value("Tenant Information",d.tenant,"allocated_date")
		cid = frappe.db.get_value("Tenant Information",d.tenant,"tenant_cid")
		if d.dzongkhag:
			dzongkhag=d.dzongkhag
		else:
			dzongkhag = frappe.db.get_value("Tenant Information",d.tenant,"dzongkhag")
		if d.security_deposit_amount > 0:
			row = {
				"payment_id":d.name,
				"tenant_id":d.tenant,
				"tenant_cid":cid,
				"tenant_name": d.tenant_name,
				"allotment_date":allotment_date,
				"sd_amount":d.security_deposit_amount,
				"dzongkhag":dzongkhag,
				"received_date":d.posting_date
			}
			data.append(row)
	return data
def get_conditions(filters):
	conditions = ""
	if filters.get("branch"):
		conditions += """and branch ='{}'""".format(filters.get("branch"))
	if filters.get("from_date") and filters.get("to_date"):
		conditions += """and posting_date between '{0}' and '{1}'""".format(filters.get("from_date"),filters.get("to_date"))
	if filters.get("fiscal_year"):
		conditions += """and fiscal_year ='{}'""".format(filters.get("fiscal_year"))
	return conditions, filters
