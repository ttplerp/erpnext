# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _, _dict
from frappe.utils import cstr, getdate, flt

def execute(filters=None):
	columns = get_columns(filters)
	queries = construct_query(filters)
	data = get_data(queries, filters)

	return columns, data

def get_data(query, filters):
	final_data = []
	datas = frappe.db.sql(query, as_dict=True)
	ini = su = cur = cm = co = ad = av = 0
	for d in datas:
		lft, rgt = frappe.db.get_value("Cost Center", d.cost_center, ["lft", "rgt"])
		cond = """ and (cost_center in (select name 
											from `tabCost Center`
											where lft >= {1} and rgt <= {2}
											) 
					 or cost_center = '{0}')
				""".format(d.cost_center, lft, rgt)

		committed = frappe.db.sql("select SUM(amount) from `tabCommitted Budget` where reference_date BETWEEN '{0}' and '{1}' {cond}".format(filters.from_date, filters.to_date, cond=cond))[0][0]
		consumed = frappe.db.sql("select SUM(amount) from `tabConsumed Budget` where reference_date BETWEEN '{0}' and '{1}' {cond}".format(filters.from_date, filters.to_date, cond=cond))[0][0]

		if not committed:
			committed = 0
		if not consumed:
			consumed = 0
			
		adjustment = flt(d.added) - flt(d.deducted)
		supplement = flt(d.supplement)
		# current    = flt(d.initial_budget) + flt(d.supplement) +flt(adjustment)
		
		if committed > 0:
			# committed -= consumed
			committed = flt(committed - consumed, 2)
			committed = 0 if committed < 0 else flt(committed, 2)

		available = flt(d.initial_budget) + flt(adjustment) + flt(d.supplement) - flt(consumed) - flt(committed)
		if d.initial_budget > 0:
			row = {
				"cost_center": d.cost_center,
				"initial": flt(d.initial_budget),
				"supplementary": supplement,
				"adjustment": adjustment,
				# "current": current,
				"committed": flt(committed, 2),
				"consumed": flt(consumed, 2),
				"available": flt(available, 2)
			}

			final_data.append(row)
			ini+=flt(d.initial_budget)
			su+=supplement
			cm+=committed
			# cur+=current
			co+=consumed
			ad+=adjustment
			av+=flt(available)
	row = {
		"cost_center": "Total",
		"initial": ini,
		"supplementary": su,
		"adjustment": ad,
		"committed": cm,
		"consumed": co,
		"available": av
	}
	final_data.append(row)
	return final_data
		
def construct_query(filters):
	condition = ""
	if filters.cost_center:
		lft, rgt = frappe.db.get_value("Cost Center", filters.cost_center, ["lft", "rgt"])
		condition += """ and (b.cost_center in (select a.name 
											from `tabCost Center` a 
											where a.lft >= {1} and a.rgt <= {2} and center_category = 'Domain'
											) 
					 or b.cost_center = '{0}')
				""".format(filters.cost_center, lft, rgt)
	
	query = """select b.cost_center, b.project,
			SUM(ba.budget_amount) as budget_amount, 
			SUM(ba.initial_budget) as initial_budget, 
			SUM(ba.budget_received) as added, 
			SUM(ba.budget_sent) as deducted, 
			SUM(ba.supplementary_budget) as supplement
		from `tabBudget` b, `tabBudget Account` ba 
		where b.docstatus = 1 
			and b.name = ba.parent 
			and b.fiscal_year = '{fiscal_year}'
		{condition}
		group by b.cost_center
		""".format(fiscal_year=filters.fiscal_year, condition=condition)
	
	return query

def get_columns(filters):
	return [
		{
			"label": _("Domain"),
			"fieldname": "cost_center",
			"fieldtype": "Link",
			"options": "Cost Center",
			"width": 120,
		},
		{
			"label": _("Initial"),
			"fieldname": "initial",
			"fieldtype": "Data",
			"width": 120,
		},
		{
			"label": _("Supplement"),
			"fieldname": "supplement",
			"fieldtype": "Data",
			"width": 120,
		},
		{
			"label": _("Adjustment"),
			"fieldname": "adjustment",
			"fieldtype": "Data",
			"width": 120,
		},
		{
			"label": _("Committed"),
			"fieldname": "committed",
			"fieldtype": "Data",
			"width": 120,
		},
		{
			"label": _("Consumed"),
			"fieldname": "consumed",
			"fieldtype": "Data",
			"width": 120,
		},
		{
			"label": _("Available"),
			"fieldname": "available",
			"fieldtype": "Data",
			"width": 120,
		}
	]