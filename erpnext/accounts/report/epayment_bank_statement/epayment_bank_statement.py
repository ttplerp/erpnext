# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe

def execute(filters=None):
	columns, data = [], []
	columns = get_columns()
	data = get_data(filters)

	return columns, data

def get_columns():
	return [
		("Transaction Date") + ":Date:130",
		("Account") + ":Data:130",
		("Amount") + ":Currency:150",
		("Reference No.") + ":Data:150",
		("Journal No.") + ":Data:110",
		("Narration") + ":Data:255",
		("Reconciled") + ":Data:70"
	]

def get_data(filters):
	condition = ""
	if filters.get("account"):
		bank_account_no = frappe.db.get_value("Account", filters.get("account"), "bank_account_no")
		condition = " and account='{}'".format(bank_account_no)
	
	if filters.get("company"):
		condition = " and company = '{}'".format(filters.get("company"))

	if filters.get("from_date") and filters.get("to_date"):
		condition = " and clearing_date between '{}' and '{}' ".format(filters.get("from_date"), filters.get("to_date"))
	
	if filters.get("payment_type"):
		if filters.get("payment_type") == "Payment":
			condition = " and amount < 0"
		else:
			condition = " and amount > 0"

	query = """ select clearing_date, account_no, amount, ref_no, jrnl_no, narration, 
				CASE WHEN reconciled = 0 THEN "No" ELSE "Yes" END
				from `tabBRS Entries`
				where docstatus = 1
				{condition}
		""".format(condition = condition)
	
	return frappe.db.sql(query)