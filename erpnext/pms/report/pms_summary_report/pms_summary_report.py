# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe

def execute(filters=None):
	columns, data = get_colums(), get_data(filters)
	return columns, data

def get_data(filters):
	conds = get_condition(filters)
	return frappe.db.sql('''
		SELECT name as reference,employee,
			employee_name,branch,
			designation, gender,
			supervisor_name, pms_group,
			pms_calendar, posting_date,
			total_score,final_rating
		FROM `tabPMS Summary`
		WHERE docstatus = 1 
		{}
	'''.format(conds))
def get_condition(filters):
	conds = ''
	if filters.branch:
		conds += " and branch = '{}' ".format(filters.branch)
	if filters.region:
		conds += " and region = '{}' ".format(filters.region)
	if filters.pms_calendar:
		conds += " and pms_calendar = '{}' ".format(filters.pms_calendar)
	if filters.pms_group:
		conds += " and pms_group = '{}' ".format(filters.pms_group)
	if filters.gender:
		conds += " and gender = '{}' ".format(filters.gender)
	if filters.rating:
		conds += " and final_rating = '{}' ".format(filters.rating)
	return conds
def get_colums():
	return [
		{
			"fieldname":"reference",
			"label":"Reference",
			"fieldtype":"Link",
			"options":"PMS Summary",
			"width":100
		},
		{
			"fieldname":"employee",
			"label":"Employee ID",
			"fieldtype":"Link",
			"options":"Employee",
			"width":100
		},
		{
			"fieldname":"employee_name",
			"label":"Employee Name",
			"fieldtype":"Data",
			"width":120
		},
		{
			"fieldname":"branch",
			"label":"Branch",
			"fieldtype":"Link",
			"options":"Branch",
			"width":130
		},
		{
			"fieldname":"desination",
			"label":"Designation",
			"fieldtype":"Link",
			"options":"Designation",
			"width":100
		},
		{
			"fieldname":"gender",
			"label":"Gender",
			"fieldtype":"Data",
			"width":100
		},
		{
			"fieldname":"supervisor_name",
			"label":"Supervisor Name",
			"fieldtype":"Data",
			"width":130
		},
		{
			"fieldname":"pms_group",
			"label":"PMS Group",
			"fieldtype":"Link",
			"options":"PMS Group",
			"width":100
		},
		{
			"fieldname":"pms_calendar",
			"label":"PMS Calendar",
			"fieldtype":"Link",
			"options":"PMS Calendar",
			"width":100
		},
		{
			"fieldname":"posting_date",
			"label":"Posting Date",
			"fieldtype":"Date",
			"width":100
		},
		{
			"fieldname":"total_score",
			"label":"Total Score",
			"fieldtype":"Float",
			"width":100
		},
		{
			"fieldname":"final_rating",
			"label":"Rating",
			"fieldtype":"Link",
			"options":"Overall Rating",
			"width":150
		},
	]