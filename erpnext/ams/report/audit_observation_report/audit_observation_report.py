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
			"fieldname": "iain_no",
			"label": "IAIN No.",
			"fieldtype": "Link",
			"options": "Audit Observation",
			"width": 150
		},
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
			"label": "Observation No.",
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
		# {
		# 	"fieldname": "direct_accountability_employee_name",
		# 	"label": "Direct Accountability Employee",
		# 	"fieldtype": "Data",
		# 	"width": 150
		# }
	]
	return columns

def get_data(filters=None):
	data = []
	conditions = get_conditions(filters)
	noi_condition = get_noicondition(filters) if get_noicondition(filters) else ''

	query1 = """
		select 
			ea.branch as auditee_branch, dai.supervisor_name as supervisor, dai.employee as direct_accountability_employee, ea.posting_date, ea.type as audit_type, 
			eati.employee_name as auditor, dai.checklist as audit_checklist, dai.observation_title as observation_title	, 
			eaci.nature_of_irregularity, dai.status, ea.name
		from 
			`tabAudit Observation` ea 
			left join `tabExecute Audit Team Item I` eati on ea.name=eati.parent
			left join `tabExecute Audit Checklist Item I` eaci on ea.name=eaci.parent
			left join `tabDirect Accountability Item I` dai on dai.parent = ea.name
			where 
			ea.docstatus=1 and ea.status != 'Closed' {cond1} {cond2}
		 ORDER BY 
        ea.name
	""".format(cond1=conditions, cond2=noi_condition)
	
	data1 = frappe.db.sql(query1, as_dict=True)
	# query2 = """
	# 	select 
	# 		dai.observation_title, dai.employee as direct_accountability_employee
	# 	from 
	# 		`tabAudit Observation` ea 
	# 	where 
	# 		dai.parent = ea.name and ea.docstatus=1 and ea.status != 'Closed' {cond}
	# 	order by dai.checklist
	# """.format(cond=conditions)
	
	# data2 = frappe.db.sql(query2, as_dict=True)

	for d in data1:
		emp = ""
		# for dd in data2:
			# if d.observation_title == dd.observation_title and d.nature_of_irregularity not in ('For Information','Found in order','Resolved'):
			# 	emp = dd.direct_accountability_employee

		row = {
			"iain_no": d.name,
			"auditee_branch": d.auditee_branch,
			"supervisor": d.supervisor,
			"posting_date": d.posting_date,
			"audit_type": d.audit_type,
			"auditor": d.auditor,
			"audit_checklist": d.audit_checklist,
			"observation_title": d.observation_title,
			"nature_of_irregularity": d.nature_of_irregularity,
			"status": d.status,
			"direct_accountability_employee": d.direct_accountability_employee,
			# "direct_accountability_employee": emp if emp else '',
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

	if filters.get("iain_no"):
		conditions += " and ea.name = '{}'".format(filters.get("iain_no"))

	if filters.get("audit_type"):
		conditions += " and ea.type = '{}'".format(filters.get("audit_type"))
	
	return conditions

def get_noicondition(filters=None):
	noi_condition = ""
	if filters.get("observation_type"):
		noi_condition += " and eaci.nature_of_irregularity = '{}'".format(filters.get("observation_type"))
	return noi_condition
