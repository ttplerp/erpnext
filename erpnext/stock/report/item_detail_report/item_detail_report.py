# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import msgprint, _


def execute(filters=None):
	columns, data = [], []
	columns = get_columns(data)
	data = get_data(filters)
	
	return columns, data

def get_columns(data):
	return [
		_("Item Code") + ":Link/Item:100", 
		_("Item Name") + ":Data:200", 
		_("Item Group") + ":Data:200", 
		_("Item Sub Group") + ":Date:200",
		_("UOM")+":Link/UOM:100", 
		_("Default Expense Account") + ":Link/Account:200",
		_("Default Income Account") + ":Link/Account:200",

	]
def get_data(filters):
	data = frappe.db.sql("""
			select i.item_old_code as item_old_code, i.item_name as item_name, i.item_group as item_group, i.item_sub_group as item_sub_group, i.stock_uom as stock_uom, id.expense_account as expense_account, id.income_account as income_account 
			from `tabItem` i
			inner join `tabItem Default` id on id.parent = i.name
			where i.disabled != 1 
		""")
	return data