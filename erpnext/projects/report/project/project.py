# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	columns, data = get_columns(filters), get_data(filters)
	return columns, data

def get_columns(filters):
    return [
			{
				"fieldname":"project_name",
				"label":"Project Name",
				"fieldtype":"data",
				"options":"",
				"width":160
			},
   {
				"fieldname":"percent_complete",
				"label":"percent_complete",
				"fieldtype":"data",
				"options":"",
				"width":160
			},
		]

def get_data(filters):
	data = []
	data = frappe.db.sql('''
						select project_name, percent_complete from `tabProject`''',as_dict=1)
	return data