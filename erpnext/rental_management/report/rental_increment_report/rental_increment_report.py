# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
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
			"fieldname": "branch",
			"label": "Branch",
			"fieldtype": "Link",
			"options": "Branch",
			"width": 200
		},
		{
			"fieldname": "tenant_id",
			"label": "Tenant ID",
			"fieldtype": "Link",
			"options": "Tenant Information",
			"width": 200
		},
		{
			"fieldname": "tenant_name",
			"label": "Tenant Name",
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "ministry_and_agency",
			"label": "Ministry and Agency",
			"fieldtype": "Link",
			"options": "Ministry and Agency",
			"width": 200
		},
		{
			"fieldname": "department",
			"label": "Tenant Department",
			"fieldtype": "Data",
			"width":200
		},
		{
			"fieldname": "from_date",
			"label": "From Date",
			"fieldtype": "Date",
			"width":250
		},
		{
			"fieldname": "to_date",
			"label": "To Date",
			"fieldtype": "Date",
			"width":250
		},
		{
			"fieldname": "increment",
			"label": "Increment Amount",
			"fieldtype": "Data",
			"width":100
		},
		{
			"fieldname": "rental_amount",
			"label": "Rental Amount",
			"fieldtype": "Data",
			"width":120
		},
		{
			"fieldname": "pmc",
			"label": "PMC Amount",
			"fieldtype": "Data",
			"width":100
		},
		{
			"fieldname": "total_amount",
			"label": "Total Rental Amount",
			"fieldtype": "Data",
			"width":180
		},
	]

def construct_query(filters=None):
	conditions, filters = get_conditions(filters)
	query = ("""
			select 
				t.name as name, t.branch as branch,t.tenant_name as tenant_name, t.tenant_department_name as tenant_department_name, t.ministry_and_agency as ministry_and_agency, t.allocated_date as allocated_date, t.flat_no as flat_no
			from `tabTenant Information` t
			where t.docstatus = 1
		  	and t.status !='Surrendered'
			{}
			""".format(conditions))
	return query	
def get_data(query, filters):
	data = []
	datas = frappe.db.sql(query, as_dict=True)
	for d in datas:
		date = datetime.strptime(str(d.allocated_date), "%Y-%m-%d")
		_,last_day_of_month = monthrange(date.year, date.month)
		start_date =date.replace(day=1)
		end_date =date.replace(day=last_day_of_month)

		if str(date.month)== str(filters.get("month")):
			increment_start_date =start_date.replace(year=cint(filters.get("fiscal_year")))
			increment_end_date =end_date.replace(year=cint(filters.get("fiscal_year")))
			item = frappe.db.sql("""
				select
					ti.from_date as from_date, ti.to_date as to_date, ti.increment as increment, ti.rental_amount as rental_amount
				from `tabTenant Rental Charges` ti
				where ti.parent='{0}'
				and ti.from_date between '{1}' and '{2}'
				""".format(d.name, increment_start_date, increment_end_date),as_dict=True)
			for r in item:
				pmc = frappe.db.get_value("Flat No",d.flat_no,"total_property_management_amount")
				total = flt(pmc)+ flt(r.rental_amount)
				row = {
					"branch":d.branch,
					"tenant_id":d.name,
					"tenant_name": d.tenant_name,
					"ministry_and_agency": d.ministry_and_agency,
					"department": d.tenant_department_name,
					"from_date":r.from_date,
					"to_date":r.to_date,
					"increment":r.increment,
					"rental_amount":r.rental_amount,
					"pmc":pmc,
					"total_amount":total
				}
				data.append(row)
	return data
def get_conditions(filters):
	conditions = ""
	if filters.get("branch"):
		conditions += """and t.branch ='{}'""".format(filters.get("branch"))
	if filters.get("ministry_and_agency"):
		conditions += """and t.ministry_and_agency ='{}'""".format(filters.get("ministry_and_agency"))
	if filters.get("department"):
		conditions += """and t.tenant_department ='{}'""".format(filters.get("department"))
	return conditions, filters

