# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
import os
from frappe.utils.data import get_first_day, get_last_day, add_years, date_diff, now, today, getdate
from frappe.utils import getdate, get_datetime, now, cint, flt

def execute(filters=None):
	data = []
	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data

def get_data(filters):
	cond = ''
	if filters.get('cost_center'):
		cond = " and cost_center='{}'".format(filters.get('cost_center'))
	if filters.get('month') and filters.get('fiscal_year'):
		if filters.get('month') == "01":
			from_date = filters.get('fiscal_year')+ "-" + filters.get('month') + "-" + "02"
		else:
			from_date = filters.get('fiscal_year')+ "-" + filters.get('month') + "-" + "01"
		to_date = get_last_day(from_date)

	accounts = ""
	if filters.get('asset_category'):
		for row in frappe.db.sql("""
					select 
						accumulated_depreciation_account, 
						depreciation_expense_account
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
						and voucher_type != "Asset Movement"
						and account in {accounts}
						and posting_date between "{from_date}" and "{to_date}"
						{cond}
						and voucher_no not in (
							select journal_entry_for_scrap from tabAsset where disposal_date between "{from_date}" and "{to_date}"
						)
						and voucher_no not in ( select name from `tabJournal Entry` where docstatus=1 and reverse_jv = 1 ) 
						group by account, cost_center 
						order by cost_center
					""".format(accounts=accounts, from_date=from_date, to_date=to_date, cond=cond), as_dict=True):
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

@frappe.whitelist()
def generate_download_file(fiscal_year=None, month=None, asset_category=None, cost_center=None):
	filters = {}
	filters["fiscal_year"] = str(fiscal_year)
	filters["month"] = str(month)
	filters['asset_category'] = str(asset_category)
	filters['cost_center'] = str(cost_center)
	data = get_data(filters)
	file_name = "Dep-" + str(filters.get('asset_category'))+"-"+str(filters.get('month'))+"-"+str(filters.get('fiscal_year'))+".txt"
	dep_dir = os.path.join(frappe.get_site_path("public", "files"), "dep")
	os.makedirs(dep_dir, exist_ok=True)
	file_path = os.path.join(dep_dir, file_name)
	line_number=1
	remarks = str(filters.get('asset_category'))+" "+str(filters.get('month'))+"-"+str(filters.get('fiscal_year'))
	for fd in data:
		if fd['credit'] > 0:
			amount = flt(fd['credit'],2)
			credit_debit = "C"
		else:
			amount = flt(fd['debit'],2)
			credit_debit = "D"

		if line_number == 1:
			with open(file_path, 'w') as file:
				#Write Mode
				file.write(fd["account_number"]+f"{' '*(16-len(str(fd['account_number'])))}BTN000     " + credit_debit + f"""{' '*(17-len(str(format(flt(amount,2),'.2f'))))}{str(format(flt(amount,2),'.2f'))}"""+remarks)
		else:
			with open(file_path, 'a') as file:
				# Append Mode to the file
				file.write("\n"+fd["account_number"]+f"{' '*(16-len(str(fd['account_number'])))}BTN000     " + credit_debit + f"""{' '*(17-len(str(format(flt(amount,2),".2f"))))}{str(format(flt(amount,2),'.2f'))}"""+remarks)
		line_number += 1
	
	with open(file_path, "rb") as f:
		file_content = f.read()

	frappe_file = frappe.get_doc({
		"doctype": "File",
		"file_name": file_name,
		"is_private": 0, 
		"content": file_content,
	})
	frappe_file.insert(ignore_permissions=True)

	file_url = frappe_file.file_url

	if os.path.exists(file_path):
		os.remove(file_path)

	return {"file_url": file_url}

