# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, cint, getdate, formatdate, cstr, rounded
from calendar import monthrange, isleap
from erpnext.accounts.report.financial_statements_cdcl \
	import filter_accounts, set_gl_entries_by_account, filter_out_zero_value_rows

value_fields = ("reporting", "comparing", "variance")

def execute(filters=None):
	filters = validate_filters(filters)
	columns = get_columns()
	data = get_data(filters)
	return columns, data

def get_data(filters):
	if filters.report == "Comprehensive Income":
		accounts = frappe.db.sql("""select name, account_number, parent_account, account_name, root_type, report_type, lft, rgt from `tabAccount` where company=%s and root_type in ('Expense', 'Income') order by lft""", filters.company, as_dict=True)
	if filters.report == "Financial Position":
		accounts = frappe.db.sql("""select name, account_number, parent_account, account_name, root_type, report_type, lft, rgt from `tabAccount` where company=%s and root_type in ('Asset', 'Liability', 'Equity') order by lft""", filters.company, as_dict=True)

	if not accounts:
		return None

	accounts, accounts_by_name, parent_children_map = filter_accounts(accounts)

	min_lft, max_rgt = frappe.db.sql("""select min(lft), max(rgt) from `tabAccount`
		where company=%s""", (filters.company,))[0]

	reporting_gls = {}
	open_reporting_gls = {}
	comparing_gls = {}
	open_comparing_gls = {}
	ignore_closing_entries = True

	if filters.report == "Financial Position":
		ignore_closing_entries = False
		open_reporting_gls = set_gl_entries_by_account(filters.cost_center, filters.company, '1900-01-01',
			filters.rep_to_date, min_lft, max_rgt, open_reporting_gls, ignore_closing_entries, open_date=filters.rep_from_date)
		open_comparing_gls = set_gl_entries_by_account(filters.cost_center, filters.company, '1900-01-01',
			filters.com_to_date, min_lft, max_rgt, open_comparing_gls, ignore_closing_entries, open_date=filters.com_from_date)
	else:
		ignore_closing_entries = True

	reporting_gls = set_gl_entries_by_account(filters.cost_center, filters.company, filters.rep_from_date,
		filters.rep_to_date, min_lft, max_rgt, reporting_gls, ignore_closing_entries)
	comparing_gls = set_gl_entries_by_account(filters.cost_center, filters.company, filters.com_from_date,
		filters.com_to_date, min_lft, max_rgt, comparing_gls, ignore_closing_entries)
	total_row = calculate_values(accounts, reporting_gls, comparing_gls, open_reporting_gls, open_comparing_gls, filters)
	accumulate_values_into_parents(accounts, accounts_by_name)

	data = prepare_data(accounts, filters, total_row, parent_children_map)
	data = filter_out_zero_value_rows(data, parent_children_map, show_zero_values=0)
	return data

def calculate_values(accounts, reporting_gls, comparing_gls, open_reporting_gls, open_comparing_gls, filters):
	init = {
		"reporting": 0.0,
		"comparing": 0.0,
		"variance": 0.0,
		"variance_percent": 0.0
	}

	total_row = {
		"account": None,
		"account_name": _("Total"),
		"warn_if_negative": True,
		"reporting": 0.0,
		"comparing": 0.0,
		"variance": 0.0
	}

	rep_income = rep_expense = com_income = com_expense = 0
	for d in accounts:
		d.update(init.copy())

		open_rep = open_com = 0
		if filters.report == "Financial Position":
			#opening data for reporting period
			for entry in (open_reporting_gls or {}).get(d.name, []):
			##	if cstr(entry.is_opening) != "Yes":
					if d.root_type == "Asset":
						open_rep += (flt(entry.debit, 3) - flt(entry.credit, 3))
					if d.root_type == "Liability":
						open_rep += (flt(entry.credit, 3) - flt(entry.debit, 3))
					if d.root_type == "Equity":
						open_rep += (flt(entry.credit, 3) - flt(entry.debit, 3))

			#opening data for comparing period
			for entry in (open_comparing_gls or {}).get(d.name, []):
			##	if cstr(entry.is_opening) != "Yes":
					if d.root_type == "Asset":
						open_com += (flt(entry.debit, 3) - flt(entry.credit, 3))
					if d.root_type == "Liability":
						open_com += (flt(entry.credit, 3) - flt(entry.debit, 3))
					if d.root_type == "Equity":
						open_com += (flt(entry.credit, 3) - flt(entry.debit, 3))

		#data for reporting period
		for entry in (reporting_gls or {}).get(d.name, []):
		##	if cstr(entry.is_opening) != "Yes":
				if d.root_type == "Expense":
					d["reporting"] += (flt(entry.debit, 3) - flt(entry.credit, 3))
					rep_expense += (flt(entry.debit, 3) - flt(entry.credit, 3))
				if d.root_type == "Income":
					d["reporting"] += (flt(entry.credit, 3) - flt(entry.debit, 3))
					rep_income += (flt(entry.credit, 3) - flt(entry.debit, 3))
				if d.root_type == "Asset":
					d["reporting"] += (flt(entry.debit, 3) - flt(entry.credit, 3))
				if d.root_type == "Liability":
					d["reporting"] += (flt(entry.credit, 3) - flt(entry.debit, 3))
				if d.root_type == "Equity":
					d["reporting"] += (flt(entry.credit, 3) - flt(entry.debit, 3))

		d["reporting"] += open_rep
		total_row["reporting"] = str(rep_income - rep_expense)

		#data for comparing period
		for entry in (comparing_gls or {}).get(d.name, []):
		##	if cstr(entry.is_opening) != "Yes":
				if d.root_type == "Expense":
					d["comparing"] += (flt(entry.debit, 3) - flt(entry.credit, 3))
					com_expense += (flt(entry.debit, 3) - flt(entry.credit, 3))
				if d.root_type == "Income":
					d["comparing"] += (flt(entry.credit, 3) - flt(entry.debit, 3))
					com_income += (flt(entry.credit, 3) - flt(entry.debit, 3))
				if d.root_type == "Asset":
					d["comparing"] += (flt(entry.debit, 3) - flt(entry.credit, 3))
				if d.root_type == "Liability":
					d["comparing"] += (flt(entry.credit, 3) - flt(entry.debit, 3))
				if d.root_type == "Equity":
					d["comparing"] += (flt(entry.credit, 3) - flt(entry.debit, 3))

		d["comparing"] += open_com
		total_row["comparing"] = str(com_income - com_expense)

		d["variance"] = flt(d["reporting"]) - flt(d["comparing"])

		d["variance_percent"] = "-"
		total_row["variance"] = flt(total_row["reporting"]) - flt(total_row["comparing"])

	if filters.report == "Financial Position":
		total_row = {}
	return total_row

def prepare_data(accounts, filters, total_row, parent_children_map):
	data = []
	for d in accounts:
		has_value = False
		row = {
			"account_number": d.account_number,
			"account_name": d.account_name,
			"account": d.name,
			"parent_account": d.parent_account,
			"indent": d.indent,
			"from_date": filters.rep_from_date,
			"to_date": filters.rep_to_date
		}

		for key in value_fields:
			row[key] = flt(d.get(key, 0.0), 3)

			if abs(row[key]) >= 0.005:
				# ignore zero values
				has_value = True
		row["has_value"] = has_value

		#Calculate Variance Percent
		if not d["comparing"] and not d["reporting"]:
			row["variance_percent"] = "100"
		elif not d["comparing"]:
			row["variance_percent"] = str(rounded((flt(d["variance"])/flt(d["variance"])) * 100, 2))
		else:
			row["variance_percent"] = str(rounded((flt(d["variance"])/flt(d["comparing"])) * 100, 2))
		data.append(row)

	data.extend([{},total_row])

	return data

def accumulate_values_into_parents(accounts, accounts_by_name):
	for d in reversed(accounts):
		if d.parent_account:
			for key in value_fields:
				accounts_by_name[d.parent_account][key] += d[key]

def validate_filters(filters):
	if filters.rep_fy < filters.com_fy:
		frappe.throw("Reporting Fiscal Year should be greater than Comparision Fiscal Year")

	from_month = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov",
		"Dec"].index(filters.from_date) + 1
	to_month = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov",
		"Dec"].index(filters.to_date) + 1
	if from_month > to_month:
		frappe.throw("From Month Cannot be greater than To Month")
	else:
		rep_last_day = monthrange(cint(filters.rep_fy), to_month)[1]
		com_last_day = monthrange(cint(filters.com_fy), to_month)[1]
		if to_month in [1,2,3,4,5,6,7,8,9]:
			to_month = "0" + str(to_month)
		if from_month in [1,2,3,4,5,6,7,8,9]:
			from_month = "0" + str(from_month)
		if from_month in [1,2,3,4,5,6,7,8,9]:
			from_month = "0" + str(from_month)
		filters.rep_to_date = str(filters.rep_fy) + "-" + str(to_month) + "-" + str(rep_last_day)
		filters.rep_from_date = str(filters.rep_fy) + "-" + str(from_month) + "-01"

		filters.com_to_date = str(filters.com_fy) + "-" + str(to_month) + "-" + str(com_last_day)
		filters.com_from_date = str(filters.com_fy) + "-" + str(from_month) + "-01"

	return filters

def get_columns():
	return [
		{
			"fieldname": "account",
			"label": _("Account"),
			"fieldtype": "Link",
			"options": "Account",
			"width": 300
		},
		{
			"fieldname": "account_number",
			"label": _("Account Code"),
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "reporting",
			"label": _("Reporting Data"),
			"fieldtype": "Currency",
			"width": 170
		},
		{
			"fieldname": "comparing",
			"label": _("Comparision Data"),
			"fieldtype": "Currency",
			"width": 170
		},
		{
			"fieldname": "variance",
			"label": _("Variance"),
			"fieldtype": "Currency",
			"width": 170
		},
		{
			"fieldname": "variance_percent",
			"label": _("Var. Percent"),
			"fieldtype": "Data",
			"width": 100
		}
	]
