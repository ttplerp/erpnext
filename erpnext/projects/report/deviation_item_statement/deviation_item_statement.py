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
	columns = [{
		"fieldname": "boq",
		"label": "BOQ",
		"fieldtype": "Link",
		"options": "BOQ",
		"width": 150
	}]

	columns.append({
		"fieldname": "boq_code",
		"label": "BSR Code",
		"fieldtype": "Link",
		"options": "Item",
		"width": 100
	})
	columns.append({
		"fieldname": "party_boq_code",
		"label": "BOQ Code",
		"fieldtype": "Data",
		"width": 100
	})
	columns.append({
		"fieldname": "description",
		"label": "Description",
		"fieldtype": "Data",
		"width": 200
	})
	columns.append({
		"fieldname": "boq_qty",
		"label": "BOQ Quantity",
		"fieldtype": "Float",
		"width": 120
	})
	columns.append({
		"fieldname": "executed_qty",
		"label": "Execute",
		"fieldtype": "Float",
		"width": 120
	})
	columns.append({
		"fieldname": "qty_within",
		"label": "Within 20% DL",
		"fieldtype": "Float",
		"width": 120
	})
	columns.append({
		"fieldname": "qty_beyond",
		"label": "Beyond 20% DL",
		"fieldtype": "Float",
		"width": 140
	})
	columns.append({
		"fieldname": "boq_rate",
		"label": "BOQ Rate",
		"fieldtype": "Currency",
		"width": 120
	})
	columns.append({
		"fieldname": "rate_within",
		"label": "Within 20% DL",
		"fieldtype": "Float",
		"width": 120
	})
	columns.append({
		"fieldname": "rate_beyond",
		"label": "Beyond 20% DL",
		"fieldtype": "Float",
		"width": 140
	})
	columns.append({
		"fieldname": "check_percent",
		"label": "Check > 1%",
		"fieldtype": "Float",
		"width": 120
	})
	columns.append({
		"fieldname": "boq_amount",
		"label": "BOQ Amount",
		"fieldtype": "Currency",
		"width": 140
	})
	columns.append({
		"fieldname": "amount_within",
		"label": "Within 20% DL",
		"fieldtype": "Currency",
		"width": 140
	})
	columns.append({
		"fieldname": "amount_beyond",
		"label": "Beyond 20% DL",
		"fieldtype": "Currency",
		"width": 140
	})
	columns.append({
		"fieldname": "financial_implication",
		"label": "Financial Implication",
		"fieldtype": "Currency",
		"width": 140
	})
	columns.append({
		"fieldname": "project",
		"label": "Project",
		"fieldtype": "Link",
		"options": "Project",
		"width": 140
	})
	return columns


def get_data(filters):
	data = []
	conditions = get_conditions(filters)
	boq = frappe.db.sql("""
		SELECT b.name as boq, bi.boq_code, bi.party_boq_code, bi.description, bi.quantity as boq_qty,
			bi.rate as boq_rate, b.project, b.total_amount
		FROM `tabBOQ` b, `tabBOQ Item` bi
		WHERE bi.parent = b.name and b.docstatus = 1 {}
		GROUP BY b.name, bi.boq_code
		ORDER BY b.name, bi.boq_code
	""".format(conditions), as_dict=True)
	boq_wise_record = frappe._dict()
	for d in boq:
		boq_wise_record.setdefault(d.boq,[]).append(d)
	
	for key, value in boq_wise_record.items():
		for item in value:
			executed_qty = frappe.db.sql("""
				select IFNULL(SUM(mbi.entry_quantity),0) as executed_qty
				from `tabMB Entry` mb, `tabMB Entry BOQ` mbi
				where mbi.parent = mb.name and mb.docstatus = 1 and mb.boq = '{0}'
				and mbi.boq_code = '{1}'
				group by mbi.boq_code, mb.boq
			""".format(key, item.boq_code))
			
			item['executed_qty'] = executed_qty[0][0] if (executed_qty and executed_qty[0][0] is not None) else 0
			item['qty_within'] = 1.2 * item['boq_qty'] if item['boq_qty'] else 0
			item['qty_beyond'] = item['executed_qty'] - item['qty_within']
			item['rate_within'] = item['boq_rate']
			item['rate_beyond'] = item['boq_rate']
			item['check_percent'] = item['boq_rate'] * item['qty_beyond'] / item['total_amount'] * 100
			item['boq_amount'] = item['boq_qty'] * item['boq_rate']
			item['amount_within'] = item['qty_within'] * item['rate_within']
			item['amount_beyond'] = item['qty_beyond'] * item['rate_beyond']
			item['financial_implication'] = item['amount_beyond'] + item['amount_within'] - item['boq_amount']
		
		boq_row = frappe._dict()
		boq_row = {'boq': key}

		data.append(boq_row)
		for d in value:
			d.boq = ''
			d.executed_qty = d.executed_qty if d.executed_qty else 0
		data += value
	return data

def get_conditions(filters):
	conditions = ""
	if filters.get("project"):
		conditions += " and b.project = \'" + str(filters.project) + "\'"

	if filters.get("boq"):
		conditions += " and b.name = \'" + str(filters.boq) + "\'"
	
	if filters.get("from_date") and filters.get("to_date"):
		conditions += f" and b.boq_date between '{filters['from_date']}' and '{filters['to_date']}'"

	return conditions

