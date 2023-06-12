# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
import datetime
from frappe.utils import flt, getdate, formatdate, cstr, get_first_day, get_last_day
from erpnext.accounts.accounts_custom_functions import get_child_cost_centers

def execute(filters=None):
	validate_filters(filters)
	from_date, to_date  = None, None
	if filters.monthly_budget:
		if filters.month:
			for month_id in range(1, 13):
				month = datetime.date(2013, month_id, 1).strftime("%B")
				if filters.month == month:
					month_num  = str("0")+str(month_id) if month_id < 10 else str(month_id)
					first_day = filters.fiscal_year + "-" + month_num + "-" + "01"
			from_date = getdate(first_day)
			to_date =  get_last_day(from_date)
	if not from_date and not to_date:
		from_date = filters.from_date
		to_date = filters.to_date

	columns = get_columns(filters)
	queries = construct_query(from_date, to_date,filters)
	data = get_data(queries,from_date, to_date, filters)
	return columns, data

def get_data(query,from_date, to_date, filters):
	data = []
	datas = frappe.db.sql(query, as_dict=True)
	ini = su = cur = cm = co = ad = av = 0
	budget_level = filters.budget_against
	for d in datas:
		if filters.monthly_budget:
			initial_budget = d.monthly_budget
			supplement = flt(frappe.db.sql("""
									select sum(amount)
									from `tabSupplementary Details`
									where month ="{month}"
									and account="{account}"
									and cost_center="{cost_center}"
									and posting_date between '{from_date}' and '{to_date}'
								""".format(month=filters.month, from_date=from_date, to_date=to_date, account = d.account, cost_center=d.cost_center))[0][0],2)
			monthly_received = frappe.db.sql("""
									select sum(amount)
									from `tabReappropriation Details`
									where to_month="{month}"
									and to_account="{account}"
									and to_cost_center="{cost_center}"
								""".format(month=filters.month, from_date=from_date, to_date=to_date, account = d.account, cost_center=d.cost_center))[0][0]
			monthly_sent = frappe.db.sql("""
									select sum(amount)
									from `tabReappropriation Details`
									where from_month="{month}"
									and from_account="{account}"
									and from_cost_center="{cost_center}"
								""".format(month=filters.month, from_date=from_date, to_date=to_date, account = d.account, cost_center=d.cost_center))[0][0]
			adjustment = flt(monthly_received,2) - flt(monthly_sent,2)

		else:
			initial_budget = d.initial_budget
			adjustment = flt(d.added) - flt(d.deducted)
			supplement = flt(d.supplement)
		if filters.monthly_budget:
			cost_center = d.cost_center
			committed = frappe.db.sql("select SUM(amount) from `tabCommitted Budget` where cost_center = %s and account = %s and reference_date BETWEEN %s and %s", (d.cost_center, d.account, from_date, to_date))[0][0]
			consumed = frappe.db.sql("select SUM(amount) from `tabConsumed Budget` where cost_center = %s and account = %s and reference_date BETWEEN %s and %s", (d.cost_center, d.account, from_date, to_date))[0][0]
		elif filters.group_by_account and filters.budget_against != "Project":
			cost_center = ""
			committed = frappe.db.sql("select SUM(amount) from `tabCommitted Budget` where account = %s and reference_date BETWEEN %s and %s", (d.account, filters.from_date, filters.to_date))[0][0]
			consumed = frappe.db.sql("select SUM(amount) from `tabConsumed Budget` where account = %s and reference_date BETWEEN %s and %s", (d.account, filters.from_date, filters.to_date))[0][0]
		
		elif filters.budget_against == "Project":
			project = filters.project
			committed = frappe.db.sql("select SUM(amount) from `tabCommitted Budget` where cost_center = %s and project = %s and reference_date BETWEEN %s and %s", (d.cost_center, d.project, filters.from_date, filters.to_date))[0][0]
			consumed = frappe.db.sql("select SUM(amount) from `tabConsumed Budget` where cost_center = %s and project = %s and reference_date BETWEEN %s and %s", (d.cost_center, d.project, filters.from_date, filters.to_date))[0][0]
		
		else:
			cost_center = d.cost_center
			committed = frappe.db.sql("select SUM(amount) from `tabCommitted Budget` where cost_center = %s and account = %s and reference_date BETWEEN %s and %s", (d.cost_center, d.account, filters.from_date, filters.to_date))[0][0]
			consumed = frappe.db.sql("select SUM(amount) from `tabConsumed Budget` where cost_center = %s and account = %s and reference_date BETWEEN %s and %s", (d.cost_center, d.account, filters.from_date, filters.to_date))[0][0]
		
		if not committed:
			committed = 0
		if not consumed:
			consumed = 0
		
		if committed > 0:
			committed -= consumed
			committed = 0 if committed < 0 else committed
		if filters.monthly_budget and filters.month:
			current    = flt(initial_budget) + flt(supplement) +flt(adjustment)
			available = flt(initial_budget) + flt(adjustment) + flt(supplement) - flt(consumed) - flt(committed)
		else:
			current    = flt(d.initial_budget) + flt(d.supplement) +flt(adjustment)
			available = flt(d.initial_budget) + flt(adjustment) + flt(d.supplement) - flt(consumed) - flt(committed)
		if d.budget_amount > 0:
			if filters.budget_against != "Project":
				row = {
					"account": d.account,
					"account_number": d.account_number,
					"budget_type": d.budget_type,
					"cost_center": cost_center,
					"initial": flt(initial_budget),
					"supplementary": supplement,
					"adjustment": adjustment,
					"current": current,
					"committed": committed,
					"consumed": consumed,
					"available": available
				}
			else:
				row = {
					"account": d.account,
					"project": d.project,
					"project_name": d.project_name,
					"cost_center": d.cost_center,
					"initial": flt(initial_budget),
					"supplementary": supplement,
					"adjustment": adjustment,
					"current": current,
					"committed": committed,
					"consumed": consumed,
					"available": available
				}

			data.append(row)
	return data

def construct_query(from_date,ot_date,filters=None):
	condition = ''
	# if filters.budget_against == "Project":
	# 	condition += " and b.project = \'" + str(filters.project) + "\' "
	if filters.budget_against == "Cost Center" and filters.cost_center:
		condition += " and b.cost_center = \'" + str(filters.cost_center) + "\' "
		
	if filters.budget_type:
		condition += " and ba.budget_type = \'" + str(filters.budget_type) + "\' "
	
	if filters.cost_center and not filters.group_by_account:
		lft, rgt = frappe.db.get_value("Cost Center", filters.cost_center, ["lft", "rgt"])
		condition += """ and (b.cost_center in (select a.name 
											from `tabCost Center` a 
											where a.lft >= {1} and a.rgt <= {2}
											) 
					 or b.cost_center = '{0}')
				""".format(filters.cost_center, lft, rgt)
	if filters.budget_type:
		condition += " and ba.budget_type = \'" + str(filters.budget_type) + "\' "

	if filters.monthly_budget and filters.month:
		# condition += " and ba.budget_type = \'" + str(filters.budget_type) + "\' "
		month_field_name = filters.month
		query = """select b.cost_center, ba.account, b.project,
			(select a.account_number from `tabAccount` a where a.name = ba.account) as account_number, 
			ba.budget_type,
			SUM(ba.budget_amount) as budget_amount,
			sum(ba.{month_name}) as monthly_budget,
			SUM(ba.initial_budget) as initial_budget, 
			SUM(ba.budget_received) as added, 
			SUM(ba.budget_sent) as deducted, 
			SUM(ba.supplementary_budget) as supplement
		from `tabBudget` b, `tabBudget Account` ba 
		where b.docstatus = 1 
			and b.name = ba.parent 
			and b.fiscal_year = {fiscal_year}
		{condition}
		""".format(fiscal_year=filters.fiscal_year, condition=condition,month_name=month_field_name.lower())
	else:
		query = """select b.cost_center, ba.account, b.project,
			(select a.account_number from `tabAccount` a where a.name = ba.account) as account_number, 
			ba.budget_type,
			SUM(ba.budget_amount) as budget_amount, 
			SUM(ba.initial_budget) as initial_budget, 
			SUM(ba.budget_received) as added, 
			SUM(ba.budget_sent) as deducted, 
			SUM(ba.supplementary_budget) as supplement
		from `tabBudget` b, `tabBudget Account` ba 
		where b.docstatus = 1 
			and b.name = ba.parent 
			and b.fiscal_year = {fiscal_year}
		{condition}
		""".format(fiscal_year=filters.fiscal_year, condition=condition)
	
	if filters.group_by_account:
		query += " group by ba.account "
	elif filters.budget_against == "Project":
		query += " group by b.cost_center, b.project"
	else:
		query += " group by ba.account, b.cost_center order by b.cost_center"
	return query

def validate_filters(filters):
	if not filters.fiscal_year:
		frappe.throw(_("Fiscal Year {0} is required").format(filters.fiscal_year))

	fiscal_year = frappe.db.get_value("Fiscal Year", filters.fiscal_year, ["year_start_date", "year_end_date"], as_dict=True)
	if not fiscal_year:
		frappe.throw(_("Fiscal Year {0} does not exist").format(filters.fiscal_year))
	else:
		filters.year_start_date = getdate(fiscal_year.year_start_date)
		filters.year_end_date = getdate(fiscal_year.year_end_date)

	if not filters.from_date:
		filters.from_date = filters.year_start_date

	if not filters.to_date:
		filters.to_date = filters.year_end_date

	filters.from_date = getdate(filters.from_date)
	filters.to_date = getdate(filters.to_date)

	if filters.from_date > filters.to_date:
		frappe.throw(_("From Date cannot be greater than To Date"))

	if (filters.from_date < filters.year_start_date) or (filters.from_date > filters.year_end_date):
		frappe.msgprint(_("From Date should be within the Fiscal Year. Assuming From Date = {0}")\
			.format(formatdate(filters.year_start_date)))

		filters.from_date = filters.year_start_date

	if (filters.to_date < filters.year_start_date) or (filters.to_date > filters.year_end_date):
		frappe.msgprint(_("To Date should be within the Fiscal Year. Assuming To Date = {0}")\
			.format(formatdate(filters.year_end_date)))
		filters.to_date = filters.year_end_date

def get_columns(filters):
	return [
		{
			"fieldname": "account",
			"label": "Account Head",
			"fieldtype": "Link",
			"options": "Account",
			"width": 200
		},
		{
			"fieldname": "account_number",
			"label": "Account Number",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "budget_type",
			"label": "Budget Type",
			"fieldtype": "Link",
			"options": "Budget Type",
			"width": 120,
		},
		{
			"fieldname": "cost_center",
			"label": "Cost Center",
			"fieldtype": "Link",
			"options": "Cost Center",
			"width": 150
		},
		{
			"fieldname": "initial",
			"label": "Initial",
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"fieldname": "supplementary",
			"label": "Supplement",
			"fieldtype": "Currency",
			"width": 110
		},
		{
			"fieldname": "adjustment",
			"label": "Adjustment",
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"fieldname": "current",
			"label": "Current",
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"fieldname": "committed",
			"label": "Committed",
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"fieldname": "consumed",
			"label": "Consumed",
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"fieldname": "available",
			"label": "Available",
			"fieldtype": "Currency",
			"width": 120
		}
	]