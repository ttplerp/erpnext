# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from datetime import datetime



def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data
def get_columns():
	columns = [
		  {
            'fieldname': 'application_date_time',
            'label': 'Application Date & Time',
            'fieldtype': 'Date',
            'options': 'Application Date & Time',
			
        },
     {
            'fieldname': 'applicant_name',
            'label':'Application Name',
            'fieldtype': 'Data',
            
        },
      
        {
            'fieldname': 'cid',
            'label': 'Citizen ID No',
            'fieldtype': 'Int',
            'options': 'Citizen No'
        },
        {
            'fieldname': 'employee_id',
            'label': 'Employee ID',
            'fieldtype': 'Int',
            'options': 'Employee ID'
        },
            {
            'fieldname': 'grade',
            'label': 'Grade',
            'fieldtype': 'Data',
            'options': 'Grade'
        },
   {
            'fieldname': 'applicant_rank',
            'label': 'Applicant Rank',
            'fieldtype': 'Int',
            'options': 'Applicant Rank'
        }
   ,
     
         {
            'fieldname': 'department',
            'label': 'Department',
            'fieldtype': 'Data',
            'options': 'Department'
        },
    {
            'fieldname': 'designation',
            'label': 'Designation',
            'fieldtype': 'Data',
            'options': 'Designation'
        },
		
		 {
            'fieldname': 'employment_type',
            'label': 'Employment Type',
            'fieldtype': 'Select',
            'options': 'Employment Type'
        },
		
    {
            'fieldname': 'work_station',
            'label': 'Work Station',
            'fieldtype': 'Data',
            
        },
  
   
  
    {
            'fieldname': 'application_status',
            'label': 'Application Status',
            'fieldtype': 'Select',
            'options': 'Application Status'
        },
     {
            'fieldname': 'gross_salary',
            'label': 'Applicant Gross Salary',
            'fieldtype': 'Int',
            'options': 'Gross Salary'
        },
      {
            'fieldname': 'spouse_gross_salary',
            'label': 'Spouse Gross Salary',
            'fieldtype': 'Int',
            'options': 'Gross Salary'
        },
     {
            'fieldname': 'total_gross_salary',
            'label': 'Total Gross Salary',
            'fieldtype': 'Int',
            'options': 'Gross Salary'
        },
     {
            'fieldname': 'flat_no',
            'label': 'Flat No',
            'fieldtype': 'Int',
            'options': 'Flat No'
        },
      {
            'fieldname': 'building_classification',
            'label': 'Eligible Building Classification',
            'fieldtype': 'Link',
            'options': 'Building Classification',
            'Link': 'Building Classification'
        },
       {
            'fieldname': 'dzongkhag',
            'label': 'Dzongkhag',
            'fieldtype': 'Data',
            'options': 'Dzongkhag'
        },
        {
            'fieldname': 'email_id',
            'label': 'Email ID',
            'fieldtype': 'Data',
            'options': 'Email ID'
        },
         {
            'fieldname': 'gewog',
            'label': 'Gewog',
            'fieldtype': 'Data',
            'options': 'Gewog'
        },
         {
            'fieldname': 'ministry_agency',
            'label': 'Ministry/Agency',
            'fieldtype': 'Data',
            'options': 'Ministry/Agency'
        },
          {
            'fieldname': 'mobile_no',
            'label': 'Mobile No',
            'fieldtype': 'Int',
            'options': 'Mobile No'
        },
           {
            'fieldname': 'village',
            'label': 'Village',
            'fieldtype': 'Data',
            'options': 'Village'
        },
            {
            'fieldname': 'telephone_office',
            'label': 'Telephone (Office)',
            'fieldtype': 'Int',
            'options': 'Telephone (Office)'
        },
               {
            'fieldname': 'telephone_residence',
            'label': 'Telephone (Residence)',
            'fieldtype': 'Int',
            'options': 'Telephone (Residence)'
        },
    
   
     {
            'fieldname': 'marital_status',
            'label': 'Marital Status',
            'fieldtype': 'Select',
            'options': 'Marital Status'
        },
      {
            'fieldname': 'gender',
            'label': 'Gender',
            'fieldtype': 'Data',
            'options': 'Gender'
        },
       {
            'fieldname': 'spouse_name',
            'label': 'Spouse Name',
            'fieldtype': 'Data',
            'options': 'Spouse Name'
        },
		 {
            'fieldname': 'spouse_cid',
            'label': 'Spouse Cid',
            'fieldtype': 'Data',
            'options': 'Spouse Name'
        },
		 {
            'fieldname': 'spouse_dzongkhag',
            'label': 'Spouse Dzongkhag',
            'fieldtype': 'Data',
            'options': 'Spouse Dzongkhag'
        },
		
   {
            'fieldname': 'spouse_gewog',
            'label': 'Spouse Gewog',
            'fieldtype': 'Data',
            'options': 'Spouse Gewog'
        },
   {
            'fieldname': 'spouse_dob',
            'label': 'Spouse Date of Birth',
            'fieldtype': 'Date',
            'options': 'Spouse Date of Birth'
        },
   
   {
            'fieldname': 'spouse_village',
            'label': 'Spouse Village',
            'fieldtype': 'Data',
            'options': 'Spouse Village'
        },
   
   {
            'fieldname': 'spouse_employment_type',
            'label': 'Spouse Employment Type',
            'fieldtype': 'Select',
            'options': 'Spouse Employment Type'
        },
   
	]


	return columns

def get_data(filters):
    conditions = get_filters(filters)
    # data = frappe.db.get_all("Housing Application",fields=get_fields_name(), filters = conditions)
    # return data
    query = """
                     SELECT *,
                     gross_salary + spouse_gross_salary AS total_gross_salary
        
           FROM `tabHousing Application`
           WHERE {conditions}""".format(conditions = conditions)
           
    data = frappe.db.sql(query, filters,as_dict=True)
    return data
        

def get_filters(filters):
    conditions = []
    if filters.get('application_date_time'):
      
        conditions.append("application_date_time <= %(application_date_time)s")
    if filters.get('employment_type'):
        conditions.append('employment_type = %(employment_type)s')
    if filters.get('work_station'):
        conditions.append('work_station = %(work_station)s')
    if filters.get('application_status'):
        conditions.append('application_status = %(application_status)s')
    if filters.get('building_classification'):
        conditions.append('building_classification = %(building_classification)s')
    # frappe.errprint(conditions)

    return  " AND ".join(conditions) if conditions else "1=1"