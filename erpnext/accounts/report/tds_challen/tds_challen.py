# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt, getdate, formatdate, cstr, cint

def execute(filters=None):
	validate_filters(filters)
	columns = get_columns()
	queries = construct_query(filters)
	data = get_data(queries, filters)

	return columns, data

def get_data(query, filters):
	data = []
	data1 = []
	datas = frappe.db.sql(query, as_dict=True)
	for d in datas:
		remittance_ref = ""
		for a in frappe.db.sql("""
			SELECT 
				r.name
			FROM `tabTDS Remittance` r, `tabTDS Remittance Item` ri
			WHERE r.name = ri.parent
				AND ri.invoice_no = "{}"
				AND ri.party = "{}"
				AND r.docstatus = 1
			""".format(d.bill_no, d.vendor), as_dict=True):
			remittance_ref = a.name
		status = 'Not Paid'
		rrco_ref = ""
		bil = frappe.db.sql("""
			SELECT 
				name, 
				tds_receipt_update 
			FROM `tabTDS Receipt Entry` 
				WHERE (bill_no = "{0}") 
				AND supplier = "{1}"
			""".format(d.bill_no, d.vendor), as_dict=True)
		if bil:
			status = 'Paid'
			for x in bil:
				rrco_ref = x.tds_receipt_update
		if filters.get("cost_center") and d.cost_center == filters.get("cost_center"):
			row = [d.vendor, d.supplier_tpn_no, d.bill_no, d.bill_date, d.tds_taxable_amount, cint(d.tds_rate), d.tds_amount, d.cost_center, status, remittance_ref, rrco_ref]
			data.append(row)
		else:
			row = [d.vendor, d.supplier_tpn_no, d.bill_no, d.bill_date, d.tds_taxable_amount, cint(d.tds_rate), d.tds_amount, d.cost_center, status, remittance_ref, rrco_ref]
			data1.append(row)
	if filters.get("cost_center"):
		return data
	else:
		return data1

def construct_query(filters=None):
	if not filters.tds_rate:
		filters.tds_rate = '2'
		pi_cost_center = "1 = 1"
		dp_cost_center = "1 = 1"

	if filters.get("cost_center"):
		pi_cost_center = "p.tds_cost_center = '{0}'".format(filters.get("cost_center"))
		dp_cost_center = "d.cost_center = '{0}'".format(filters.get("cost_center"))

	query = """
		SELECT 
			s.supplier_tpn_no, 
			s.name as vendor, 
			p.name as bill_no, 
			p.posting_date as bill_date, 
			p.total as tds_taxable_amount, 
			t.rate as tds_rate, 
			t.tax_amount as tds_amount, 
			p.cost_center as cost_center  		
		FROM `tabPurchase Invoice` as p	
		INNER JOIN `tabPurchase Taxes and Charges` t 
			on p.name = t.parent
		INNER JOIN `tabSupplier` as s
			on p.supplier = s.name
		WHERE p.docstatus = 1 AND t.tax_amount > 0 
			AND p.posting_date BETWEEN '{0}' AND '{1}'
			AND t.rate = '{2}'
		UNION 
			SELECT 
				(
				SELECT supplier_tpn_no from `tabSupplier` where name = di.party) as supplier_tpn_no, 
				di.party as vendor, 
				d.name as bill_no, 
				d.posting_date as bill_date,			
				di.taxable_amount as tds_taxable_amount, 
				d.tax_withholding_category as tds_rate, 
				di.tax_amount as tds_amount, 
				di.cost_center as cost_center 
			FROM `tabJournal Entry` as d
				LEFT JOIN `tabJournal Entry Account` as di on di.parent = d.name
				WHERE d.docstatus = 1 
				AND di.tax_amount > 0 
				AND d.posting_date BETWEEN '{0}' AND '{1}'  
				AND di.rate = '{2}'
				AND di.tax_amount > 0
			""".format(str(filters.from_date), str(filters.to_date), filters.tds_rate)
   
	return query
   
	# query = """
	# 		SELECT s.vendor_tpn_no, s.name as vendor, p.name as bill_no, p.posting_date as bill_date, 
   	# 		p.total as tds_taxable_amount, 
   	# 		t.rate as tds_rate, t.tax_amount as tds_amount, p.cost_center as cost_center  
	# 		FROM `tabPurchase Invoice` as p
   	# 		inner join `tabPurchase Taxes and Charges` t 
    #         on p.name = t.parent
    #         inner join `tabSupplier` as s
    #         on p.supplier = s.name
	# 		WHERE p.docstatus = 1 AND t.tax_amount > 0 
	# 		AND p.posting_date BETWEEN '{0}' AND '{1}'
	# 		AND t.rate = '{2}'
	# 		UNION 
	# 		SELECT 
   	# 			(select vendor_tpn_no from `tabSupplier` where name = di.party) as vendor_tpn_no, 
	# 			di.party as vendor, d.name as bill_no, d.posting_date as bill_date,
    # 			di.taxable_amount as tds_taxable_amount, d.tds_percent as tds_rate, 
    #    			di.tds_amount as tds_amount, d.cost_center as cost_center 
	# 		FROM `tabDirect Payment` as d
	# 		LEFT JOIN `tabDirect Payment Item` as di on di.parent = d.name
	# 		WHERE d.docstatus = 1 
	# 		AND d.tds_amount > 0 AND d.posting_date BETWEEN '{0}' AND '{1}'  
	# 		AND d.tds_percent = '{2}'
	# 		AND di.tds_amount > 0
	# 		""".format(str(filters.from_date), str(filters.to_date), filters.tds_rate)
   
	# return query

def validate_filters(filters):
	if not filters.fiscal_year:
		frappe.throw(_("Fiscal Year {0} is required").format(filters.fiscal_year))

	fiscal_year = frappe.db.get_value("Fiscal Year", filters.fiscal_year, ["year_start_date", "year_end_date"], as_dict=True)
	if not fiscal_year:
		frappe.throw(_("Fiscal Year {0} does not exist").format(filters.fiscal_year))
	else:
		filters.year_start_date = getdate(fiscal_year.year_start_date)
		filters.year_end_date = getdate(fiscal_year.year_end_date)
	
	if filters.year_start_date < fiscal_year.year_start_date and filters.year_end_date > fiscal_year.year_end_date:
		frappe.throw("Start Date or End Date selected is not within the selected Fiscal Year <b>{}</b>".format(filters.fiscal_year))

	if not filters.from_date:
		filters.from_date = filters.year_start_date

	if not filters.to_date:
		filters.to_date = filters.year_end_date

	filters.from_date = getdate(filters.from_date)
	filters.to_date = getdate(filters.to_date)

	if filters.from_date > filters.to_date:
		frappe.throw(_("From Date cannot be greater than To Date"))

	if (filters.from_date < filters.year_start_date) or (filters.from_date > filters.year_end_date):
		frappe.msgprint(_("From Date should be within the Fiscal Year. Assuming From Date = {0}")\
			.format(formatdate(filters.year_start_date)))

		filters.from_date = filters.year_start_date

	if (filters.to_date < filters.year_start_date) or (filters.to_date > filters.year_end_date):
		frappe.msgprint(_("To Date should be within the Fiscal Year. Assuming To Date = {0}")\
			.format(formatdate(filters.year_end_date)))
		filters.to_date = filters.year_end_date

def get_columns():
	return [
		{
		  "fieldname": "vendor_name",
		  "label": "Vendor Name",
		  "fieldtype": "Data",
		  "width": 250
		},
		{
		  "fieldname": "tpn_no",
		  "label": "TPN Number",
		  "fieldtype": "Data",
		  "width": 100
		},
		{
		  "fieldname": "invoice_no",
		  "label": "Invoice No",
		  "fieldtype": "Link",
		  "options":"Purchase Invoice",
		  "width": 200
		},
		{
		  "fieldname": "Invoice_date",
		  "label": "Invoice Date",
		  "fieldtype": "Date",
		  "width": 100
		},
		{
		  "fieldname": "bill_amount",
		  "label": "Bill Amount",
		  "fieldtype": "Currency",
		  "width": 120
		},
		{
		  "fieldname": "tds_rate",
		  "label": "TDS Rate(%)",
		  "fieldtype": "Data",
		  "width": 80
		},
		{
		  "fieldname": "tds_amount",
		  "label": "TDS Amount",
		  "fieldtype": "Currency",
		  "width": 120
		},
		{
	  	"fieldname": "cost_center",
	   	"label": "Cost Center",
	    "fieldtype": "Link",
		"options": "Cost Center",
		"width": 150
		},
		{
		"fieldname": "status",
		"label": "Status",
		"fieldtype": "Data",
		"width": 80
		},
		{
		"fieldname": "remittance",
		"label": "Remittance",
		"fieldtype": "Link",
		"options": "TDS Remittance",
		"width": 110
		},
    	{
		"fieldname": "rrco",
		"label": "TDS Receipt Update",
		"fieldtype": "Link",
		"options": "TDS Receipt Update",
		"width": 120
		},
	
		        
	]
