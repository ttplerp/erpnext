# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt
from erpnext.accounts.report.business_review_report.business_review_report import get_data
from erpnext.accounts.accounts_custom_functions import get_child_cost_centers
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from erpnext.accounts.report.financial_statements_nhdcl import get_key_data, get_period_list

def execute(filters=None):
	data, parent_children_map = get_data(filters)

	modified_data = []
	add_key_indicators_row(modified_data)

	if data:
		# key indicator rows
		add_key_indicators_rows(data, modified_data, filters)

		add_empty_row(modified_data)
		
		# headcount row
		add_headcount_row(modified_data)

	columns = get_columns(filters)

	return columns, modified_data

def add_key_indicators_row(data):
	key_indicators_row = {
		"account_name": "Key Indicators",
		"account": "Key Indicators",
		"indent": 0,
		"actuals": None,
		"planned": None,
		"actual_plan_difference": None,
		"actual_plan_diff_percent": None,
		"comparison_actuals": None,
		"comparison_actual_difference": None,
		"comparison_actual_diff_percent": None,
		"has_value": True,
	}
	data.append(key_indicators_row)

def add_empty_row(data):
	empty_row = {
		"account_name": "",
		"account": "",
		"indent": 0,
		"actuals": None,
		"planned": None,
		"actual_plan_difference": None,
		"actual_plan_diff_percent": None,
		"comparison_actuals": None,
		"comparison_actual_difference": None,
		"comparison_actual_diff_percent": None,
		"has_value": False,
	}
	data.append(empty_row)

def add_headcount_row(modified_data):
	drivers_row = {
		"account_name": "Headcount",
		"account": "Headcount",
		"indent": 0,
		"actuals": None,
		"planned": None,
		"actual_plan_difference": None,
		"actual_plan_diff_percent": None,
		"comparison_actuals": None,
		"comparison_actual_difference": None,
		"comparison_actual_diff_percent": None,
		"has_value": True,
	}
	modified_data.append(drivers_row)

def add_key_indicators_rows(data, modified_data, filters):
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
	
	tax_rate = 0.30  

	net_profit_actuals = (revenue_actuals - expense_actuals) - (revenue_actuals - expense_actuals) * tax_rate
	net_profit_planned = (revenue_planned - expense_planned) - (revenue_planned - expense_planned) * tax_rate
	net_profit_comparison = (comparison_revenue - comparison_expense) - (comparison_revenue - comparison_expense) * tax_rate
	
	equity = get_equity_for_date_range(filters)

	# asset = get_asset(filters, period_list)
	# Calculate "Return on Assets" row
	return_on_asset_actuals = net_profit_actuals/equity[0] * 100
	return_on_asset_planned = net_profit_actuals/equity[0] * 100
	return_on_asset_comparison = net_profit_actuals/equity[1] * 100
	
	# Calculate "Return on Equity" row
	return_on_equity_actuals = net_profit_actuals/equity[0] * 100
	return_on_equity_planned = net_profit_actuals/equity[0] * 100
	return_on_equity_comparison = net_profit_actuals/equity[1] * 100

	# Calculate "Revenue Per Emplloyee" row
	employee_count = get_employee_count(filters)
	rev_per_employee_actual = net_profit_actuals/employee_count[0] * 100
	rev_per_employee_planned = net_profit_planned/employee_count[0] * 100
	rev_per_employee_comparison = net_profit_comparison/employee_count[1] * 100
	
	create_row(modified_data, "Operating Efficiency %", operating_efficiency, operating_efficiency_planned, operating_efficiency_comparison)
	create_row(modified_data, "Return on Assets %", return_on_asset_actuals, return_on_asset_planned, return_on_asset_comparison)
	create_row(modified_data, "Return on Equity %", return_on_equity_actuals, return_on_equity_planned, return_on_equity_comparison)
	create_row(modified_data, "Revenue Per Employee", rev_per_employee_actual, rev_per_employee_planned, rev_per_employee_comparison)

def get_equity_for_date_range(filters):
	current_period_list = get_period_list(
		filters.current_from_date,
		filters.current_to_date,
		filters.current_from_date,  
		filters.current_to_date,  
		"Date Range",  
		"Yearly",       
		filters.accumulated_values,
		filters.company
	)

	current_equity = get_equity_data(current_period_list, filters)
	
	comparison_period_list = get_period_list(
		filters.comparison_from_date,
		filters.comparison_to_date,
		filters.comparison_from_date,  
		filters.comparison_to_date,  
		"Date Range",  
		"Yearly",       
		filters.accumulated_values,
		filters.company
	)

	comparison_equity = get_equity_data(comparison_period_list, filters)

	current_total = current_equity[-2].get('total', 0) if len(current_equity) >= 2 else 0
	comparison_total = comparison_equity[-2].get('total', 0) if len(comparison_equity) >= 2 else 0
	total_values = [current_total, comparison_total]

	return total_values

def get_equity_data(period_list, filters):
	equity_data = get_key_data(
		filters.company,
		"Equity",
		"Credit",
		period_list,
		only_current_fiscal_year=False,
		filters=filters,
		accumulated_values=filters.accumulated_values,
	)
	return equity_data

def get_employee_count(filters):
	# for actual value
	to_month = datetime.strptime(filters.current_to_date, '%Y-%m-%d').strftime('%B')

	# for comparison value
	comparison_to_month = datetime.strptime(filters.comparison_to_date, '%Y-%m-%d').strftime('%B')

	total_employee_count = []

	# Get employee count for the latest month in the current period
	current_month_employee_count = frappe.db.get_value("Payroll Entry", {"month_name": to_month, "docstatus": 1, "salary_slips_submitted": 1}, "number_of_employees")
	if current_month_employee_count is not None:
		total_employee_count.append(current_month_employee_count)

	# Get employee count for the latest month in the comparison period
	comparison_month_employee_count = frappe.db.get_value("Payroll Entry", {"month_name": comparison_to_month, "docstatus": 1, "salary_slips_submitted": 1}, "number_of_employees")
	if comparison_month_employee_count is not None:
		total_employee_count.append(comparison_month_employee_count)

	return total_employee_count

def add_return_on_assets_row(data, modified_data):
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


def get_columns(filters):
	return [
		{
			"fieldname": "account",
			"label": _("Account"),
			"fieldtype": "Link",
			"options": "Account",
			"width": 200,
		},
		{
			"fieldname": "actuals",
			"label": _("Actuals [{0} - {1}]").format(filters.current_from_date, filters.current_to_date),
			"fieldtype": "Float",
			"width": 160,
		},
		{
			"fieldname": "planned",
			"label": _("Plan [{0} - {1}]").format(filters.current_from_date, filters.current_to_date),
			"fieldtype": "Float",
			"width": 160,
		},
		{
			"fieldname": "actual_plan_difference",
			"label": _("I/(D) Nu."),
			"fieldtype": "Float",
			"width": 120,
		},
		{
			"fieldname": "actual_plan_diff_percent",
			"label": _("I/(D) %"),
			"fieldtype": "Float",
			"width": 120,
		},
		{
			"fieldname": "comparison_actuals",
			"label": _("Actuals [{0} - {1}]").format(filters.comparison_from_date, filters.comparison_to_date),
			"fieldtype": "Float",
			"width": 160,
		},
		{
			"fieldname": "comparison_actual_difference",
			"label": _("I/(D) Nu."),
			"fieldtype": "Float",
			"width": 120,
		},
		{
			"fieldname": "comparison_actual_diff_percent",
			"label": _("I/(D) %"),
			"fieldtype": "Float",
			"width": 120,
		}
	]
