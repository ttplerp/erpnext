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
			"fieldname": "branch",
			"label": "Branch",
			"fieldtype": "Link",
			"options": "Branch",
			"width": 120
		},
				{
			"fieldname": "cost_center",
			"label": "Cost Center",
			"fieldtype": "Link",
			"options": "Cost Center",
			"width": 120
		},
		{
			"fieldname": "posting_date",
			"label": "Posting Date",
			"fieldtype": "Date",
			"width": 100
		},
		{
			"fieldname": "equipment",
			"label": "Equipment",
			"fieldtype": "Link",
			"options": "Equipment",
			"width": 120
		},
		{
			"fieldname": "equipment_type",
			"label": "Equipment Type",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"fieldname": "ehf_name",
			"label": "EHF Reference",
			"fieldtype": "Link",
			"options": "Equipment Hiring Form",
			"width": 120
		},
		{
			"fieldname": "party_type",
			"label": "Party Type",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"fieldname": "party",
			"label": "Party",
			"fieldtype": "Dynamic Link",
			"options": "party_type",
			"width": 150
		},
		{
			"fieldname": "rate_type",
			"label": "Rate Type",
			"fieldtype": "Data",
			"width": 100
		},
		# {
		# 	"fieldname": "rate",
		# 	"label": "Rate",
		# 	"fieldtype": "Currency",
		# 	"width": 100
		# },
		{
			"fieldname": "total_hours",
			"label": "Total Hours",
			"fieldtype": "Float",
			"width": 100
		},
		{
			"fieldname": "deduction_amount",
			"label": "Deduction Amount",
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"fieldname": "payable_amount",
			"label": "Amount",
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"fieldname": "grand_total",
			"label": "Grand Total",
			"fieldtype": "Currency",
			"width": 120
		},
		# {
		# 	"fieldname": "idle_hours",
		# 	"label": "Idle Hours",
		# 	"fieldtype": "Float",
		# 	"width": 80
		# },
		# {
		# 	"fieldname": "idle_rate",
		# 	"label": "Idle Rate",
		# 	"fieldtype": "Float",
		# 	"width": 80
		# },
		# {
		# 	"fieldname": "idle_amount",
		# 	"label": "Idle Amount",
		# 	"fieldtype": "Currency",
		# 	"width": 100
		# },
		{
			"fieldname": "own",
			"label": "Is Own Company",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"fieldname": "hci_reference",
			"label": "HCI Reference",
			"fieldtype": "Link",
			"options": "Hire Charge Invoice",
			"width": 120
		},
	]

def get_data(filters):
	cond = get_conditions(filters)
	data = []
	query = """
			SELECT hci.branch, hci.cost_center, hci.posting_date, eii.equipment, eii.equipment_type, eii.equipment_hiring_form, hci.party, hci.party_type,
				(select er.rate_type from `tabEHF Rate` er where er.parent = eii.equipment_hiring_form limit 1) as rate_type,
				eii.rate, hci.total_hours, hci.payable_amount, e.hired_equipment, hci.name, hci.total_deduction, hci.grand_total,
				(select er.idle_rate from `tabEHF Rate` er where er.parent = eii.equipment_hiring_form limit 1) as idle_rate
			FROM `tabHire Charge Invoice` AS hci, `tabEME Invoice Item` AS eii, `tabEquipment` AS e, 
			`tabLogbook` AS lb, `tabEquipment History` AS eh
			WHERE eii.parent = hci.name AND eii.logbook = lb.name and eii.equipment = e.name and 
			e.name = eh.parent and eh.branch = hci.branch and hci.docstatus = 1	{}
			GROUP BY eii.equipment, eii.equipment_hiring_form 
			""".format(cond)
	
	try:
		datas = frappe.db.sql(query, as_dict=True)


		for d in datas:
			row = {
				"branch": d.branch,
				"cost_center": d.cost_center,
				"posting_date": d.posting_date,
				"equipment": d.equipment,
				"equipment_type": d.equipment_type,
				"ehf_name": d.equipment_hiring_form,
				"party_type": d.party_type,
				"party": d.party,
				"rate_type": d.rate_type,
				# "rate": d.rate,
				"total_hours": d.total_hours,
				"payable_amount": d.payable_amount,
				"deduction_amount": d.total_deduction,
				"grand_total": d.grand_total,
				# "idle_hours": d.total_idle_hour,
				# "idle_rate": d.idle_rate,
				# "idle_amount": flt(d.idle_hour)*flt(d.idle_rate),
				"own": "Yes" if d.hired_equipment == 0 else "No",
				"hci_reference": d.name,
				}

			data.append(row)

	except Exception as e:
		frappe.log_error(_("Error in getting data: {0}").format(str(e)))

	return data

def get_conditions(filters):
	conditions = ""
	if filters.get("branch"):
		conditions += " and hci.branch = \'" + str(filters.branch) + "\'"

	if filters.get("from_date") and filters.get("to_date"):
		conditions += """ and (('{0}' between eh.from_date and ifnull(eh.to_date, now())) or
		('{1}' between eh.from_date and ifnull(eh.to_date, now())))""".format(filters.get("from_date"), filters.get("to_date"))
	
	if filters.get("not_nhdcl"):
		conditions += " and e.hired_equipment = 0"

	if filters.get("include_disabled"):
		conditions += " "
	else:
		conditions += " and e.enabled = 1"

	if filters.get("party"):
		conditions += " and hci.party = \'" + str(filters.party) + "\'"
	
	return conditions

