'''
--------------------------------------------------------------------------------------------------------------------------
Version		 	Author		  				CreatedOn		 	ModifiedOn		  	Remarks
------------ --------------- ------------------ -------------------  -----------------------------------------------------
1.0		      	Dawa Nyuehtyue Tshering		2024/11/20			2024/11/21			Original Version
--------------------------------------------------------------------------------------------------------------------------			
'''

from __future__ import unicode_literals
import frappe
from frappe import _

def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data

def get_columns():
	return [
		{"fieldtype": "Link",	"fieldname": "project", "label": _("Project"),  "options": "Project", "width": 200},
		{"fieldtype": "Data",	"fieldname": "project_name", "label": _("Project Name"), "width": 200},
		{"fieldtype": "Link",	"fieldname": "cost_center", "label": _("Cost Center"), "options": "Cost Center", "width": 180},
		{"fieldtype": "Date",	"fieldname": "boq_date", "label": _("Date"), "width": 110},
		{"fieldtype": "Link",	"fieldname": "name", "label": _("BOQ"), "options": "BOQ", "width": 150},
		{"fieldtype": "Float",	"fieldname": "total_amount", "label": _("Total Amount (Nu.)"), "width": 150},
		{"fieldtype": "Float",	"fieldname": "total_unclaimed_amount", "label": _("Unclaimed Amount (Nu.)"), "width": 180},
		{"fieldtype": "Float",	"fieldname": "total_claimed_amount_", "label": _("Claimed Amount (Nu.)"), "width": 180},
	]

def get_data(filters):
	query =  """
			select 
				p.name as project, 
				p.project_name, 
				b.cost_center, 
				b.boq_date, 
				b.name, 
				b.total_amount, 
				b.total_unclaimed_amount, 
				b.total_claimed_amount
			from `tabBOQ` as b, `tabProject` as p 
			where b.docstatus =1
			and   p.name = b.project
	""" 
	if filters.get("project"):
		query += ' and project = "{0}"'.format(str(filters.project))

	if filters.get("from_date") and filters.get("to_date"):
		query += " and boq_date between \'" + str(filters.from_date) + "\' and \'"+ str(filters.to_date) + "\'"
	elif filters.get("from_date") and not filters.get("to_date"):
		query += " and boq_date >= \'" + str(filters.from_date) + "\'"
	elif not filters.get("from_date") and filters.get("to_date"):
		query += " and boq_date <= \'" + str(filters.to_date) + "\'"

	query += " order by boq_date desc"
	return frappe.db.sql(query)
