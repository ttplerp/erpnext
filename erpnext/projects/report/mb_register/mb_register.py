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
		{"fieldtype": "Link",	"fieldname": "name", "label": _("Transaction #"),  "options": "MB Entry", "width": 150},
		{"fieldtype": "Date",	"fieldname": "entry_date", "label": _("Date"), "width": 110},
		{"fieldtype": "Link",	"fieldname": "cost_center", "label": _("Cost Center"), "options": "Cost Center", "width": 180},
		{"fieldtype": "Link",	"fieldname": "party_type", "label": _("Party Type"), "options": "DocType", "width": 100},
		{"fieldtype": "Dynamice Link",	"fieldname": "party", "label": _("Party"), "options": "party_type", "width": 150},
		{"fieldtype": "Link",	"fieldname": "boq", "label": _("BOQ"), "options": "BOQ", "width": 150},
		{"fieldtype": "Float",	"fieldname": "booked_amount", "label": _("Booked Amount (Nu.)"), "width": 180},
		{"fieldtype": "Float",	"fieldname": "invoice_amount", "label": _("Invoice Amount (Nu.)"), "width": 180},
		{"fieldtype": "Data",	"fieldname": "status", "label": _("Status"), "width": 110},

		]

def get_data(filters):
	query = """ 
			select 
				p.name as project, 
				p.project_name, 
				mb.name,
				mb.entry_date, 
				mb.cost_center, 
				mb.party_type,
				mb.party,
				mb.boq, 
				mb.total_entry_amount as booked_amount, 
				mb.total_invoice_amount as invoice_amount, 
				mb.status
			from  `tabMB Entry` as mb, `tabProject` p
			where  mb.docstatus = 1
			and p.name = mb.project
	"""

	if filters.get("project"):
				query += " and project = \'" + str(filters.project) + "\'"

	if filters.get("from_date") and filters.get("to_date"):
			query += " and entry_date between \'" + str(filters.from_date) + "\' and \'"+ str(filters.to_date) + "\'"

	elif filters.get("from_date") and not filters.get("to_date"):
			query += " and entry_date >= \'" + str(filters.from_date) + "\'"

	elif not filters.get("from_date") and filters.get("to_date"):
			query += " and entry_date <= \'" + str(filters.to_date) + "\'"

	query += " order by entry_date desc"

	return frappe.db.sql(query)

