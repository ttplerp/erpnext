# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data

def get_columns(filters):
	column = [
		{
			"fieldname": "court_tracking_id",
			"label": "Court Tracking System",
			"fieldtype": "Link",
			"options": "Court Tracking System",
			"width": 170
		},
		{
			"fieldname": "case_type",
			"label": "Case Type",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"fieldname": "branch",
			"label": "Branch",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"fieldname": "date",
			"label": "Date of Registration/Filing/Complaint",
			"fieldtype": "Date",
			"width": 150
		},
		
	]

	if filters.get('case_type') == 'NPL Recovery Cases':
		column.extend([
			{
				"fieldname": "court_venue",
				"label": "Court Venue",
				"fieldtype": "Data",
				"width": 100
			},
			{
				"fieldname": "borrower_filed_by",
				"label": "Borrower/Filed By Name",
				"fieldtype": "Data",
				"width": 130
			},
			{
				"fieldname": "cid_license_number",
				"label": "CID/License Number",
				"fieldtype": "Data",
				"width": 130
			},
			{
				"fieldname": "loan_account_no",
				"label": "Loan Account",
				"fieldtype": "Data",
				"width": 130
			},
			{
				"fieldname": "case_status",
				"label": "Case Status",
				"fieldtype": "Data",
				"width": 180
			},
			{
				"fieldname": "case_description",
				"label": "Case Description",
				"fieldtype": "Data",
				"width": 180
			},
			{
				"fieldname": "case_date",
				"label": "Case Date",
				"fieldtype": "Date",
				"width": 180
			},
		])
	elif filters.get('case_type') == 'Criminal & ACC Cases':
		column.extend([
			{
				"fieldname": "investigation",
				"label": "Investigation",
				"fieldtype": "Data",
				"width": 130
			}
		])
	elif filters.get('case_type') == 'Counter Litigation':
		column.extend([
			{
				"fieldname": "court_venue",
				"label": "Court Venue",
				"fieldtype": "Data",
				"width": 100
			},
			{
				"fieldname": "borrower_filed_by",
				"label": "Borrower/Filed By Name",
				"fieldtype": "Data",
				"width": 130
			},
			{
				"fieldname": "cid_license_number",
				"label": "CID/License Number",
				"fieldtype": "Data",
				"width": 130
			},
		])

	return column

def get_data(filters):
	if not filters.get('case_type'):
		return []
	
	condition = ""
	if filters.get('case_type'):
		condition = f" AND case_type='{filters.get('case_type')}'"
	
	if filters.get('case_type') == 'Criminal & ACC Cases':
		query = """
			SELECT 
				a.name AS court_tracking_id,
				a.branch,
				a.case_type,
				a.investigation,
				a.date
			FROM `tabCourt Tracking System` a
			WHERE a.docstatus = 1
			AND a.date BETWEEN '{from_date}' AND '{to_date}'
			{cond}
			ORDER BY a.date DESC
			""".format(cond=condition, from_date=filters.get('from_date'), to_date=filters.get('to_date'))
		result = frappe.db.sql(query, as_dict=1)
		return result

	query = """
		SELECT 
			a.name AS court_tracking_id,
			a.branch,
			a.case_type,
			a.court_venue,
			a.date,
			a.borrower_filed_by,
			a.loan_account_no,
			a.cid_license_number,
			b.case_status,
			b.case_description,
			b.date AS case_date
		FROM `tabCourt Tracking System` a
		JOIN (
			SELECT b1.*
			FROM `tabCourt Status` b1
			INNER JOIN (
				SELECT parent, MAX(date) AS max_date
				FROM `tabCourt Status`
				WHERE date BETWEEN '{from_date}' AND '{to_date}'
				GROUP BY parent
			) b2 ON b1.parent = b2.parent AND b1.date = b2.max_date
		) b ON b.parent = a.name
		WHERE a.docstatus = 1
		{cond}
		ORDER BY b.date DESC
		""".format(cond=condition, from_date=filters.get('from_date'), to_date=filters.get('to_date'))
	
	result = frappe.db.sql(query, as_dict=1)

	return result