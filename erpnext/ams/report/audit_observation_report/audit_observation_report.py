# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt, getdate

def execute(filters=None):
	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data

def get_columns(filters=None):
	columns = [
		{
			"fieldname": "auditee_branch",
			"label": "Auditee Branch",
			"fieldtype": "Data",
			"width": 200
		},
		{
			"fieldname": "supervisor",
			"label": "Supervisor",
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "posting_date",
			"label": "Posting Date",
			"fieldtype": "Date",
			"width": 150
		},
		{
			"fieldname": "audit_type",
			"label": "Audit Type",
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "auditor",
			"label": "Auditor",
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "audit_checklist",
			"label": "Audit Checklist",
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "observation_title",
			"label": "Observation Title",
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "nature_of_irregularity",
			"label": "Nature of Irregularity",
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "status",
			"label": "Status",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"fieldname": "direct_accountability_employee",
			"label": "Direct Accountability Employee",
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "execute_audit_id",
			"label": "Execute Audit ID",
			"fieldtype": "Data",
			"width": 150
		}
	]
	return columns

def get_data(filters=None):
	data = []
	conditions = get_conditions(filters)
	noi_condition = get_noicondition(filters) if get_noicondition(filters) else ''

	query1 = """
		select 
			ea.branch as auditee_branch, ea.supervisor_name as supervisor, ea.posting_date, ea.type as audit_type, 
			eati.employee_name as auditor, eaci.audit_area_checklist as audit_checklist, eaci.observation_title as observation_title, 
			eaci.nature_of_irregularity, eaci.status, ea.name as execute_audit_id
		from 
			`tabExecute Audit` ea 
			inner join `tabExecute Audit Team Item` eati on ea.name=eati.parent
			inner join `tabExecute Audit Checklist Item` eaci on ea.name=eaci.parent
		where 
			ea.docstatus=1 and ea.status != 'Closed' {cond1} {cond2}
		group by eaci.observation_title
		order by eaci.audit_area_checklist
	""".format(cond1=conditions, cond2=noi_condition)

	data1 = frappe.db.sql(query1, as_dict=True)

	query2 = """
		select 
			dai.observation_title, dai.employee_name as direct_accountability_employee
		from 
			`tabExecute Audit` ea inner join `tabDirect Accountability Item` dai
		where 
			dai.parent = ea.name and ea.docstatus=1 and ea.status != 'Closed' {cond}
		group by dai.observation_title
		order by dai.checklist
	""".format(cond=conditions)
	
	data2 = frappe.db.sql(query2, as_dict=True)

	for d in data1:
		emp = ""
		for dd in data2:
			if d.observation_title == dd.observation_title and d.nature_of_irregularity not in ('For Information','Found in order','Resolved'):
				emp = dd.direct_accountability_employee

		row = {
			"auditee_branch": d.auditee_branch,
			"supervisor": d.supervisor,
			"posting_date": d.posting_date,
			"audit_type": d.audit_type,
			"auditor": d.auditor,
			"audit_checklist": d.audit_checklist,
			"observation_title": d.observation_title,
			"nature_of_irregularity": d.nature_of_irregularity,
			"status": d.status,
			"direct_accountability_employee": emp if emp else '',
			"execute_audit_id": d.execute_audit_id,
		}

		data.append(row)

	return data
		

def get_conditions(filters=None):
	conditions = ""

	if not filters.get("from_date"):
		frappe.throw(_("'From Date' is required"))
	
	if not filters.get("to_date"):
		frappe.throw(_("'To Date' is required"))

	if filters.get("from_date") and filters.get("to_date"):
		conditions += " and ea.posting_date between '{}' and '{}'".format(filters.get("from_date"),filters.get("to_date"))

	if filters.get("execute_audit"):
		conditions += " and ea.name = '{}'".format(filters.get("execute_audit"))

	if filters.get("audit_type"):
		conditions += " and ea.type = '{}'".format(filters.get("audit_type"))
	
	return conditions

def get_noicondition(filters=None):
	noi_condition = ""
	if filters.get("observation_type"):
		noi_condition += " and eaci.nature_of_irregularity = '{}'".format(filters.get("observation_type"))
	return noi_condition
