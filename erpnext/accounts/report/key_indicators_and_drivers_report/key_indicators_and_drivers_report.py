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

		# add driver rows
		add_drivers_rows(modified_data, filters)

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

def add_drivers_row(modified_data):
	drivers_row = {
		"account_name": "Drivers",
		"account": "Drivers",
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

def add_headcount_row(modified_data):
	drivers_row = {
		"account_name": "Drivers",
		"account": "Drivers",
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

	headcount_row = {
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
	modified_data.append(headcount_row)

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

	asset = get_asset(filters)
	# Calculate "Return on Assets" row
	return_on_asset_actuals = net_profit_actuals/asset[0] * 100
	return_on_asset_planned = 0
	return_on_asset_comparison = net_profit_comparison/asset[1] * 100
	
	equity = get_equity(filters)
	# Calculate "Return on Equity" row
	return_on_equity_actuals = net_profit_actuals/equity * 100
	return_on_equity_planned = 0
	return_on_equity_comparison = net_profit_comparison/equity * 100

	# Calculate "Revenue Per Employee" row
	employee_count = get_employee_count(filters)
	if len(employee_count) >= 1 and employee_count[0]:
		rev_per_employee_actual = net_profit_actuals / employee_count[0] * 100
		rev_per_employee_planned = net_profit_planned / employee_count[0] * 100
	else:
		rev_per_employee_actual = 0
		rev_per_employee_planned = 0

	if len(employee_count) >= 2 and employee_count[1]:
		rev_per_employee_comparison = net_profit_comparison / employee_count[1] * 100
	else:
		rev_per_employee_comparison = 0

	create_row(modified_data, "Operating Efficiency %", operating_efficiency, operating_efficiency_planned, operating_efficiency_comparison)
	create_row(modified_data, "Return on Assets %", return_on_asset_actuals, return_on_asset_planned, return_on_asset_comparison)
	create_row(modified_data, "Return on Equity %", return_on_equity_actuals, return_on_equity_planned, return_on_equity_comparison)
	create_row(modified_data, "Revenue Per Employee", rev_per_employee_actual, rev_per_employee_planned, rev_per_employee_comparison)

def add_drivers_rows(modified_data, filters):
	# Headcount of employee
	employee_count = get_employee_count(filters)
	employee_actual = 0
	employee_planned = 0
	employee_comparison = 0

	if len(employee_count) >= 1:
		employee_actual = employee_count[0]

	if len(employee_count) >= 2:
		employee_comparison = employee_count[1]

	# Rental units
	rental_units_count = get_rental_count(filters)
	rental_actual = 0
	rental_planned = 0
	rental_comparison = 0
	if len(rental_units_count) >= 1:
		rental_actual = rental_units_count[0]

	if len(rental_units_count) >= 2:
		rental_comparison = rental_units_count[1]
	
	# Units of concrete produced
	concrete_products = get_products_produced('Concrete Work', filters)
	concrete_actual = 0
	concrete_planned = 0
	concrete_comparison = 0
	if len(concrete_products) >= 1:
		concrete_actual = concrete_products[0]

	if len(concrete_products) >= 2:
		concrete_comparison = concrete_products[1]
	
	# Units of woods produced
	wood_products = get_products_produced('Wood Work', filters)
	wood_actual = 0
	wood_planned = 0
	wood_comparison = 0
	if len(wood_products) >= 1:
		wood_actual = wood_products[0]

	if len(wood_products) >= 2:
		wood_comparison = wood_products[1]
		
	create_row(modified_data, "No of Employee", employee_actual, employee_planned, employee_comparison)
	create_row(modified_data, "Rental Units", rental_actual, rental_planned, rental_comparison)
	create_row(modified_data, "No. of Units Produced (Concrete)", concrete_actual, concrete_planned, concrete_comparison)
	create_row(modified_data, "No. of Units Produced (Wood)", wood_actual, wood_planned, wood_comparison)

def get_products_produced(branch, filters):
	total_products_count = []

	query = """
		SELECT
			COALESCE(SUM(sed.qty), 0) as units
		FROM
			`tabStock Entry` se,
			`tabStock Entry Detail` sed
		WHERE
			sed.parent = se.name
			AND se.docstatus = 1
			AND se.stock_entry_type = 'Manufacture'
			AND sed.t_warehouse = 'FInished goods wareshouse - NHDCL'
			AND se.branch = '{branch}'
			AND se.posting_date BETWEEN '{from_date}' AND '{to_date}'
	"""

	current_units = frappe.db.sql(query.format(branch=branch, from_date=filters.current_from_date, to_date=filters.current_to_date), as_dict=True)
	if current_units:
		for d in current_units:
			total_products_count.append(d.units)

	comparison_units = frappe.db.sql(query.format(branch=branch, from_date=filters.comparison_from_date, to_date=filters.comparison_to_date), as_dict=True)
	if comparison_units:
		for d in comparison_units:
			total_products_count.append(d.units)
	
	return total_products_count

def get_equity(filters):
	year = datetime.strptime(filters.current_from_date, '%Y-%m-%d').year

	period_list = get_period_list(
		year,
		year,
		year,
		year,
		"Fiscal Year",  
		"Yearly",       
		filters.accumulated_values,
		filters.company
	)

	equity = get_key_data(
		filters.company,
		"Equity",
		"Credit",
		period_list,
		only_current_fiscal_year=False,
		filters=filters,
		accumulated_values=filters.accumulated_values,
	)

	total_equity = 0
	for row in equity:
		if row.get('account_name') == 'Share Capital':
			total_equity = row.get('total')
			break

	return total_equity

def get_asset(filters):
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

	current_asset = get_asset_value(filters, current_period_list)

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

	comparison_asset = get_asset_value(filters, comparison_period_list)

	current_total = current_asset[-2].get('total', 0) if len(current_asset) >= 2 else 0
	comparison_total = comparison_asset[-2].get('total', 0) if len(comparison_asset) >= 2 else 0

	# Combine 'total' values into a single list
	total_values = [current_total, comparison_total]

	return total_values

def get_asset_value(filters, period_list):
	asset = get_key_data(
		filters.company,
		"Asset",
		"Debit",
		period_list,
		only_current_fiscal_year=False,
		filters=filters,
		accumulated_values=filters.accumulated_values,
	)
	return asset

def get_employee_count(filters):
	to_month = datetime.strptime(filters.current_to_date, '%Y-%m-%d').strftime('%m')
	comparison_to_month = datetime.strptime(filters.comparison_to_date, '%Y-%m-%d').strftime('%m')

	total_employee_count = []

	current_month_employee = frappe.db.get_all("Salary Slip", {"month": to_month, "docstatus": 1})
	current_month_employee_count = len(current_month_employee)
	if current_month_employee_count > 0:
		total_employee_count.append(current_month_employee_count)

	comparison_month_employee = frappe.db.get_all("Salary Slip", {"month": comparison_to_month, "docstatus": 1})
	comparison_month_employee_count = len(comparison_month_employee)
	if comparison_month_employee_count > 0:
		total_employee_count.append(comparison_month_employee_count)

	return total_employee_count

def get_rental_count(filters):
	to_month = datetime.strptime(filters.current_to_date, '%Y-%m-%d').strftime('%m')
	comparison_to_month = datetime.strptime(filters.comparison_to_date, '%Y-%m-%d').strftime('%m')

	total_rental_count = []

	current_month_rental = frappe.db.get_all("Rental Bill", {"month": to_month, "docstatus": 1})
	current_month_rental_count = len(current_month_rental)
	if current_month_rental_count > 0:
		total_rental_count.append(current_month_rental_count)

	comparison_month_rental = frappe.db.get_all("Rental Bill", {"month": comparison_to_month, "docstatus": 1})
	comparison_month_rental_count = len(comparison_month_rental)
	if comparison_month_rental_count > 0:
		total_rental_count.append(comparison_month_rental_count)
	
	return total_rental_count

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
