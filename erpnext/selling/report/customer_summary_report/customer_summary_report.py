# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


from __future__ import unicode_literals
import frappe
from frappe.utils import flt

def execute(filters=None):
	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data
	
def get_columns(filters):
	columns = [
		{
			"fieldname": "customer",
			"label": "CUSTOMER",
			"fieldtype": "Link",
			"options": "Customer",
			"width": 200
		},
		{
			"fieldname": "country",
			"label": "Country",
			"fieldtype": "data",
			"width": 100
		},
		{
			"fieldname": "territory",
			"label": "TERRITORY",
			"fieldtype": "Link",
			"options": "Territory",
			"width": 100
		},
		{
			"fieldname": "customer_type",
			"label": "Customer Type",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"fieldname": "opening",
			"label": "OPENING",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 150
		},
		{
			"fieldname": "billed_amount",
			"label": "BILLED AMOUNT",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 150
		},
		{
			"fieldname": "received_amount",
			"label": "PAYMENT RECEIVED",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 150
		},
		{
			"fieldname": "closing",
			"label": "CLOSING BALANCE",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 150
		}
	]
	return columns
def get_data(filters):
	data = []
	row = []
	cus_list = frappe.db.sql("""
			select name from `tabCustomer` where disabled != 1
		""",as_dict=True)
	for q in cus_list:
		# query = """ select sum(case when si.posting_date between '{from_date}' and '{to_date}' then ifnull(sii.amount + sii.excess_amt + si.total_charges + sii.normal_loss_amt + sii.abnormal_loss_amt, 0) else 0 end) as billed_amount from `tabSales Invoice` si, `tabSales Invoice Item` sii where sii.parent = si.name and si.docstatus = 1 and si.customer="{customer}" """.format(from_date = filters.from_date, to_date = filters.to_date, customer=q.name)
		
		# if filters.item_code:
		# 	query += " and sii.item_code = '{0}'".format(filters.item_code)

		# if filters.country:
		# 	query += " and exists ( select 1 from `tabCustomer` where country = '{0}') ".format(filters.country)

		# if filters.item_type:
		# 	query += " and sii.item_type = '{0}'".format(filters.item_type)

		# dat = frappe.db.sql(query, as_dict = 1)


		# for d in dat:
		territory, country , customer_type = get_customer_details(filters, q.name)
		openning_amount = get_openning_amount(filters, q.name)
		received_amount = payment_details(filters, q.name)
		billed_amount = get_billed_amount(filters, q.name)
		# total_bill_amount=flt(billed_amount)-flt(openning_amount)
		closing_amt =  flt(openning_amount) + flt(billed_amount) - flt(received_amount)	
		# if flt(openning_amount) + flt(total_bill_amount) + flt(received_amount) + flt(closing_amt) != 0:
		row = [q.name, country, territory,customer_type, openning_amount, billed_amount, received_amount, closing_amt]
		data.append(row)
	return data

def get_customer_details(filters, customer):
	cust = frappe.db.sql(""" select territory, country, customer_type from `tabCustomer` where name = "{0}" """.format(customer), as_dict = 1)
	if cust:
		return cust[0].territory, cust[0].country, cust[0].customer_type
	else:
		 return ''
def get_openning_amount(filters, customer):
	credit = debit =0
	opening_data = frappe.db.sql("""
			select debit as debit, credit as credit
			from
				`tabGL Entry`
			where is_cancelled =0
			and party_type='Customer'
			and party='{0}'
			and posting_date < '{1}'
		""".format(customer,filters.from_date),as_dict=True)
	for d in opening_data:
		credit += flt(d.credit)
		debit += flt(d.debit)
	opening_amount =flt(debit)-flt(credit)
	return opening_amount
def payment_details(filters, customer):
	# received_amount = 0
	# payment = frappe.db.sql("""select paid_amount from `tabPayment Entry`where party_type='Customer' and posting_date between '{0}' and '{1}' and party='{2}' and docstatus = 1 """.format(filters.from_date, filters.to_date,party), as_dict = 1)
	
	# for d in payment:
	# 	received_amount += d.paid_amount
	# return received_amount
	payment_received = 0
	payment = frappe.db.sql("""
			select credit as credit
			from
				`tabGL Entry`
			where is_cancelled =0
			and party_type='Customer'
			and party='{0}'
			and posting_date between '{1}' and '{2}'
		""".format(customer,filters.from_date, filters.to_date),as_dict=True)
	for d in payment:
		payment_received += flt(d.credit)
	return payment_received

def get_billed_amount(filters, customer):
	bill_amount = 0
	bill = frappe.db.sql("""
			select debit as debit
			from
				`tabGL Entry`
			where is_cancelled =0
			and party_type='Customer'
			and party='{0}'
			and posting_date between '{1}' and '{2}'
		""".format(customer,filters.from_date, filters.to_date),as_dict=True)
	for d in bill:
		bill_amount += flt(d.debit)
	return bill_amount