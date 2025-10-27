# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils.data import get_first_day, get_last_day, add_years, date_diff, now, today, getdate

def execute(filters=None):
	data = []
	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data

def get_data(filters):
	if filters.get('month') and filters.get('fiscal_year'):
		from_date = filters.get('fiscal_year')+ "-" + filters.get('month') + "-" + "01"
		to_date = get_last_day(from_date)

	accounts = ""
	if filters.get('asset_category'):
		for row in frappe.db.sql("""
					select 
						fixed_asset_account, 
						accumulated_depreciation_account, 
						depreciation_expense_account, 
						credit_account
					from `tabAsset Category Account`
					where parent="{}"
					""".format(filters.get('asset_category')), as_dict=True):
			accounts = '("' + str(row.fixed_asset_account) + '", "'+ str(row.accumulated_depreciation_account) + '", "' + str(row.depreciation_expense_account) + '", "' + str(row.credit_account) + '")'
	data=[]
	for a in frappe.db.sql("""select 
						account, 
						sum(credit) as credit, sum(debit) as debit, 
						cost_center, posting_date 
						from `tabGL Entry` 
						where docstatus=1
						and is_cancelled=0 
						and account in {accounts}
						and posting_date between "{from_date}" and "{to_date}" 
						group by account, cost_center 
						order by cost_center
					""".format(accounts=accounts, from_date=from_date, to_date=to_date), as_dict=True):
		cc_number = frappe.db.get_value("Cost Center",a.cost_center,"cost_center_number")
		account_no = str(cc_number) + str(frappe.db.get_value("Account",a.account,"account_number"))
		data.append({
			"account": a.account,
			"credit": a.credit,
			"debit": a.debit,
			"cost_center": a.cost_center,
			"branch_code": cc_number,
			"account_number": account_no,
			"posting_date": a.posting_date
		})
	return data	

def get_columns(filters):
	columns = [
		{
			"fieldname": "account",
			"label": _("Account"),
			"fieldtype": "Link",
			"options": "Account",
			"width": 300
		},
		{
			"fieldname": "account_number",
			"label": _("Account Number"), #Branch Code + GL Code
			"fieldtype": "Data",
			"width": 130
		}, 
		{
			"fieldname": "debit",
			"label": _("Debit"),
			"fieldtype": "Currency",
			"width": 150
		}, 
		{
			"fieldname": "credit",
			"label": _("Credit"),
			"fieldtype": "Currency",
			"width": 150
		},
		{
            "fieldname": "cost_center",
            "label": _("Cost Center"),
            "fieldtype": "Link",
            "options": "Cost Center",
            "width": 280
        },
		{
			"fieldname": "posting_date",
			"label": _("Posting Date"),
			"fieldtype": "Data",
			"width": 110
		},
		{
			"fieldname": "branch_code",
			"label": _("Branch Code"),
			"fieldtype": "Data",
			"width": 90
		},
	]
	return columns
