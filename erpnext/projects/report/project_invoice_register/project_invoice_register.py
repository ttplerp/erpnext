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
			{"fieldtype": "Date",	"fieldname": "invoice_date", "label": _("Invoice Date"), "width": 110},
			{"fieldtype": "Link",	"fieldname": "cost_center", "label": _("Cost Center"), "options": "Cost Center", "width": 180},
			{"fieldtype": "Link",	"fieldname": "party_type", "label": _("Party Type"), "options": "DocType", "width": 100},
			{"fieldtype": "Dynamice Link",	"fieldname": "party", "label": _("Party"), "options": "party_type", "width": 150},
			{"fieldtype": "Link",	"fieldname": "boq", "label": _("BOQ"), "options": "BOQ", "width": 150},
			{"fieldtype": "Link",	"fieldname": "invoice_no", "label": _("Invoice"), "options": "BOQ", "width": 150},
			{"fieldtype": "Float",	"fieldname": "total_amount", "label": _("Total Amount (Nu.)"), "width": 150},
			{"fieldtype": "Float",	"fieldname": "total_advance_amount", "label": _("Advance Amount (Nu.)"), "width": 180},
			{"fieldtype": "Float",	"fieldname": "tds_amount", "label": _("Net Amount (Nu.)"), "width": 150},
			{"fieldtype": "Float",	"fieldname": "retention_amount", "label": _("TDS Amount (Nu.)"), "width": 150},
			{"fieldtype": "Float",	"fieldname": "net_amount", "label": _("Retention Amount (Nu.)"), "width": 180},
			{"fieldtype": "Float",	"fieldname": "outstanding_amount", "label": _("Outstanding Amount (Nu.)"), "width": 200},
			{"fieldtype": "Data",	"fieldname": "status", "label": _("Status"), "width": 110},
	]

def get_data(filters):
	query =  """
			select 
				p.name as project,
				p.project_name,
				pi.invoice_date, 
				pi.cost_center, 
				pi.party_type,
				pi.party, 
				pi.boq, 
				pi.name as invoice_no, 
				pi.total_amount,
				pi.total_advance_amount,
				pi.tds_amount,
				pi.retention_amount, 
				pi.net_amount,
				pi.outstanding_amount,
				pi.status
			from `tabProject Invoice` as pi, `tabProject` as p 
			where pi.docstatus != 2
			and p.name = pi.project
		"""
	if filters.get("project"):
		query += ' and project = "{0}"'.format(str(filters.project))
	if filters.get("from_date") and filters.get("to_date"):
		query += " and invoice_date between \'" + str(filters.from_date) + "\' and \'"+ str(filters.to_date) + "\'"
	elif filters.get("from_date") and not filters.get("to_date"):
		query += " and invoice_date >= \'" + str(filters.from_date) + "\'"
	elif not filters.get("from_date") and filters.get("to_date"):
		query += " and invoice_date <= \'" + str(filters.to_date) + "\'"

	query += " order by invoice_date desc"
	return frappe.db.sql(query)

