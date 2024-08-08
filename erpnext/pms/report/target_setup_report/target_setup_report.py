# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _

def execute(filters=None):
	columns = get_column(filters)
	data = get_data(filters)
	return columns, data

	
	
def get_data(filters):
	cond = get_conditions(filters)	
	query = """
		select 
				name,
				employee_name,
                grade,
				pms_group,
				designation,
				pms_calendar,
				start_date,
				end_date,
				supervisor_name,
                
               
				
			"""
	if filters.type == "Target Setup Report":
		query += "from `tabTarget Set Up` {}".format(cond)

	if filters.type == "Review Report":
		query += "from `tabReview` {}".format(cond)

	if filters.type == "Performance Evaluation Report":
		query += "final_score from `tabPerformance Evaluation` {}".format(cond)	
	
	# frappe.msgprint(format(query))
	data = frappe.db.sql(query)
	return data



def get_column(filters):
	columns = [
					
					_("Employee Name") + ":Data:120",
                    _("Grade") + ":Data:120",
					_("PMS Group") + ":Data:120",
					_("Designation") + ":Data:120",			
					_("PMS Calender") + ":Data:120",
					_("Start Date") + ":Date:120",
					_("End Date") + ":Date:120",
					_("Supervisor") + ":Data:120"					
					# _("Status") + ":Data:120"				
					
	]		
	if filters.get("type") == "Target Setup Report":		
		columns.insert(0,_("Name") + ":Link/Target Set Up:120")	

	if filters.get("type") == "Review Report":		
		columns.insert(0,_("Name") + ":Link/Review:120")

	if filters.get("type") == "Performance Evaluation Report":		
		columns.insert(0,_("Name") + ":Link/Performance Evaluation:120")
		columns.insert(9,_("Final Score") + ":Data:120")
                  			
	return columns



def get_conditions(filters):
	cond = ""
	if filters.pms_calendar:
		cond += " where pms_calendar='{}'".format(filters.pms_calendar)
	
	if filters.docstatus == "Submitted":
		cond += " and docstatus = 1"
	elif filters.docstatus == "Draft":
		cond += " and docstatus = 0"

	if filters.Branch:
		cond += " and branch='{}'".format(filters.Branch)	
		
		
	return cond

	
