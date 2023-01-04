# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _

def execute(filters=None):
	columns, data = get_columns(filters), get_data(filters)
	return columns, data

def get_columns(filters):
	columns = [
			 _("Reimbursement") + ":Link/Reimbursement:150", 
			 _("Branch") + ":Link/Branch:150", 
			 _("Cost Center") + ":Data:150",
			 _("Posting Date") + ":Date:100",
			 _("Purpose") + ":Data:150",
			 _("Expense Account") + ":Link/Account:180",
			 _("Type") + ":Data:90",
			 _("Amount") + ":Currency:100",
			 _("Journal Entry") + ":Link/Journal Entry:120",
			 _("Credit Account") + ":Link/Account:180",
			 _("Party Type") + ":Data:120",
			 _("Party") + ":Link/Employee:120",
			 _("Remarks") + ":Data:200"

	]
	return columns

def get_data(filters):
	if not filters.from_date or not filters.to_date:
		return
	data = frappe.db.sql("""
			select name, branch, cost_center, posting_date, purpose, expense_account, type, amount, journal_entry, credit_account,
				party_type, party, remarks
			from `tabReimbursement`
			where posting_date between '{from_date}' and '{to_date}' and docstatus = 1
			""".format(from_date=filters.from_date, to_date=filters.to_date))
	
	return data
