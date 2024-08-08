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
                employee,
                pms_group,
                designation,
                pms_calendar,
                approver_name,
                department,
                division,
                region,
                unit,
                section               
            """
    if filters.type == "Target Setup Report":
        query += ",date from `tabTarget Set Up` {}".format(cond)

    if filters.type == "Review Report":
        query += ",review_date from `tabReview` {}".format(cond)

    if filters.type == "Performance Evaluation Report":
        query += ", date_of_joining, reason, evaluation_date, form_i_total_rating, form_ii_total_rating, form_i_score, form_ii_score, final_score, final_score_percent, overall_rating from `tabPerformance Evaluation` {}".format(cond)	
        
    if filters.type == "PMS Summary":
        query += ", date_of_joining, posting_date, form_i_total_rating, form_ii_total_rating, form_i_score, form_ii_score, final_score, final_score_percent, overall_rating from `tabPMS Summary` {}".format(cond)
    
    # frappe.throw(str(query))
    data = frappe.db.sql(query)
    return data

def get_column(filters):
    columns = [
                _("Employee Name") + ":Data:120",
                _("Employee ID") + ":Data:120",
                _("PMS Group") + ":Data:120",
                _("Designation") + ":Data:120",			
                _("PMS Calender") + ":Data:120",
                _("Supervisor") + ":Data:120",
                _("Department") + ":Link/Department:120",
                _("Division") + ":Link/Division:120",
                _("Region") + ":Link/Region:120",
                _("Unit") + ":Link/Unit:120",
                _("Section") + ":Link/Section:120",
                
    ]		
    if filters.get("type") == "Target Setup Report":		
        columns.insert(0,_("Reference") + ":Link/Target Set Up:120"),
        columns.append(("Posting Date") + ":Data:120")		

    if filters.get("type") == "Review Report":		
        columns.insert(0,_("Reference") + ":Link/Review:120"),
        columns.append(("Posting Date") + ":Data:120")	
       
    if filters.get("type") == "Performance Evaluation Report":		
        columns.insert(0,_("Reference") + ":Link/Performance Evaluation:120"),
        columns.append(("Date Of Joining") + ":Date:100"),
        columns.append(("Reason") + ":Data:100"),
        columns.append(("Posting Date") + ":Data:100"),
        columns.append(("Form I Total Rating") + ":Float:100"),				
        columns.append(("Form II Total Rating") + ":Float:100"),		
        columns.append(("Form I Score") + ":Float:100"),				
        columns.append(("Form II Score") + ":Float:100"),				
        columns.append(("Final Score") + ":Float:100"),
        columns.append(("Final Score(%)") + ":Float:100"),				
        columns.append(("Overall Rating") + ":Link/Overall Rating:150")
        
    if filters.get("type") == "PMS Summary":		
        columns.insert(0,_("Reference") + ":Link/PMS Summary:120"),
        columns.append(("Date Of Joining") + ":Date:100"),
        columns.append(("Posting Date") + ":Data:100"),
        columns.append(("Form I Total Rating") + ":Float:100"),				
        columns.append(("Form II Total Rating") + ":Float:100"),		
        columns.append(("Form I Score") + ":Float:100"),				
        columns.append(("Form II Score") + ":Float:100"),				
        columns.append(("Final Score") + ":Float:100"),
        columns.append(("Final Score(%)") + ":Float:100"),				
        columns.append(("Overall Rating") + ":Link/Overall Rating:150")
                    
                           
    return columns

def get_conditions(filters):
    cond = ""
    if filters.pms_calendar:
        cond += " where pms_calendar='{}'".format(filters.pms_calendar)
    
    if filters.type == "Target Setup Report":
        if filters.workflow_state == "Draft":
            cond += " and workflow_state = 'Draft'"
        elif filters.workflow_state == "Waiting Approval":
            cond += " and workflow_state = 'Waiting Approval'"
        elif filters.workflow_state == "Approved":
            cond += " and workflow_state = 'Approved'"
        elif filters.workflow_state == "Rejected":
            cond += " and workflow_state = 'Rejected'"

    elif filters.type == "Review Report":
        if filters.workflow_state == "Draft":
            cond += " and rev_workflow_state = 'Draft'"
        elif filters.workflow_state == "Waiting Approval":
            cond += " and rev_workflow_state = 'Waiting Approval'"
        elif filters.workflow_state == "Approved":
            cond += " and rev_workflow_state = 'Approved'"
        elif filters.workflow_state == "Rejected":
            cond += " and rev_workflow_state = 'Rejected'"
    
    elif filters.type == "Performance Evaluation Report":
        if filters.workflow_state == "Draft":
            cond += " and eval_workflow_state = 'Draft'"
        elif filters.workflow_state == "Waiting Approval":
            cond += " and (eval_workflow_state = 'Waiting Approval' or eval_workflow_state = 'Waiting Supervisor Approval' or eval_workflow_state = 'Waiting PERC')"
        elif filters.workflow_state == "Approved":
            cond += " and eval_workflow_state = 'Approved'"
        elif filters.workflow_state == "Rejected":
            cond += " and eval_workflow_state = 'Rejected'"

    elif filters.type == "PMS Summary":
        if filters.docstatus == "Draft":
            cond += " and docstatus = 0"
        elif filters.docstatus == "Submitted":
            cond += " and docstatus = 1"

    if filters.department:
        cond += " and department='{}' ".format(filters.department)
    if filters.branch:
        cond += " and branch='{}'".format(filters.branch)	
    if filters.division:
        cond += " and division = '{}'".format(filters.division)
    if filters.region:
        cond += " and region = '{}'".format(filters.region)
    if filters.unit:
        cond += " and unit = '{}'".format(filters.unit)
    if filters.from_date:
        cond += " and date_of_joining >= '{}'".format(filters.from_date)
    if filters.to_date:
        cond += " and date_of_joining <= '{}'".format(filters.to_date)
    if filters.reason:
        cond += " and reason = '{}'".format(filters.reason)
    if filters.gender:
        cond += " and gender= '{}'".format(filters.gender)

    return cond

    
