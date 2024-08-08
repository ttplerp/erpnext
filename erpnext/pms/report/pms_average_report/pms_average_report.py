# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt

def execute(filters=None):
    columns = get_column(filters)
    data = get_data(filters) 
    return columns, data

def get_data(filters):
    additional_fields = get_additional_fields(filters)
    cond = get_conditions(filters)
    group_by = get_group_by(filters)

    query = """
        SELECT 
            x.pms_calendar,            
            MIN(x.form_i_total_rating) as form_i_min_rating,
            MAX(x.form_i_total_rating) as form_i_max_rating,
            AVG(x.form_i_total_rating) as form_i_avg_rating,
            MIN(x.form_ii_total_rating) as form_ii_min_rating,
            MAX(x.form_ii_total_rating) as form_ii_max_rating,
            AVG(x.form_ii_total_rating) as form_ii_avg_rating,
            MIN(x.form_i_score) as form_i_min_score,
            MAX(x.form_i_score) as form_i_max_score,
            AVG(x.form_i_score) as form_i_avg_score,
            MIN(x.form_ii_score) as form_ii_min_score,
            MAX(x.form_ii_score) as form_ii_max_score,
            AVG(x.form_ii_score) as form_ii_avg_score,
            MIN(x.final_score) as min_final_score,
            MAX(x.final_score) as max_final_score,
            AVG(x.final_score) as avg_final_score,
            x.final_score_percent,
            x.overall_rating {0}
            FROM
        (select
            employee,
            pms_calendar,
            gender,
            approver, 
            form_i_total_rating,
            form_ii_total_rating,
            form_i_score,
            form_ii_score,
            final_score,
            final_score_percent,
            overall_rating {0}
            FROM `tabPerformance Evaluation` pe {1} 
            AND NOT EXISTS (SELECT employee FROM `tabPMS Summary` ps {1} AND ps.employee = pe.employee) AND docstatus = 1
        union
        select 
            employee,
            pms_calendar,
            gender,
            approver,
            form_i_total_rating,
            form_ii_total_rating,
            form_i_score,
            form_ii_score,
            final_score,
            final_score_percent,
            overall_rating {0} 
            FROM `tabPMS Summary` {1} AND docstatus = 1) AS x {1} {2};
        """.format(additional_fields, cond, group_by)
    # frappe.throw(str(query))

    data = frappe.db.sql(query, as_dict=1)
    max = frappe.db.get_single_value('PMS Setting','max_rating_limit')
    for d in data:
        d['final_score_percent'] = flt(d.avg_final_score)/flt(max) * 100
        d['overall_rating'] = frappe.db.sql('''select name from `tabOverall Rating` where  upper_range_percent >= {0} and lower_range_percent <= {0}'''.format(d.final_score_percent))[0][0]
    return data

def get_column(filters):
    columns = []		
    if filters.get("average") == "Section":		
        columns.append({
            'fieldname':'section',
            'fieldtype':'Link',
            'label':'Section',
            'options':'Section',
            'width':200
        })		

    if filters.get("average") == "Unit":		
        columns.append({
            'fieldname':'unit',
            'fieldtype':'Link',
            'label':'Unit',
            'options':'Unit',
            'width':200
        })	

    if filters.get("average") == "Region":		    
        columns.append({
            'fieldname':'region',
            'fieldtype':'Link',
            'label':'Region',
            'options':'Region',
            'width':200
        })	

    if filters.get("average") == "Division":		
        columns.append({
            'fieldname':'division',
            'fieldtype':'Link',
            'label':'Division',
            'options':'Division',
            'width':200
        })	

    if filters.get("average") == "Cost Center":		
        columns.append({
            'fieldname':'cost_center',
            'fieldtype':'Link',
            'label':'Cost Center',
            'options':'Cost Center',
            'width':200
        })	

    if filters.get("average") == "Department":		
        columns.append({
            'fieldname':'department',
            'fieldtype':'Link',
            'label':'Department',
            'options':'Department',
            'width':200
        })		
    columns.append({
            'fieldname':'pms_calendar',
            'fieldtype':'Link',
            'label':'PMS Calendar',
            'options':'PMS Calendar'
        })
    columns.append({
            'fieldname':'form_i_min_rating',
            'fieldtype':'Float',
            'label':'F1 Min Rating',
            'precision': 5,
        })
    columns.append({
            'fieldname':'form_i_max_rating',
            'fieldtype':'Float',
            'label':'F1 Max Rating',
            'precision': 5,
        })
    columns.append({
            'fieldname':'form_i_avg_rating',
            'fieldtype':'Float',
            'label':'F1 Avg Rating',
            'precision': 5,
        })
    columns.append({
            'fieldname':'form_ii_min_rating',
            'fieldtype':'Float',
            'label':'F2 Min Rating',
            'precision': 5,
        })
    columns.append({
            'fieldname':'form_ii_max_rating',
            'fieldtype':'Float',
            'label':'F2 Max Rating',
            'precision': 5,
        })
    columns.append({
            'fieldname':'form_ii_avg_rating',
            'fieldtype':'Float',
            'label':'F2 Avg Rating',
            'precision': 5
        })
    columns.append({
            'fieldname':'form_i_min_score',
            'fieldtype':'Float',
            'label':'F1 Min Score',
            'precision': 5,
        })
    columns.append({
            'fieldname':'form_i_max_score',
            'fieldtype':'Float',
            'label':'F1 Max Score',
            'precision': 5,
        })
    columns.append({
            'fieldname':'form_i_avg_score',
            'fieldtype':'Float',
            'label':'F1 Avg Score',
            'precision': 5,
        })
    columns.append({
            'fieldname':'form_ii_min_score',
            'fieldtype':'Float',
            'label':'F2 Min Score',
            'precision': 5,
        })
    columns.append({
            'fieldname':'form_ii_max_score',
            'fieldtype':'Float',
            'label':'F2 Max Score',
            'precision': 5,
        })
    columns.append({
            'fieldname':'form_ii_avg_score',
            'fieldtype':'Float',
            'label':'F2 Avg Score',
            'precision': 5
        })
    columns.append({
            'fieldname':'min_final_score',
            'fieldtype':'Float',
            'label':'Min Final Score',
            'precision': 5
        })
    columns.append({
            'fieldname':'max_final_score',
            'fieldtype':'Float',
            'label':'Max Final Score',
            'precision': 5
        })               
    columns.append({
            'fieldname':'avg_final_score',
            'fieldtype':'Float',
            'label':'Final Score Avg',
            'precision': 5
        })  
    columns.append({
            'fieldname':'final_score_percent',
            'fieldtype':'Float',    
            'label':'Final Score Percent',
            'precision': 5
        })
    columns.append({
            'fieldname':'overall_rating',
            'fieldtype':'Link',
            'width': 200,
            'options':'Overall Rating',    
            'label':'Overall Rating'
        })  
    return columns

def get_additional_fields(filters):
    additional_fields = ""

    if filters.average == "Section":
        additional_fields += ",section"
    
    if filters.average == "Unit":
        additional_fields += ",unit"

    if filters.average == "Region":
        additional_fields += ",region"
	
    if filters.average == "Division":
        additional_fields += ",division"

    if filters.average == "Cost Center":
        additional_fields += ",cost_center"

    if filters.average == "Department":
        additional_fields += ",department"
    
    return additional_fields

def get_group_by(filters):
    group_by = ""
    if filters.average == "Section":
        group_by = "GROUP BY section"
    if filters.average == "Unit":
        group_by = "GROUP BY unit"
    if filters.average == "Region":
        group_by = "GROUP BY region"
    if filters.average == "Division":
        group_by = "GROUP BY division"
    if filters.average == "Cost Center":
        group_by = "GROUP BY cost_center"
    if filters.average == "Department":
        group_by = "GROUP BY department"
        
    return group_by

def get_conditions(filters):
    cond = ""
    if filters.pms_calendar:
        cond += " WHERE pms_calendar = '{}'".format(filters.pms_calendar)
    
    if filters.gender:
        cond += " AND gender= '{}'".format(filters.gender)

    if filters.average == "Section":
        cond1 = ""
        if filters.exclude_approver:
            cond1 = " AND employee NOT IN (select approver from `tabSection` where name = CONCAT(section,' - BTL')) "
        if filters.section:
            cond += " AND section = '{}' {}".format(filters.section, cond1)
        else:
            cond += " AND (section IS NOT NULL OR section !='') {}".format(cond1)
    
    if filters.average == "Unit":
        cond1 = ""
        if filters.exclude_approver:
            cond1 = " AND employee NOT IN (select approver from `tabUnit` where name = CONCAT(unit,' - BTL')) "
        if filters.unit:
            cond += " AND unit = '{}' {}".format(filters.unit, cond1)
        else:
            cond += " AND (unit IS NOT NULL OR unit != '') {}".format(cond1)

    if filters.average == "Region":
        cond1 = ""
        if filters.exclude_approver:
            cond1 = " AND employee NOT IN (select approver from `tabRegion` where name = CONCAT(region,' - BTL')) "
        if filters.region:
            cond += " AND region = '{}' {}".format(filters.region, cond1)
        else:
            cond += " AND (region IS NOT NULL OR region != '') {}".format(cond1)
	
    if filters.average == "Division":
        cond1 = ""
        if filters.exclude_approver:
            cond1 = " AND employee NOT IN (select approver from `tabDivision` where name = CONCAT(division,' - BTL')) "
        if filters.division:
            cond += " AND division = '{}' {}".format(filters.division, cond1)
        else:
            cond += " AND (division IS NOT NULL OR division != '') {}".format(cond1)

    if filters.average == "Cost Center":
        cond1 = ""
        if filters.exclude_approver:
            cond1 = " AND employee NOT IN (select approver from `tabCost Center` where name = CONCAT(cost_center,' - BTL')) "
        if filters.cost_center:
            cond += " AND cost_center = '{}' {}".format(filters.cost_center, cond1)
        else:
            cond += " AND (cost_center IS NOT NULL OR cost_center != '') {}".format(cond1)

    if filters.average == "Department":
        cond1 = ""
        if filters.exclude_approver:
            cond1 = " AND employee NOT IN (select approver from `tabDepartment` where name = CONCAT(department,' - BTL')) "
        if filters.department:
            cond += " AND department = '{}' {}".format(filters.department, cond1)
        else:
            cond += " AND (department IS NOT NULL OR department != '') {}".format(cond1)

    return cond
