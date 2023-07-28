# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt
from erpnext.accounts.report.financial_statements_nhdcl import (
	filter_accounts,
	set_gl_entries_by_account,
	filter_out_zero_value_rows,
)
from erpnext.accounts.accounts_custom_functions import get_child_cost_centers
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


value_fields = (
	"debit",
	"credit",
	"comparison_debit",
	"comparison_credit",
	"planned",
	"actual_plan_difference",
	"actual_plan_diff_percent",
	"comparison_actual_difference",
	"comparison_actual_diff_percent",
)

def execute(filters=None):
	data, parent_children_map = get_data(filters)
	columns = get_columns(filters)

	if data:
		calculate_row_values(data)
		
	return columns, data, parent_children_map

def add_operating_efficiency_row(data):
	revenue_actuals, expense_actuals = 0.0, 0.0
	revenue_planned, expense_planned = 0.0, 0.0
	comparison_revenue, comparison_expense = 0.0, 0.0

	# Calculate the total revenue and expense actuals and planned
	for row in data:
		parent_account = row.get("parent_account")
		actuals = row.get("actuals", 0.0)
		planned = row.get("planned", 0.0)
		comparison_actuals = row.get("comparison_actuals", 0.0)

		if parent_account is None:
			if row.get("root_type") == "Income":
				revenue_actuals += actuals
				revenue_planned += planned
				comparison_revenue += comparison_actuals
			elif row.get("root_type") == "Expense":
				expense_actuals += actuals
				expense_planned += planned
				comparison_expense += comparison_actuals

	# Calculate "Operating Efficiency" row
	operating_efficiency = expense_actuals / revenue_actuals * 100 if revenue_actuals != 0 else 0
	operating_efficiency_planned = expense_planned / revenue_planned * 100 if revenue_planned != 0 else 0
	operating_efficiency_comparison = comparison_expense / comparison_revenue * 100 if comparison_revenue != 0 else 0

	create_row(data, "Operating Efficiency %", operating_efficiency, operating_efficiency_planned, operating_efficiency_comparison)

def calculate_row_values(data):
	revenue_actuals, expense_actuals = 0.0, 0.0
	revenue_planned, expense_planned = 0.0, 0.0
	comparison_revenue, comparison_expense = 0.0, 0.0

	# Calculate the total revenue and expense actuals and planned
	for row in data:
		if row["parent_account"] is None:
			if row["root_type"] == "Income":
				revenue_actuals += row["actuals"]
				revenue_planned += row["planned"]
				comparison_revenue += row["comparison_actuals"]
			elif row["root_type"] == "Expense":
				expense_actuals += row["actuals"]
				expense_planned += row["planned"]
				comparison_expense += row["comparison_actuals"]

	# Calculate "Margin" row
	margin_actuals = revenue_actuals - expense_actuals
	margin_planned = revenue_planned - expense_planned
	margin_comparison = comparison_revenue - comparison_expense

	# Calculate "Earnings Before Income Tax" row
	earnings_before_tax_actuals = margin_actuals
	earnings_before_tax_planned = margin_planned
	earnings_before_tax_comparison = margin_comparison

	# Calculate "Tax" row
	tax_rate = 0.30  # 30% tax rate
	tax_amount_actuals = earnings_before_tax_actuals * tax_rate
	tax_amount_planned = earnings_before_tax_planned * tax_rate
	tax_amount_comparison = earnings_before_tax_comparison * tax_rate

	# Calculate "Net Profit After Tax" row
	net_profit_actuals = earnings_before_tax_actuals - tax_amount_actuals
	net_profit_planned = earnings_before_tax_planned - tax_amount_planned
	net_profit_comparison = earnings_before_tax_comparison - tax_amount_comparison

	create_row(data, "Margin", margin_actuals, margin_planned, margin_comparison)
	create_row(data, "Earnings Before Income Tax", earnings_before_tax_actuals, earnings_before_tax_planned, earnings_before_tax_comparison)
	create_row(data, "Tax", tax_amount_actuals, tax_amount_planned, tax_amount_comparison)
	create_row(data, "Net Profit After Tax", net_profit_actuals, net_profit_planned, net_profit_comparison)

def create_row(data, name, actuals, planned, comparison):
	row = {
		"account_name": name,
		"account": name,
		"indent": 0,
		"actuals": actuals,
		"planned": planned,
		"actual_plan_difference": actuals - planned,
		"actual_plan_diff_percent": (actuals - planned) / planned * 100 if planned else 0.0,
		"comparison_actuals": comparison,
		"comparison_actual_difference": actuals - comparison,
		"comparison_actual_diff_percent": (actuals - comparison) / comparison * 100 if comparison else 0.0,
		"has_value": True,
	}
	data.append(row)
	row["actuals"] = round(row["actuals"], 2)
	row["comparison_actuals"] = round(row["comparison_actuals"], 2)
	row["comparison_actual_difference"] = round(row["comparison_actual_difference"], 2)

def get_data(filters):
	accounts = frappe.db.sql(
		"""SELECT name, parent_account, account_name, root_type
		FROM `tabAccount`
		WHERE company=%s AND root_type IN ('Income', 'Expense')
		ORDER BY CASE WHEN root_type = 'Income' THEN 0 ELSE 1 END, name ASC""",
		filters.company,
		as_dict=True,
	)

	if not accounts:
		return None, None

	accounts, accounts_by_name, parent_children_map = filter_accounts(accounts)

	min_lft, max_rgt = frappe.db.sql(
		"""SELECT min(lft), max(rgt)
		FROM `tabAccount`
		WHERE company=%s""",
		(filters.company,),
	)[0]

	gl_entries_by_account = {}
	set_gl_entries_by_account(
		filters.company,
		filters.current_from_date,
		filters.current_to_date,
		min_lft,
		max_rgt,
		filters,
		gl_entries_by_account,
		ignore_closing_entries=False,
	)
	set_gl_entries_by_account(
		filters.company,
		filters.comparison_from_date,
		filters.comparison_to_date,
		min_lft,
		max_rgt,
		filters,
		gl_entries_by_account,
		ignore_closing_entries=False,
	)
	planned_data_by_account = {}
	get_planned_data_for_account(
		filters.company,
		filters.current_from_date,
		filters.current_to_date,
		min_lft,
		max_rgt,
		planned_data_by_account
	)

	combined_data = combine_gl_and_planned_data(gl_entries_by_account, planned_data_by_account)

	total_row = calculate_values(accounts, combined_data, filters)
	accumulate_values_into_parents(accounts, accounts_by_name)

	data = prepare_data(accounts, total_row, parent_children_map, planned_data_by_account)
	data = filter_out_zero_value_rows(
		data,
		parent_children_map,
		show_zero_values=False,
	)
	return data, parent_children_map

def combine_gl_and_planned_data(gl_entries_by_account, planned_data_by_account):
	for account, planned_entries in planned_data_by_account.items():
		if account in gl_entries_by_account:
			gl_entries_by_account[account].extend(planned_entries)
		else:
			gl_entries_by_account[account] = planned_entries

	return gl_entries_by_account

def get_planned_data_for_account(company, from_date, to_date, root_lft, root_rgt, planned_data_by_account):
	from_month = datetime.strptime(from_date, '%Y-%m-%d').strftime('%B')
	to_month = datetime.strptime(to_date, '%Y-%m-%d').strftime('%B')
	
	from_year = datetime.strptime(from_date, '%Y-%m-%d').year
	to_year = datetime.strptime(to_date, '%Y-%m-%d').year

	months_list = []
	current_month = from_month

	while current_month != to_month:
		months_list.append(current_month)
		current_month = (datetime.strptime(current_month, '%B').month % 12) + 1
		current_month = datetime(1900, current_month, 1).strftime('%B')

	months_list.append(to_month)
	
	cond = ''
	accounts = frappe.db.sql_list(
		"""select name from `tabAccount`
		where lft >= %s and rgt <= %s and company = %s""",
		(root_lft, root_rgt, company),
	)

	if accounts:
		cond += " and account in ({})".format(
			", ".join(frappe.db.escape(d) for d in accounts)
		)

	for month in months_list:
		month_lower = month.lower()
		revenue_entries = frappe.db.sql(
			"""
			SELECT 
				rta.account, SUM(rta.{month}) as monthly_amt, rt.fiscal_year
			FROM `tabRevenue Target` rt, `tabRevenue Target Account` rta
			WHERE rta.parent=rt.name AND rt.docstatus = 1
			AND rt.company='{company}'
			AND rt.fiscal_year = '{from_year}'
			{cond}
			GROUP BY rta.account
			""".format(month=month, company=company, from_year=from_year, cond=cond), as_dict=True,
		)

		for entry in revenue_entries:
			planned_data_by_account.setdefault(entry.account, []).append(entry)
		
		query = f"""
			SELECT 
				ba.account, 
				SUM(ba.{month_lower} + ba.sb_{month_lower} + ba.br_{month_lower} - ba.bs_{month_lower}) as monthly_amt, 
				b.fiscal_year
			FROM `tabBudget` b, `tabBudget Account` ba
			WHERE ba.parent=b.name AND b.docstatus = 1
			AND b.company='{company}'
			AND b.fiscal_year = '{from_year}'
			{cond}
			GROUP BY ba.account
		"""
		budget_entries = frappe.db.sql(query, as_dict=True)

		for entry in budget_entries:
			planned_data_by_account.setdefault(entry.account, []).append(entry)

	return planned_data_by_account

def calculate_values(accounts, combined_data, filters):
	init = {
		"debit": 0.0,
		"credit": 0.0,
		"comparison_debit": 0.0,
		"comparison_credit": 0.0,
		"planned": 0.0,
		"actual_plan_difference": 0.0, 
		"actual_plan_diff_percent": 0.0, 
		"comparison_actual_difference": 0.0, 
		"comparison_actual_diff_percent": 0.0, 
	}

	total_row = {
		"account": None,
		"account_name": _("Total"),
		"debit": 0.0,
		"credit": 0.0,
		"root_type": None,
		"comparison_debit": 0.0,
		"comparison_credit": 0.0,
		"planned": 0.0,
		"actual_plan_difference": 0.0,
		"actual_plan_diff_percent": 0.0,
		"comparison_actual_difference": 0.0, 
		"comparison_actual_diff_percent": 0.0, 
	}

	current_from_date = datetime.strptime(filters.current_from_date, "%Y-%m-%d").date()
	current_to_date = datetime.strptime(filters.current_to_date, "%Y-%m-%d").date()
	comparison_from_date = datetime.strptime(filters.comparison_from_date, "%Y-%m-%d").date()
	comparison_to_date = datetime.strptime(filters.comparison_to_date, "%Y-%m-%d").date()

	for d in accounts:
		d.update(init.copy())

		for entry in combined_data.get(d.name, []):
			if entry.posting_date and current_from_date <= entry.posting_date <= current_to_date:
				d["debit"] += flt(entry.debit, 3)
				d["credit"] += flt(entry.credit, 3)
			elif entry.posting_date and comparison_from_date <= entry.posting_date <= comparison_to_date:
				d["comparison_debit"] += flt(entry.debit, 3)
				d["comparison_credit"] += flt(entry.credit, 3)
			d["planned"] += flt(entry.monthly_amt, 3)

		# Calculate the actuals based on root_type
		if d["root_type"] == "Income":
			d["actuals"] = d["credit"] - d["debit"]
			d["comparison_actuals"] = d["comparison_credit"] - d["comparison_debit"]

		elif d["root_type"] == "Expense":
			d["actuals"] = d["debit"] - d["credit"]
			d["comparison_actuals"] = d["comparison_debit"] - d["comparison_credit"]
		else:
			d["actuals"] = 0.0
			d["comparison_actuals"] = 0.0

		# Calculate the difference between actuals and planned
		d["actual_plan_difference"] = d["actuals"] - d["planned"]
		
		# Calculate the difference percentage
		d["actual_plan_diff_percent"] = (d["actual_plan_difference"] / d["planned"]) * 100 if d["planned"] else 0.0

		# Calculate the difference between actuals and comparison_actuals
		d["comparison_actual_difference"] = d["actuals"] - d["comparison_actuals"]

		# Calculate the difference percentage
		d["comparison_actual_diff_percent"] = (d["comparison_actual_difference"] / d["comparison_actuals"]) * 100 if d["comparison_actuals"] else 0.0

		total_row["debit"] += d["debit"]
		total_row["credit"] += d["credit"]
		total_row["comparison_debit"] += d["comparison_debit"]
		total_row["comparison_credit"] += d["comparison_credit"]
		total_row["root_type"] = d["root_type"]
		total_row["planned"] += d["planned"]
		total_row["actual_plan_difference"] += d["actual_plan_difference"]
		total_row["actual_plan_diff_percent"] += d["actual_plan_diff_percent"]
		total_row["comparison_actual_difference"] += d["comparison_actual_difference"]
		total_row["comparison_actual_diff_percent"] += d["comparison_actual_diff_percent"]

	return total_row

def accumulate_values_into_parents(accounts, accounts_by_name):
	for d in reversed(accounts):
		if d.parent_account:
			for key in value_fields:
				accounts_by_name[d.parent_account][key] += d[key]

def prepare_data(accounts, total_row, parent_children_map, planned_data_by_account):
	data = []

	def add_account_row(account, indent):
		has_value = False
		row = {
			"account_name": account.name,
			"account": account.name,
			"parent_account": account.parent_account,
			"indent": indent,
			"root_type": account.root_type,
			"actuals": 0.0,
			"planned": 0.0,
			"actual_plan_difference": 0.0,  
			"actual_plan_diff_percent": 0.0, 
			"comparison_actuals": 0.0,
			"comparison_actual_difference": 0.0,
			"comparison_actual_diff_percent": 0.0,
			"has_value": True,
		}

		for key in value_fields:
			row[key] = flt(account.get(key, 0.0), 3)

			if abs(row[key]) >= 0.005:
				has_value = True

		row["has_value"] = has_value

		if account.root_type == "Income":
			row["actuals"] = row["credit"] - row["debit"]
			row["comparison_actuals"] = row["comparison_credit"] - row["comparison_debit"]
		elif account.root_type == "Expense":
			row["actuals"] = row["debit"] - row["credit"]
			row["comparison_actuals"] = row["comparison_debit"] - row["comparison_credit"]
		else:
			row["actuals"] = 0.0
			row["comparison_actuals"] = 0.0

		# Retrieve and add the revenue target for the account
		if account.name in planned_data_by_account:
			planned_targets = planned_data_by_account[account.name]
			planned_sum = sum([entry["monthly_amt"] if entry["monthly_amt"] else 0 for entry in planned_targets])
			row["planned"] = planned_sum
			row["actual_plan_difference"] = row["actuals"] - planned_sum
			row["actual_plan_diff_percent"] = (row["actual_plan_difference"] / row["planned"]) * 100 if row["planned"] else 0.0
		
		# Calculate the difference between actuals and comparison_actuals
		row["comparison_actual_difference"] = row["actuals"] - row["comparison_actuals"]
		row["comparison_actual_diff_percent"] = (row["comparison_actual_difference"] / row["comparison_actuals"]) * 100 if row["comparison_actuals"] else 0.0

		data.append(row)

		# Append an additional row if planned value exists but actuals values are 0
		if row["planned"] > 0 and not has_value:
			data.append({
				"account_name": account.name,
				"account": account.name,
				"parent_account": account.parent_account,
				"indent": indent + 1,
				"root_type": account.root_type,
				"actuals": 0.0,
				"planned": row["planned"],
				"actual_plan_difference": -row["planned"],
				"actual_plan_diff_percent": -100.0,
				"comparison_actuals": 0.0,
				"comparison_actual_difference": -row["planned"],
				"comparison_actual_diff_percent": -100.0,
				"has_value": True,
			})

	def process_children(children, indent):
		for child in children:
			add_account_row(child, indent)

			if child.name in parent_children_map:
				process_children(parent_children_map[child.name], indent + 1)

	for account in accounts:
		if not account.parent_account:
			add_account_row(account, 0)

			if account.name in parent_children_map:
				process_children(parent_children_map[account.name], 1)

	return data

def get_columns(filters):
	return [
		{
			"fieldname": "account",
			"label": _("Account"),
			"fieldtype": "Link",
			"options": "Account",
			"width": 300,
		},
		{
			"fieldname": "actuals",
			"label": _("Actuals [{0} - {1}]").format(filters.current_from_date, filters.current_to_date),
			"fieldtype": "Currency",
			"width": 160,
		},
		{
			"fieldname": "planned",
			"label": _("Plan [{0} - {1}]").format(filters.current_from_date, filters.current_to_date),
			"fieldtype": "Currency",
			"width": 160,
		},
		{
			"fieldname": "actual_plan_difference",
			"label": _("I/(D) Nu."),
			"fieldtype": "Currency",
			"width": 140,
		},
		{
			"fieldname": "actual_plan_diff_percent",
			"label": _("I/(D) %"),
			"fieldtype": "Percent",
			"width": 140,
		},
		{
			"fieldname": "comparison_actuals",
			"label": _("Actuals [{0} - {1}]").format(filters.comparison_from_date, filters.comparison_to_date),
			"fieldtype": "Currency",
			"width": 160,
		},
		{
			"fieldname": "comparison_actual_difference",
			"label": _("I/(D) Nu."),
			"fieldtype": "Currency",
			"width": 140,
		},
		{
			"fieldname": "comparison_actual_diff_percent",
			"label": _("I/(D) %"),
			"fieldtype": "Percent",
			"width": 140,
		}
	]

