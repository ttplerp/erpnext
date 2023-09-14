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
	"planned",
	"variance",
	"variance_percent",
)

def execute(filters=None):
	data, parent_children_map = get_data(filters)
	columns = get_columns(filters)

	return columns, data, parent_children_map

def get_data(filters):
	accounts = frappe.db.sql(
		"""SELECT name, parent_account, account_name, root_type
		FROM `tabAccount`
		WHERE company=%s AND root_type IN ('Expense', 'Asset')
		ORDER BY CASE WHEN root_type = 'Asset' THEN 0 ELSE 1 END, name ASC""",
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
		filters.from_date,
		filters.to_date,
		min_lft,
		max_rgt,
		filters,
		gl_entries_by_account,
		ignore_closing_entries=False,
	)
	planned_data_by_account = {}
	get_planned_data_for_account(
		filters.company,
		filters.from_date,
		filters.to_date,
		min_lft,
		max_rgt,
		planned_data_by_account,
		filters.budget_against_filter
	)
	# frappe.throw(str(planned_data_by_account))

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

def get_planned_data_for_account(company, from_date, to_date, root_lft, root_rgt, planned_data_by_account, cost_center=None):
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
	
	if cost_center:
		cond += " and b.cost_center in ({})".format(
			", ".join(frappe.db.escape(d) for d in cost_center)
		)

	for month in months_list:
		month_lower = month.lower()
		query = f"""
			SELECT 
				ba.account, 
				COALESCE(SUM(ba.{month_lower}), 0) +
				COALESCE(SUM(ba.sb_{month_lower}), 0) +
				COALESCE(SUM(ba.br_{month_lower}), 0) -
				COALESCE(SUM(ba.bs_{month_lower}), 0) as monthly_amt,
				b.fiscal_year
			FROM `tabBudget` b, `tabBudget Account` ba
			WHERE ba.parent=b.name AND b.docstatus = 1
			AND b.company='{company}'
			AND b.fiscal_year = '{from_year}'
			{cond}
			GROUP BY ba.account
		"""
		# frappe.throw(str(query))
		budget_entries = frappe.db.sql(query, as_dict=True)

		for entry in budget_entries:
			planned_data_by_account.setdefault(entry.account, []).append(entry)

	return planned_data_by_account

def calculate_values(accounts, combined_data, filters):
	init = {
		"debit": 0.0,
		"credit": 0.0,
		"planned": 0.0,
		"variance": 0.0, 
		"variance_percent": 0.0, 
	}

	total_row = {
		"account": None,
		"account_name": _("Total"),
		"debit": 0.0,
		"credit": 0.0,
		"root_type": None,
		"planned": 0.0,
		"variance": 0.0,
		"variance_percent": 0.0,
	}

	from_date = datetime.strptime(filters.from_date, "%Y-%m-%d").date()
	to_date = datetime.strptime(filters.to_date, "%Y-%m-%d").date()

	for d in accounts:
		d.update(init.copy())

		for entry in combined_data.get(d.name, []):
			if entry.posting_date and from_date <= entry.posting_date <= to_date:
				d["debit"] += flt(entry.debit, 3)
				d["credit"] += flt(entry.credit, 3)
			d["planned"] += flt(entry.monthly_amt, 3)

		if d["root_type"]:
			d["actuals"] = d["debit"] - d["credit"]
		else:
			d["actuals"] = 0.0

		# Calculate the difference between actuals and planned
		d["variance"] = d["planned"] - d["actuals"]
		
		# Calculate the difference percentage
		d["variance_percent"] = (d["variance"] / d["planned"]) * 100 if d["planned"] else 0.0

		total_row["debit"] += d["debit"]
		total_row["credit"] += d["credit"]
		total_row["root_type"] = d["root_type"]
		total_row["planned"] += d["planned"]
		total_row["variance"] += d["variance"]
		total_row["variance_percent"] += d["variance_percent"]

	return total_row

def accumulate_values_into_parents(accounts, accounts_by_name):
    for d in reversed(accounts):
        if d.parent_account:
            # Check if the planned value is greater than 0 before accumulating
            if d.planned > 0:
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
			"variance": 0.0,
			"variance_percent": 0.0,
			"has_value": True,
		}

		for key in value_fields:
			row[key] = flt(account.get(key, 0.0), 3)

			if abs(row[key]) >= 0.005:
				has_value = True

		row["has_value"] = has_value

		if account.root_type:
			row["actuals"] = row["debit"] - row["credit"]
		else:
			row["actuals"] = 0.0

		# Retrieve and add the revenue target for the account
		if account.name in planned_data_by_account:
			planned_targets = planned_data_by_account[account.name]
			planned_sum = sum([entry["monthly_amt"] if entry["monthly_amt"] else 0 for entry in planned_targets])
			row["planned"] = planned_sum
			row["variance"] = row["actuals"] - planned_sum
			row["variance_percent"] = (row["variance"] / row["planned"]) * 100 if row["planned"] else 0.0

		# Only add the row if the planned value is greater than 0
		if row["planned"] > 0:
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
					"variance": -row["planned"],
					"variance_percent": -100.0,
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
			"fieldname": "planned",
			"label": _("Budget"),
			"fieldtype": "Currency",
			"width": 160,
		},
		{
			"fieldname": "actuals",
			"label": _("Actual"),
			"fieldtype": "Currency",
			"width": 160,
		},
		{
			"fieldname": "variance",
			"label": _("Variance"),
			"fieldtype": "Currency",
			"width": 140,
		},
		{
			"fieldname": "variance_percent",
			"label": _("Variance Percentaget"),
			"fieldtype": "Percent",
			"width": 140,
		}
	]

