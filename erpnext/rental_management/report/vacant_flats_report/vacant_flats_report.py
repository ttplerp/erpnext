import frappe
from datetime import datetime



def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data
def get_columns():
	columns = [
		  {
            'fieldname': 'block_no',
            'label': 'Block No',
            'fieldtype': 'Data',
            'options': 'Application Date & Time',
			
        },
      {
            'fieldname': 'flat_no',
            'label': 'Flat No',
            'fieldtype': 'Data',
            'options': 'Application Date & Time',
			
        },
     {
            'fieldname': 'dzongkhag',
            'label':'Dzongkhag',
            'fieldtype': 'Data',
            
        },
     {
            'fieldname': 'location_name',
            'label':'Location Name',
            'fieldtype': 'Data',
            
        },
     {
            'fieldname': 'building_classification',
            'label':'Building Classification',
            'fieldtype': 'Data',
            
        },

     {
            'fieldname': 'building_category',
            'label':'Building Category',
            'fieldtype': 'Data',
            
        },
     {
            'fieldname': 'total_floor_area',
            'label':'Total Floor Area',
            'fieldtype': 'Data',
            
        },
     {
            'fieldname': 'status',
            'label':'Flat Status',
            'fieldtype': 'Data',
            
        },
  
    
    
   
	]


	return columns

def get_data(filters):
    conditions = get_filters(filters)
    # data = frappe.db.get_all("Housing Application",fields=get_fields_name(), filters = conditions)
    # return data
    query = """
                     SELECT *
        
           FROM `tabFlat No`
           WHERE {conditions} and status != 'Allocated' """.format(conditions = conditions)
           
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