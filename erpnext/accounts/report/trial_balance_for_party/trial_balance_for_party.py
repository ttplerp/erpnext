# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt, cint
from erpnext.accounts.report.trial_balance.trial_balance import validate_filters

def execute(filters=None):
	validate_filters(filters)
	check_accounts(filters)

	show_party_name = is_party_name_visible(filters)
	
	columns = get_columns(filters, show_party_name)
	data = get_data(filters, show_party_name)

	return columns, data

def get_data(filters, show_party_name):
	party_name_field = "customer_name" if filters.get("party_type")=="Customer" else "supplier_name" if filters.get("party_type")=="Supplier" else "employee_name"
	if not filters.get("inter_company"):
		parties = frappe.get_all(filters.get("party_type"), fields = ["name", party_name_field], order_by="name")
	elif filters.get("party_type") == "Employee":
		parties = frappe.get_all(filters.get("party_type"), fields = ["name", party_name_field], order_by="name")
	else:
		parties = frappe.get_all(filters.get("party_type"), fields = ["name", party_name_field], filters = {"inter_company": 1}, order_by="name")
	
	company_currency = frappe.db.get_value("Company", filters.company, "default_currency")

	party_balances = get_balances(filters)

	data = []
	tot_op_dr, tot_op_cr, total_debit, total_credit, tot_cl_dr, tot_cl_cr = 0, 0, 0, 0, 0, 0
	for party in parties:
		if party_balances.get(party.name):
			for cc, values in party_balances.get(party.name).items():
				row = {"party": party.name, "cost_center": cc}
				opening_debit, opening_credit, debit, credit, project = values
				
				if show_party_name:
					row["party_name"] = party.get(party_name_field)

				tot_op_dr += flt(opening_debit)
				tot_op_cr += flt(opening_credit)

				row.update({"opening_debit": opening_debit, "opening_credit": opening_credit, "debit": debit, "credit": credit})
				
				# totals
				total_debit += debit
				total_credit += credit
				
				# closing
				closing_debit, closing_credit = toggle_debit_credit(opening_debit + debit, opening_credit + credit)
				row.update({
					"closing_debit": closing_debit,
					"closing_credit": closing_credit
				})

				tot_cl_dr += flt(closing_debit)
				tot_cl_cr += flt(closing_credit)
				
				row.update({
					"currency": company_currency,
					"project": project
				})
				
				has_value = False
				if (opening_debit or opening_credit or debit or credit or closing_debit or closing_credit):
					has_value  =True
				
				if cint(filters.show_zero_values) or has_value:
					data.append(row)

	# Add total row
	if total_debit or total_credit:
		data.append({
			"party": "'" + _("Totals") + "'",
			"opening_debit": tot_op_dr,
			"opening_credit": tot_op_cr,
			"debit": total_debit,
			"credit": total_credit,
			"currency": company_currency,
			"closing_debit": tot_cl_dr,
			"closing_credit": tot_cl_cr
		})
	
	return data

def get_balances(filters):
	filters.accounts    = None if filters.get("accounts") == '%' else filters.get("accounts")
	filters.cost_center = None if filters.get("cost_center") == '%' else filters.get("cost_center")
	filters.project = None if filters.get("project") == '%' else filters.get("project")
	
	cond = ""
	cond += " and account = '{0}'".format(filters.accounts) if filters.get("accounts") else ""
	cond += " and cost_center = '{0}'".format(filters.cost_center) if filters.get("cost_center") else ""
	cond += " and project = '{0}'".format(filters.project) if filters.get("project") else ""
	sql = """
		select
			{group_by} as cost_center, project,
			sum(case when ifnull(is_opening, 'No') = 'Yes' or posting_date < '{from_date}' then ifnull(debit,0) else 0 end) as opening_debit,
			sum(case when ifnull(is_opening, 'No') = 'Yes' or posting_date < '{from_date}' then ifnull(credit,0) else 0 end) as opening_credit,
			sum(case when ifnull(is_opening, 'No') = 'No' and posting_date between '{from_date}' and '{to_date}' then ifnull(debit,0) else 0 end) as debit,
			sum(case when ifnull(is_opening, 'No') = 'No' and posting_date between '{from_date}' and '{to_date}' then ifnull(credit,0) else 0 end) as credit
		from `tabGL Entry` as ge
		where company='{company}' 
		and ifnull(party_type, '') = '{party_type}' and ifnull(party, '') != ''
		and posting_date <= '{to_date}'
		and is_cancelled = 0
		{cond}
		group by {group_by}""".format(
					company = filters.company,
					from_date = filters.from_date,
					to_date = filters.to_date,
					party_type = filters.party_type,
					group_by = "party,''" if filters.get("group_by_party") else "party, cost_center",
					cond = cond
			)
	gle = frappe.db.sql(sql, as_dict=True)
	
	balances = frappe._dict()
	for d in gle:
		opening_debit, opening_credit = toggle_debit_credit(d.opening_debit, d.opening_credit)
		balances.setdefault(d.party, frappe._dict()).setdefault(d.cost_center, [opening_debit, opening_credit, flt(d.debit), flt(d.credit), d.project])
	return balances
	
def toggle_debit_credit(debit, credit):
	if flt(debit) > flt(credit):
		debit = flt(debit) - flt(credit)
		credit = 0.0
	else:
		credit = flt(credit) - flt(debit)
		debit = 0.0
		
	return debit, credit
	
def get_columns(filters, show_party_name):
	columns = [
		{
			"fieldname": "party",
			"label": _(filters.party_type),
			"fieldtype": "Link",
			"options": filters.party_type,
			"width": 200
		},
		{
			"fieldname": "opening_debit",
			"label": _("Opening (Dr)"),
			"fieldtype": "Currency",
			"options": "currency",
			"width": 120
		},
		{
			"fieldname": "opening_credit",
			"label": _("Opening (Cr)"),
			"fieldtype": "Currency",
			"options": "currency",
			"width": 120
		},
		{
			"fieldname": "debit",
			"label": _("Debit"),
			"fieldtype": "Currency",
			"options": "currency",
			"width": 120
		},
		{
			"fieldname": "credit",
			"label": _("Credit"),
			"fieldtype": "Currency",
			"options": "currency",
			"width": 120
		},
		{
			"fieldname": "closing_debit",
			"label": _("Closing (Dr)"),
			"fieldtype": "Currency",
			"options": "currency",
			"width": 120
		},
		{
			"fieldname": "closing_credit",
			"label": _("Closing (Cr)"),
			"fieldtype": "Currency",
			"options": "currency",
			"width": 120
		},
		{
			"fieldname": "currency",
			"label": _("Currency"),
			"fieldtype": "Link",
			"options": "Currency",
			"hidden": 1
		}
	]
	
	if show_party_name:
		columns.insert(1, {
			"fieldname": "party_name",
			"label": _(filters.party_type) + " Name",
			"fieldtype": "Data",
			"width": 200
		})

	if not filters.get("group_by_party"):
		columns.append({
			"fieldname": "cost_center",
			"label": _("Cost Center"),
			"fieldtype": "Link",
			"options": "Cost Center",
			"width": 200
		})
		columns.append({
			"fieldname": "project",
			"label": _("Project"),
			"fieldtype": "Link",
			"options": "Project",
			"width": 200
		})
	return columns
		
def is_party_name_visible(filters):
	if filters.get("party_type") == "Employee":
		return True

	show_party_name = False
	if filters.get("party_type") == "Customer":
		party_naming_by = frappe.db.get_single_value("Selling Settings", "cust_master_name")
	else:
		party_naming_by = frappe.db.get_single_value("Buying Settings", "supp_master_name")
		
	if party_naming_by == "Naming Series":
		show_party_name = True
		
	return show_party_name

def check_accounts(filters):
	if not filters.accounts:
		filters.accounts = '%'
