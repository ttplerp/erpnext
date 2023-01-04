# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _

def execute(filters=None):
	columns=get_columns()
	data = get_data(filters)
	return columns, data

def get_columns():
	return [
		("Posting Date") + ":Date:140",
		("Branch") + ":Link/Branch:130",
		("Equipment") + ":Link/Equipment:100",
		("Equipment No.") + ":Data:100",
		("Service Type") + ":Data:100",
		("Code") + ":Dynamic Link/"+_("Service Type")+":100",
		("Name") + ":Data:120",
		("Amount") + ":Currency:100",
		("Qty") + ":Data:70",
		("Job Card") + ":Link/Job Card:100"
	]	
	


def get_data(filters=None):
	query = """ select j.posting_date as posting_date, j.branch as branch, j.equipment as equipment, j.equipment_number as equipment_number, 
		i.which as service_type, i.job as job, i.job_name as job_name, i.amount as amount, i.quantity as qty, j.name as name 
		from `tabJob Card` j inner join `tabJob Card Item` i on j.name = i.parent where j.docstatus = 1 """


	if filters.from_date and filters.to_date:
		query += " and j.posting_date between \'" + str(filters.from_date) + "\' and \'" + str(filters.to_date) + "\'"

	if filters.branch:
		query += " and j.branch = \'" + str(filters.branch) + "\'"
	
	if filters.equipment:
		query += " and j.equipment = \'" + str(filters.equipment) + "\'"
		
	query += " order by `posting_date` desc"
	data = frappe.db.sql(query)
	
	return data
