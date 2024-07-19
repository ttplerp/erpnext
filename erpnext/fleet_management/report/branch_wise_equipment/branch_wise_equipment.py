# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	columns, data = get_columns(filters), get_data(filters)
	return columns, data

def get_columns(filters):
	return [
			{
				"fieldname":"branch",
				"label":"Branch",
				"fieldtype":"data",
				"options":"",
				"width":160
			},
   {
				"fieldname":"number",
				"label":"Number",
				"fieldtype":"data",
				"options":"",
				"width":160
			},

   
		]

def get_data(filters):
	data = []
	
	data = frappe.db.sql('''
						select branch, count(name) as number from `tabEquipment` group by branch;''',as_dict=1)
	
	return data
