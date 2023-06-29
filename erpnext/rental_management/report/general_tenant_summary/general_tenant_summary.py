# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import getdate


def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	# if filters.get("rental_official"):
	# 	data = get_tenant_list(filters);
	# else:
	# 	data = get_data(filters);
	return columns, data

def get_columns():
	return [
		("Tenant Code") + ":Data:120",
		("Tenant") + ":Data:150",
		("Rental Bill") + ":Data:260",
		("Rental Income") + ":Currency:120",
		("Rent Received") + ":Currency:120",
		("Pre-rent") + ":Currency:120",
		("Adjusted Amount") + ":Currency:150",
		("Excess Rent") + ":Currency:120",
		("TDS") + ":Currency:90",
		("Rent Write-off") + ":Currency:150",
		("Penalty") + ":Currency:90",
		("Discount") + ":Currency:90",
		("Total Rent Received") + ":Currency:180",
		("Outstanding Rent") + ":Currency:170",
		("Pre-rent Balance") + ":Currency:170",
		("Outstanding Received") + ":Currency:180"
	]

def get_data(filters):
	cond=''
	if filters.get("rental_official"):
		cond = " and rb.rental_focal='{}'".format(filters.get("rental_official"))

	query = """
		select 
			tenant, 
			tenant_name, 
			GROUP_CONCAT(DISTINCT(name) SEPARATOR ', ') rental_bill,
			(case 
				when rb_posting_date between '{from_date}' and '{to_date}' then sum(rb_rent_amount)
				else 0
			end) total_rent_amount,
			(case 
				when rb_posting_date between '{from_date}' and '{to_date}' then sum(rpd_received_amount)
				else 0
			end) total_received_amount,
			(case 
				when rb_posting_date between '{from_date}' and '{to_date}' then sum(rpd_pre_rent_amount)
				else 0
			end) total_pre_rent_amount,
			(case 
				when rb_posting_date between '{from_date}' and '{to_date}' then sum(rb_adjusted_amount)
				else 0
			end) total_adjusted_amount,
			(case 
				when rb_posting_date between '{from_date}' and '{to_date}' then sum(rpd_excess_amount)
				else 0
			end) total_excess_amount,
			(case 
				when rb_posting_date between '{from_date}' and '{to_date}' then sum(rpd_tds_amount)
				else 0
			end) total_tds_amount,
			(case 
				when rb_posting_date between '{from_date}' and '{to_date}' then sum(rpd_rent_write_off_amount)
				else 0
			end) total_rent_write_off_amount,
			(case 
				when rb_posting_date between '{from_date}' and '{to_date}' then sum(rpd_penalty_amount)
				else 0
			end) total_penalty_amount,
			(case 
				when rb_posting_date between '{from_date}' and '{to_date}' then sum(rpd_discount_amount)
				else 0
			end) total_discount_amount,
			(case 
				when rb_posting_date between '{from_date}' and '{to_date}'
				then sum(rpd_received_amount) + sum(rpd_property_management_amount) + sum(rpd_pre_rent_amount) + sum(rpd_excess_amount) + sum(rpd_penalty_amount) - sum(rpd_discount_amount)
				else 0
			end) total_rent_received,
			(case 
				when rb_posting_date between '{from_date}' and '{to_date}'
				then sum(rb_receivable_amount) - sum(rpd_received_amount) - sum(rpd_property_management_amount) - sum(rb_adjusted_amount) - sum(rpd_rent_write_off_amount) - sum(rpd_tds_amount)
				else 0
			end) outstanding_amount,
			(case 
				when rb_posting_date between '{from_date}' and '{to_date}'
				then sum(rpd_pre_rent_amount) - sum(rb_adjusted_amount)
				else 0
			end) pre_rent_balance,
			(case 
				when rb_posting_date < '{from_date}' then sum(rpd_received_amount)
				else 0
			end) outstanding_received
		from (
			select 
				rb.name, rb.tenant, rb.tenant_name,
				rb.receivable_amount rb_receivable_amount,
				rb.rent_amount rb_rent_amount,
				rb.adjusted_amount rb_adjusted_amount,
				rb.posting_date rb_posting_date,
			
				IFNULL(sum(rpd.pre_rent_amount), 0) rpd_pre_rent_amount,
				IFNULL(sum(rpd.tds_amount), 0) rpd_tds_amount,
				IFNULL(sum(rpd.excess_amount), 0) rpd_excess_amount,
				IFNULL(sum(rpd.penalty_amount), 0) rpd_penalty_amount,
				IFNULL(sum(rpd.rent_write_off_amount), 0) rpd_rent_write_off_amount,
				IFNULL(sum(rpd.received_amount), 0) rpd_received_amount,
				IFNULL(sum(rpd.discount_amount), 0) rpd_discount_amount,
				IFNULL(sum(rpd.property_management_amount), 0) rpd_property_management_amount
			from `tabRental Bill` rb
			inner join `tabRental Payment Details` rpd on rb.name=rpd.parent and rpd.payment_date between '{from_date}' and '{to_date}'
			where rb.docstatus=1 and rb.gl_entry = 1 {cond} group by name order by rb.name
		) as x group by tenant
		""".format(from_date=filters.get("from_date"), to_date=filters.get("to_date"), cond=cond)
	
	# frappe.throw(str(query))
	retult = frappe.db.sql(query)

	return retult