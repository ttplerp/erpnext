# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import flt, cstr
from frappe import msgprint, _

def execute(filters=None):
	columns, data = [], []
	data = get_data(filters)
	if not data:
		return columns, data
		
	columns = get_columns(data)

	return columns, data

def get_columns(data):
	columns = [
		_("Transaction Date") + "::150",
		_("Against Voucher") + "::200",
		_("Voucher Type") + "::160",
		_("Voucher No") + "::150",
		_("Debit") + ":Currency:150",
		_("Credit") + ":Currency:150",
		_("Branch") + "::200",
	]
	return columns

def get_data(filters):
	data = []
	total_opening=total_closing=total_credit=total_debit=0.00
	adv_account = frappe.db.get_value("Company",filters.get('company'), 'salary_advance_account')
	open_bal = frappe.db.sql("""
							select sum(debit)-sum(credit) as opening_balance 
							from `tabGL Entry`
							where account ="{0}"
							and party = "{1}" and party_type="Employee"
							and posting_date < "{2}"
							and is_cancelled != 1
				""".format(adv_account, filters.get("employee"), filters.get('from_date')), as_dict=True)[0]
	bda_open = frappe.db.sql("""
							select sum(amount) as advance
							from `tabBatch Data Communication` a inner join 
							`tabBatch Data Communication Item` b on a.name=b.parent
							where a.docstatus=1 
							and b.employee="{0}"
							and a.to_date < "{1}" 
				""".format(filters.get("employee"), filters.get('from_date')), as_dict=True)[0]

	data.append({
			"transaction_date":filters.get("from_date"),
			"against_voucher": "",
			"voucher_type": "Opening Balance",
			"voucher_no": "",
			"debit": flt(open_bal['opening_balance'],2) + flt(bda_open['advance'],2),
			"credit":"",
			"branch":""
		})
	for a in frappe.db.sql("""
						(select debit, credit, posting_date, voucher_type, voucher_no,
							against_voucher_type, against_voucher, cost_center as cc_branch 
							from `tabGL Entry`
							where account ="{0}"
							and party = "{1}" and party_type="Employee"
							and posting_date between "{2}" and "{3}"
							and is_cancelled != 1)
							union
						(select b.amount as debit, 0.00 as credit, a.from_date as posting_date, 
							"Batch Data" as voucher_type, a.name as voucher_no, 
							"Batch Data" as against_voucher_type, a.name as against_voucher, branch as cc_branch
							from `tabBatch Data Communication` a inner join 
							`tabBatch Data Communication Item` b on a.name=b.parent
							where a.docstatus=1 
							and b.employee="{1}"
							and a.to_date between "{2}" and "{3}")
						order by posting_date
				""".format(adv_account, filters.get("employee"), filters.get('from_date'),  filters.get('to_date')), as_dict=True):

		data.append({
			"transaction_date":a.posting_date,
			"against_voucher": a.against_voucher_type,
			"voucher_type": a.voucher_type,
			"voucher_no": a.voucher_no,
			"debit": flt(a.debit,2),
			"credit": flt(a.credit,2),
			"branch": a.cc_branch,
		})
		total_debit += flt(a.debit,2)
		total_credit += flt(a.credit,2)
	total_closing = (flt(open_bal['opening_balance'],2) + flt(total_debit,2)) - flt(total_credit,2)
	data.append({
			"transaction_date":"",
			"against_voucher": "",
			"voucher_type": "Total",
			"voucher_no": "",
			"debit": total_debit,
			"credit": total_credit,
			"branch":""
		})
	data.append({
			"transaction_date":"",
			"voucher_type": "Closing Balance",
			"voucher_no": "",
			"against_voucher": "",
			"debit": flt(total_closing,2),
			"credit":"",
			"branch":""
		})
	return data