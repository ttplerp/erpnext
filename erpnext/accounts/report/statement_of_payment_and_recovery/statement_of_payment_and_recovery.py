# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import flt, cstr
from frappe import msgprint, _

def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data

def get_columns():
	return [
		{
			"fieldname": "project",
			"label": "Project",
			"fieldtype": "Link",
			"options": "Project",
			"width": 140
		},
		{
			"fieldname": "project_name",
			"label": "Project Name",
			"fieldtype": "Data",
			"width": 200
		},
		{
			"fieldname": "branch",
			"label": "Branch",
			"fieldtype": "Link",
			"options": "Branch",
			"width": 160
		},
		{
			"fieldname": "gross_bill",
			"label": "Gross Bill",
			"fieldtype": "Currency",
			"width": 150
		},
		{
			"fieldname": "mobilization_advance",
			"label": "Mobilization Advance",
			"fieldtype": "Currency",
			"width": 150
		},
		{
			"fieldname": "contractor_advance",
			"label": "Labor Contractor Advance",
			"fieldtype": "Currency",
			"width": 150
		},
		{
			"fieldname": "secured_advance",
			"label": "Secured Advance",
			"fieldtype": "Currency",
			"width": 150
		},
		{
			"fieldname": "total_advance",
			"label": "Total Advance",
			"fieldtype": "Currency",
			"width": 150
		},
		{
			"fieldname": "mobilization_recovered",
			"label": "Recovered Mobilization Amount",
			"fieldtype": "Currency",
			"width": 150
		},
		{
			"fieldname": "contractor_recovered",
			"label": "Recovered Contractor Advance",
			"fieldtype": "Currency",
			"width": 150
		},
		{
			"fieldname": "secured_recovered",
			"label": "Recovered Secured Advance",
			"fieldtype": "Currency",
			"width": 150
		},
		{
			"fieldname": "retention_money",
			"label": "10% Security Deposit/Retention Money",
			"fieldtype": "Currency",
			"width": 150
		},
		{
			"fieldname": "tds_amount",
			"label": "2% TDS",
			"fieldtype": "Currency",
			"width": 150
		},
		{
			"fieldname": "other_deductions",
			"label": "Other Deductions",
			"fieldtype": "Currency",
			"width": 150
		},
		{
			"fieldname": "liquidity_damage",
			"label": "Liquidity Damage",
			"fieldtype": "Currency",
			"width": 150
		},
		{
			"fieldname": "total_recovered",
			"label": "Total Recovered Amount",
			"fieldtype": "Currency",
			"width": 150
		},
		{
			"fieldname": "balance_mobilization",
			"label": "Mobilization Balance",
			"fieldtype": "Currency",
			"width": 150
		},
		{
			"fieldname": "balance_contractor",
			"label": "Labor Contractor Balance",
			"fieldtype": "Currency",
			"width": 150
		},
		{
			"fieldname": "balance_secured",
			"label": "Secured Balance",
			"fieldtype": "Currency",
			"width": 150
		},
		{
			"fieldname": "total_balance",
			"label": "Balance Amount",
			"fieldtype": "Currency",
			"width": 150
		},
		{
			"fieldname": "net_payment",
			"label": "Net Payment",
			"fieldtype": "Currency",
			"width": 150
		}
	]

def get_data(filters):
	cond = get_conditions(filters)
	data = []
	project_list = frappe.db.sql("""
			SELECT name, project_name, branch, boq_value from `tabProject` where is_active = 'Yes' {}
			""".format(cond), as_dict = True)
	
	for d in project_list:
		mobilization_advance = frappe.db.sql("select IFNULL(SUM(paid_amount),0) from `tabProject Advance` where docstatus = 1 and advance_type = 'Mobilisation Advance' and project = %s and advance_date BETWEEN %s and %s", (d.name, filters.from_date, filters.to_date))[0][0]
		contractor_advance = frappe.db.sql("select IFNULL(SUM(paid_amount),0) from `tabProject Advance` where docstatus = 1 and advance_type = 'Advance to Contractor' and project = %s and advance_date BETWEEN %s and %s", (d.name, filters.from_date, filters.to_date))[0][0]
		secured_advance = frappe.db.sql("select IFNULL(SUM(paid_amount),0) from `tabProject Advance` where docstatus = 1 and advance_type = 'Secured Advance' and project = %s and advance_date BETWEEN %s and %s", (d.name, filters.from_date, filters.to_date))[0][0]
		mobilization_recovered = frappe.db.sql("select IFNULL(SUM(pia.allocated_amount),0) from `tabProject Invoice Advance` pia, `tabProject Invoice` pi where pia.parent = pi.name and pi.docstatus = 1 and pia.advance_account = 'Mobilisation Advance - NHDCL' and pi.project = %s and pi.invoice_date BETWEEN %s and %s", (d.name, filters.from_date, filters.to_date))[0][0]
		contractor_recovered = frappe.db.sql("select IFNULL(SUM(pia.allocated_amount),0) from `tabProject Invoice Advance` pia, `tabProject Invoice` pi where pia.parent = pi.name and pi.docstatus = 1 and pia.advance_account = 'Advance to Contractor - NHDCL' and pi.project = %s and pi.invoice_date BETWEEN %s and %s", (d.name, filters.from_date, filters.to_date))[0][0]
		secured_recovered = frappe.db.sql("select IFNULL(SUM(pia.allocated_amount),0) from `tabProject Invoice Advance` pia, `tabProject Invoice` pi where pia.parent = pi.name and pi.docstatus = 1 and pia.advance_account = 'Secured Advance - NHDCL' and pi.project = %s and pi.invoice_date BETWEEN %s and %s", (d.name, filters.from_date, filters.to_date))[0][0]
		retention_money = frappe.db.sql("select IFNULL(SUM(pid.amount),0) from `tabProject Invoice Deduction` pid, `tabProject Invoice` pi where pid.parent = pi.name and pi.docstatus = 1 and pid.account = '10%% Retention Money Payable - NHDCL' and pi.project = %s and pi.invoice_date BETWEEN %s and %s", (d.name, filters.from_date, filters.to_date))[0][0]
		liquidity_damage = frappe.db.sql("select IFNULL(SUM(pid.amount),0) from `tabProject Invoice Deduction` pid, `tabProject Invoice` pi where pid.parent = pi.name and pi.docstatus = 1 and pid.account = 'Liquidity Damage (LD) - NHDCL' and pi.project = %s and pi.invoice_date BETWEEN %s and %s", (d.name, filters.from_date, filters.to_date))[0][0]
		tds_amount = frappe.db.sql("select IFNULL(SUM(tds_amount),0) from `tabProject Invoice` where docstatus = 1 and project = %s and invoice_date BETWEEN %s and %s", (d.name, filters.from_date, filters.to_date))[0][0]
		other_deductions = frappe.db.sql("select IFNULL(SUM(pid.amount),0) from `tabProject Invoice Deduction` pid, `tabProject Invoice` pi where pid.parent = pi.name and pi.docstatus = 1 and pid.account not in ('10%% Retention Money Payable - NHDCL', 'Liquidity Damage (LD) - NHDCL') and pi.project = %s and pi.invoice_date BETWEEN %s and %s", (d.name, filters.from_date, filters.to_date))[0][0]

		row = {
			"project": d.name,
			"project_name": d.project_name,
			"branch": d.branch,
			"gross_bill": d.boq_value,
			"mobilization_advance": mobilization_advance,
			"contractor_advance": contractor_advance,
			"secured_advance": secured_advance,
			"total_advance": flt(mobilization_advance)+flt(contractor_advance)+flt(secured_advance),
			"mobilization_recovered": mobilization_recovered,
			"contractor_recovered": contractor_recovered,
			"secured_recovered": secured_recovered,
			"retention_money": retention_money,
			"tds_amount": tds_amount,
			"liquidity_damage": liquidity_damage,
			"other_deductions": other_deductions,
			"total_recovered": flt(mobilization_recovered)+flt(contractor_recovered)+flt(secured_recovered)+flt(retention_money)+flt(tds_amount)+flt(liquidity_damage)+flt(other_deductions),
			"balance_mobilization": flt(mobilization_advance) - flt(mobilization_recovered),
			"balance_contractor": flt(contractor_advance) - flt(contractor_recovered),
			"balance_secured": flt(secured_advance) - flt(secured_recovered),
			"total_balance": (flt(mobilization_advance) - flt(mobilization_recovered)) + (flt(contractor_advance) - flt(contractor_recovered)) + (flt(secured_advance) - flt(secured_recovered)),
			"net_payment": flt(d.boq_value) - flt(flt(mobilization_recovered)+flt(contractor_recovered)+flt(secured_recovered)+flt(retention_money)+flt(tds_amount)+flt(liquidity_damage)+flt(other_deductions)),
			}

		data.append(row)

	return data

def get_conditions(filters):
	conditions = ""
	if filters.get("project"):
		conditions += " and name = \'" + str(filters.project) + "\'"

	if filters.get("branch"):
		conditions += " and branch = \'" + str(filters.branch) + "\'"
	
	return conditions

