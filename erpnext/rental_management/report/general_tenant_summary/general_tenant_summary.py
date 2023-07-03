# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _, _dict
from frappe.utils import cstr, getdate, flt


def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data

def get_columns():
	columns = [
			{
				"label": _("Tenant Code"),
				"fieldname": "tenant",
				"fieldtype": "Data",
				"width": 120,
			},
			{
				"label": _("Tenant"),
				"fieldname": "tenant_name",
				"fieldtype": "Data",
				"width": 150,
			},
			{
				"label": _("Rental Bill"),
				"fieldname": "rental_bill",
				"fieldtype": "Data",
				"width": 150,
			},
			{
				"label": _("Receivable Amount"),
				"fieldname": "total_receivable_amount",
				"fieldtype": "Currency",
				"width": 160,
			},
			{
				"label": _("Rental Income"),
				"fieldname": "total_rent_amount",
				"fieldtype": "Currency",
				"width": 120,
			},
			{
				"label": _("Rent Received"),
				"fieldname": "total_received_amount",
				"fieldtype": "Currency",
				"width": 120,
			},
			{
				"label": _("Property Mgt. Amount"),
				"fieldname": "total_prop_mgt_amount",
				"fieldtype": "Currency",
				"width": 150,
			},
			{
				"label": _("Pre-rent"),
				"fieldname": "total_pre_rent_amount",
				"fieldtype": "Currency",
				"width": 120,
			},
			{
				"label": _("Adjusted Amount"),
				"fieldname": "total_adjusted_amount",
				"fieldtype": "Currency",
				"width": 150,
			},
			{
				"label": _("Excess Rent"),
				"fieldname": "total_excess_amount",
				"fieldtype": "Currency",
				"width": 100,
			},
			{
				"label": _("TDS"),
				"fieldname": "total_tds_amount",
				"fieldtype": "Currency",
				"width": 100,
			},
			{
				"label": _("Rent Write-off"),
				"fieldname": "total_rent_write_off_amount",
				"fieldtype": "Currency",
				"width": 160,
			},
			{
				"label": _("Penalty"),
				"fieldname": "total_penalty_amount",
				"fieldtype": "Currency",
				"width": 100,
			},
			{
				"label": _("Discount"),
				"fieldname": "total_discount_amount",
				"fieldtype": "Currency",
				"width": 100,
			},
			{
				"label": _("Total Rent Received"),
				"fieldname": "total_rent_received",
				"fieldtype": "Currency",
				"width": 170,
			},
			{
				"label": _("Outstanding Rent"),
				"fieldname": "outstanding_amount",
				"fieldtype": "Currency",
				"width": 170,
			},
			{
				"label": _("Pre-rent Balance"),
				"fieldname": "pre_rent_balance",
				"fieldtype": "Currency",
				"width": 150,
			},
			{
				"label": _("Outstanding Received"),
				"fieldname": "outstanding_received",
				"fieldtype": "Currency",
				"width": 170,
			},
		]
	
	return columns

def get_data(filters):
	# cond=''
	# if filters.get("rental_official"):
	# 	cond = " and rb.rental_focal='{}'".format(filters.get("rental_official"))

	# query = """
	# 	select 
	# 		tenant, 
	# 		tenant_name, 
	# 		GROUP_CONCAT(DISTINCT(name) SEPARATOR ', ') rental_bill,
			# (case 
			# 	when rb_posting_date between '{from_date}' and '{to_date}' then sum(rb_rent_amount)
			# 	else 0
			# end) total_rent_amount,
			# (case 
			# 	when rb_posting_date between '{from_date}' and '{to_date}' then sum(rpd_received_amount)
			# 	else 0
			# end) total_received_amount,
			# (case 
			# 	when rb_posting_date between '{from_date}' and '{to_date}' then sum(rpd_pre_rent_amount)
			# 	else 0
			# end) total_pre_rent_amount,
			# (case 
			# 	when rb_posting_date between '{from_date}' and '{to_date}' then sum(rb_adjusted_amount)
			# 	else 0
			# end) total_adjusted_amount,
			# (case 
			# 	when rb_posting_date between '{from_date}' and '{to_date}' then sum(rpd_excess_amount)
			# 	else 0
			# end) total_excess_amount,
			# (case 
			# 	when rb_posting_date between '{from_date}' and '{to_date}' then sum(rpd_tds_amount)
			# 	else 0
			# end) total_tds_amount,
			# (case 
			# 	when rb_posting_date between '{from_date}' and '{to_date}' then sum(rpd_rent_write_off_amount)
			# 	else 0
			# end) total_rent_write_off_amount,
			# (case 
			# 	when rb_posting_date between '{from_date}' and '{to_date}' then sum(rpd_penalty_amount)
			# 	else 0
			# end) total_penalty_amount,
			# (case 
			# 	when rb_posting_date between '{from_date}' and '{to_date}' then sum(rpd_discount_amount)
			# 	else 0
			# end) total_discount_amount,
			# (case 
			# 	when rb_posting_date between '{from_date}' and '{to_date}'
			# 	then sum(rpd_received_amount) + sum(rpd_property_management_amount) + sum(rpd_pre_rent_amount) + sum(rpd_excess_amount) + sum(rpd_penalty_amount) - sum(rpd_discount_amount)
			# 	else 0
			# end) total_rent_received,
			# (case 
			# 	when rb_posting_date between '{from_date}' and '{to_date}'
			# 	then sum(rb_receivable_amount) - sum(rpd_received_amount) - sum(rpd_property_management_amount) - sum(rb_adjusted_amount) - sum(rpd_rent_write_off_amount) - sum(rpd_tds_amount)
			# 	else 0
			# end) outstanding_amount,
			# (case 
			# 	when rb_posting_date between '{from_date}' and '{to_date}'
			# 	then sum(rpd_pre_rent_amount) - sum(rb_adjusted_amount)
			# 	else 0
			# end) pre_rent_balance,
			# (case 
			# 	when rb_posting_date < '{from_date}' then sum(rpd_received_amount)
			# 	else 0
			# end) outstanding_received
	# 	from (
	# 		select 
	# 			rb.name, rb.tenant, rb.tenant_name,
	# 			rb.receivable_amount rb_receivable_amount,
	# 			rb.rent_amount rb_rent_amount,
	# 			rb.adjusted_amount rb_adjusted_amount,
	# 			rb.posting_date rb_posting_date,
				
	# 			rpd.payment_date rpd_payment_date,
	# 			IFNULL(sum(rpd.pre_rent_amount), 0) rpd_pre_rent_amount,
	# 			IFNULL(sum(rpd.tds_amount), 0) rpd_tds_amount,
	# 			IFNULL(sum(rpd.excess_amount), 0) rpd_excess_amount,
	# 			IFNULL(sum(rpd.penalty_amount), 0) rpd_penalty_amount,
	# 			IFNULL(sum(rpd.rent_write_off_amount), 0) rpd_rent_write_off_amount,
	# 			IFNULL(sum(rpd.received_amount), 0) rpd_received_amount,
	# 			IFNULL(sum(rpd.discount_amount), 0) rpd_discount_amount,
	# 			IFNULL(sum(rpd.property_management_amount), 0) rpd_property_management_amount
	# 		from `tabRental Bill` rb
	# 		left join `tabRental Payment Details` rpd on rb.name=rpd.parent and rpd.payment_date between '{from_date}' and '{to_date}'
	# 		where rb.docstatus=1 and rb.gl_entry = 1 {cond} group by name order by rb.name
	# 	) as x where 1=1 and (rb_posting_date between '{from_date}' and '{to_date}' or rpd_payment_date between '{from_date}' and '{to_date}')  group by tenant
	# 	""".format(from_date=filters.get("from_date"), to_date=filters.get("to_date"), cond=cond)
	
	data = []
	tenant_rental_map = frappe._dict()
	rental_list = get_all_bills(filters);
	for d in rental_list:
		tenant_rental_map.setdefault(d.tenant, []).append(d)
	
	# frappe.throw("<pre>{}</pre>".format(frappe.as_json(tenant_rental_map)))
	from_date, to_date = getdate(filters.from_date), getdate(filters.to_date)
	for key, value in tenant_rental_map.items():
		filter_data = frappe._dict({
			"tenant": key,
			"tenant_name": frappe.db.get_value("Tenant Information", key, "tenant_name"),
			"rental_bill": '',
			"total_receivable_amount": 0.0,
			"total_rent_amount": 0.0,
			"total_received_amount": 0.0,
			"total_prop_mgt_amount": 0.0,
			"total_pre_rent_amount": 0.0,
			"total_adjusted_amount": 0.0,
			"total_excess_amount": 0.0,
			"total_tds_amount": 0.0,
			"total_rent_write_off_amount": 0.0,
			"total_penalty_amount": 0.0,
			"total_discount_amount": 0.0,
			"total_rent_received": 0.0,
			"outstanding_amount": 0.0,
			"pre_rent_balance": 0.0,
			"outstanding_received": 0.0,
		})

		""" opening values """

		total_receivalble_amt = total_prop_mgt_amt = 0
		for d in value:
			# if d.rb_posting_date < to_date:
			# 	filter_data['rental_bill'] += str(d.name) + ", "
			if d.rb_posting_date < from_date:
				filter_data['total_pre_rent_amount'] 	= flt(filter_data['total_pre_rent_amount'] + (d.rpd_pre_rent_amount - d.rb_adjusted_amount), 2)
			elif d.rb_posting_date >= from_date and d.rb_posting_date <= to_date:
				# if d.rb_posting_date >= from_date and d.rb_posting_date <= to_date:
				filter_data['rental_bill'] += str(d.name) + ", "
				filter_data['total_rent_amount'] 		= flt(filter_data['total_rent_amount'] + d.rb_rent_amount, 2)
				filter_data['total_received_amount'] 	= flt(filter_data['total_received_amount'] + d.rpd_received_amount, 2)
				filter_data['total_pre_rent_amount'] 	= flt(filter_data['total_pre_rent_amount'] + d.rpd_pre_rent_amount, 2)
				filter_data['total_adjusted_amount'] 	= flt(filter_data['total_adjusted_amount'] + d.rb_adjusted_amount, 2)
				filter_data['total_excess_amount'] 		= flt(filter_data['total_excess_amount'] + d.rpd_excess_amount, 2)
				filter_data['total_tds_amount'] 		= flt(filter_data['total_tds_amount'] + d.rpd_tds_amount, 2)
				filter_data['total_rent_write_off_amount'] 	= flt(filter_data['total_rent_write_off_amount'] + d.rpd_rent_write_off_amount, 2)
				filter_data['total_penalty_amount'] 	= flt(filter_data['total_penalty_amount'] + d.rpd_penalty_amount, 2)
				filter_data['total_discount_amount'] 	= flt(filter_data['total_discount_amount'] + d.rpd_discount_amount, 2)
				filter_data['total_receivable_amount'] 	= flt(filter_data['total_receivable_amount'] + d.rb_receivable_amount, 2)
				filter_data['total_prop_mgt_amount'] 	= flt(filter_data['total_prop_mgt_amount'] + d.rpd_property_management_amount, 2)
				
			if d.rb_posting_date < from_date and d.rpd_payment_date: 
				if d.rpd_payment_date >= from_date and d.rpd_payment_date <= to_date:
					filter_data['rental_bill'] += str(d.name) + ", "
					filter_data['outstanding_received'] = flt(filter_data['outstanding_received'] + d.rpd_received_amount, 2)

		filter_data['total_rent_received'] = flt(filter_data['total_received_amount'] + filter_data['total_prop_mgt_amount'] + filter_data['total_pre_rent_amount'] + filter_data['total_excess_amount'] + filter_data['total_penalty_amount'] - filter_data['total_discount_amount'], 2)
		filter_data['outstanding_amount'] = flt(filter_data['total_receivable_amount'] - filter_data['total_received_amount'] - filter_data['total_prop_mgt_amount'] - filter_data['total_adjusted_amount'] - filter_data['total_rent_write_off_amount'] - filter_data['total_tds_amount'], 2)
		filter_data['pre_rent_balance'] = flt(filter_data['total_pre_rent_amount'] - filter_data['total_adjusted_amount'], 2)

		data.append(filter_data)

	return data

	# and rpd.payment_date between '{from_date}' and '{to_date}'
def get_all_bills(filters):
	cond=''
	if filters.get("rental_official"):
		cond = " and rb.rental_focal='{}'".format(filters.get("rental_official"))
	if filters.get("ministyr_agency"):
		cond = " and rb.ministry_agency='{}'".format(filters.get("ministyr_agency"))

	query = """select 
				rb.name, rb.tenant, rb.tenant_name,
				rb.receivable_amount rb_receivable_amount,
				rb.rent_amount rb_rent_amount,
				rb.adjusted_amount rb_adjusted_amount,
				rb.posting_date rb_posting_date,
				
				rpd.payment_date rpd_payment_date,
				IFNULL(sum(rpd.pre_rent_amount), 0) rpd_pre_rent_amount,
				IFNULL(sum(rpd.tds_amount), 0) rpd_tds_amount,
				IFNULL(sum(rpd.excess_amount), 0) rpd_excess_amount,
				IFNULL(sum(rpd.penalty_amount), 0) rpd_penalty_amount,
				IFNULL(sum(rpd.rent_write_off_amount), 0) rpd_rent_write_off_amount,
				IFNULL(sum(rpd.received_amount), 0) rpd_received_amount,
				IFNULL(sum(rpd.discount_amount), 0) rpd_discount_amount,
				IFNULL(sum(rpd.property_management_amount), 0) rpd_property_management_amount
			from `tabRental Bill` rb
			left join `tabRental Payment Details` rpd on rb.name=rpd.parent and rpd.payment_date <= '{to_date}'
			where rb.docstatus=1 and rb.gl_entry = 1 {cond} group by name order by rb.name
		""".format(from_date=filters.get("from_date"), to_date=filters.get("to_date"), cond=cond)
	
	result = frappe.db.sql(query, as_dict=1)
	return result