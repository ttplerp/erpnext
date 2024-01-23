# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe

def execute(filters=None):
	columns, data = get_column(), get_data(filters)
	return columns, data

def get_column():
    columns = [
		("eNote") + ":Link/eNote:100",
		("Dispatch Number") + ":Data:200",
        ("eNote Type") + ":Data:150",
		("eNote Category") + ":Data:150",
        ("Posting Date") + ":Date:120",
        ("Approver") + ":Link/User:200",
        ("owner") + ":Link/User:200",
    ]
    return columns

def get_data(filters):
    cond = get_condition(filters)
    return frappe.db.sql("""
		SELECT 
			name,
			enote_format,
			enote_type, 
			category,
			note_date,
			permitted_user, 
			owner
		FROM `tabeNote`
		WHERE docstatus = 1 {condition}
	""".format(condition=cond))
    
def get_condition(filters):
    conds = ""
    if filters.enote_type:
        conds += "and enote_type='{}'".format(filters.enote_type)
    if filters.category:
        conds += "and category='{}'".format(filters.category)
    return conds