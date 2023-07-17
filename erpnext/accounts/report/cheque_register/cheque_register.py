# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt
from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt

def execute(filters=None):
	columns = get_columns()
	queries = construct_query(filters)
	data = get_data(queries)

	return columns, data

def get_data(query):
	data = []
	datas = frappe.db.sql(query, as_dict=True)
	total = {}
	total_amount = 0
	total_cancelled = 0
	for d in datas:
		key = (d.cheque_no, d.cheque_date)
		total[key] = flt(total.get(key)) + flt(d.amount)

	for d in datas:
		key = (d.cheque_no, d.cheque_date)
		row = [d.voucher_type, d.voucher_no, d.voucher_date, d.cheque_no, d.cheque_date, d.amount, total[key],
			d.recipient, d.cheque_status, d.cancelled_amount]
		data.append(row)
		total_amount += flt(d.amount)
		total_cancelled += flt(d.cancelled_amount)

	# Total row
	row = ['Total', '', '', '', '', total_amount, '', '', '', total_cancelled]
	data.append(row)

	return data

def construct_query(filters=None):
	query = """SELECT 'Journal Entry' as voucher_type, je.name as voucher_no, je.posting_date as voucher_date, 
			je.cheque_no, je.cheque_date, 
			CASE je.docstatus WHEN 2 THEN 0 ELSE je.total_amount END AS amount, 
			CASE je.docstatus WHEN 2 THEN je.total_amount ELSE 0 END AS cancelled_amount, 
			je.pay_to_recd_from recipient, 
			CASE je.docstatus WHEN 2 THEN 'CANCELLED' ELSE null END AS cheque_status 
		FROM `tabJournal Entry` je 
		WHERE je.naming_series IN ('Bank Payment Voucher') 
		AND IFNULL(je.cheque_no,'') != '' 
		AND je.posting_date BETWEEN '{from_date}' AND '{to_date}' 
		AND NOT EXISTS (SELECT 1 from `tabJournal Entry` je1 where je1.amended_from = je.name) 
		UNION ALL 
		SELECT 'Payment Entry' as voucher_type, pe.name as voucher_no, pe.posting_date as voucher_date, 
			pe.reference_no AS cheque_no, pe.reference_date AS cheque_date, 
			CASE pe.docstatus WHEN 2 THEN 0 
				ELSE (CASE WHEN pe.base_paid_amount > 0 THEN pe.base_paid_amount ELSE pe.base_received_amount END) 
			END AS amount, 
			CASE pe.docstatus WHEN 2 THEN (CASE WHEN pe.base_paid_amount > 0 THEN pe.base_paid_amount ELSE pe.base_received_amount END) 
				ELSE 0 
			END AS cancelled_amount, 
			pe.party_name as recipient, 
			CASE pe.docstatus WHEN 2 THEN 'CANCELLED' ELSE null END AS cheque_status 
		FROM `tabPayment Entry` pe 
		WHERE pe.docstatus !=2 
		AND IFNULL(pe.reference_no,'') != '' 
		AND pe.posting_date BETWEEN '{from_date}' AND '{to_date}' 
		AND NOT EXISTS (SELECT 1 from `tabPayment Entry` pe1 where pe1.amended_from = pe.name) 
		""".format(from_date=filters.from_date, to_date=filters.to_date)
	return query

def get_columns():
	return [
		{
		  "fieldname": "voucher_type",
		  "label": "Voucher Type",
		  "fieldtype": "Data",
		  "width": 100
		},
		{
		  "fieldname": "voucher_no",
		  "label": "Voucher No",
		  "fieldtype": "Dynamic Link",
		  "options": "voucher_type",
		  "width": 120
		},
		{
		  "fieldname": "voucher_date",
		  "label": "Voucher Date",
		  "fieldtype": "Date",
		  "width": 100
		},
		{
		  "fieldname": "cheque_no",
		  "label": "Cheque No",
		  "fieldtype": "Data",
		  "width": 100
		},
		{
		  "fieldname": "cheque_date",
		  "label": "Cheque Date",
		  "fieldtype": "Date",
		  "width": 100
		},
		{
		  "fieldname": "amount",
		  "label": "Amount",
		  "fieldtype": "Currency",
		  "width": 130
		},
		{
		  "fieldname": "total_amount",
		  "label": "Total Amount",
		  "fieldtype": "Currency",
		  "width": 130
		},
		{
		  "fieldname": "recipient",
		  "label": "Recipient",
		  "fieldtype": "Data",
		  "width": 230
		},
		{
		  "fieldname": "cheque_status",
		  "label": "Cheque Status",
		  "fieldtype": "Data",
		  "width": 100
		},
		{
		  "fieldname": "cancelled_amount",
		  "label": "Cancelled Amount",
		  "fieldtype": "Currency",
		  "width": 130
		},
	]
