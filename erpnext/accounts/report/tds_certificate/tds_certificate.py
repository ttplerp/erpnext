# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt

# changes made by dorji 05/07/22 for issue #1911
# added line 91, added cases from line 93-103, added line 112, added cases from line 114-123, added line 136

def execute(filters=None):
	currency_symbol=''
	if filters.currency:
		currency_symbol= frappe.db.sql("""select symbol from `tabCurrency` where name=%s""",(filters.currency))[0][0]
	columns = get_columns(currency_symbol)

	data = get_data(filters)
	data.append(calculate_total(data))
	return columns, data
	
def get_columns(currency_symbol):
	return [
		{
			"fieldname":"posting_date",
			"label":_("Invoice Date"),
			"fieldtype":"Date",
			"width":120
		},
		{
			"fieldname":"tds_taxable_amount",
			"label":_("Gross Amount(" + currency_symbol + ")"),
			"fieldtype":"Float",
			"width":140
		},
		{
			"fieldname":"tds_rate",
			"label":_("TDS Rate(%)"),
			"fieldtype":"Data",
			"width":100
		},
		{
			"fieldname":"tds_amount",
			"label":_("TDS Amount(" + currency_symbol + ")"),
			"fieldtype":"Float",
			"width":140
		},
		{
			"fieldname":"cheque_no",
			"label":("Cheque Number"),
			"fieldtype":"Data",
			"width":100
		},
		{
			"fieldname":"cheque_date",
			"label":("Cheque Date"),
			"fieldtype":"Date",
			"width":100
		},
		{
			"fieldname":"receipt_number",
			"label":("Receipt Number"),
			"fieldtype":"Data",
			"width":100
		},
		{
			"fieldname":"receipt_date",
			"label":("Receipt Date"),
			"fieldtype":"Date",
			"width":100,
		}
	]
def calculate_total(data):
	total_amount = total_tds_amount = 0
	for d in data:
		total_amount += flt(d.tds_taxable_amount)
		total_tds_amount += flt(d.tds_amount)
	row = frappe._dict({
		'tds_taxable_amount':total_amount,
		'tds_amount':total_tds_amount
	})
	return row

# def get_data(filters):
# 	pass
	
def get_data(filters):
	query = query1 = ''
	je_entries = []
	if filters.party_type == "Supplier" and filters.supplier:
		# if frappe.db.get_single_value("Accounts Settings", "book_purchase_tax_charges") == "Purchase Invoice":
		query = """SELECT a.posting_date, t.total as tds_taxable_amount, round(t.rate) as tds_rate, t.tax_amount as tds_amount,
						b.cheque_no, b.cheque_date, 
						b.receipt_number, b.receipt_date 
						FROM `tabPurchase Invoice` AS a
						inner join `tabPurchase Taxes and Charges` t 
						on a.name = t.parent and t.rate in (2,3,5,10)
						inner join `tabTDS Receipt Entry` AS b
						on a.name = b.invoice_no
						AND a.posting_date BETWEEN '{0}' AND '{1}'
						AND a.supplier = '{2}'
						AND a.currency = '{3}' """.format(filters.from_date, filters.to_date, filters.supplier, filters.currency)
		# else:
		# 	query = """select t.posting_date,
		# 			case when t.currency != "BTN" 
		# 				then t1.base_total + t1.base_tax_amount 
		# 				else t1.total end 
		# 			as tds_taxable_amount,
		# 			round(t1.rate) as tds_rate,
		# 			case when t1.base_tax_amount > 0 
		# 				then t1.base_tax_amount 
		# 				else t1.tax_amount end 
		# 			as tds_amount,
		# 			b.cheque_number, b.cheque_date,
		# 			b.receipt_number, b.receipt_date 
		# 			FROM `tabPayment Entry` as t
		# 			inner join `tabPurchase Taxes and Charges` t1
		# 			on t.name = t1.parent
		# 			inner join `tabRRCO Receipt Entries` AS b
		# 			on t.name = b.purchase_invoice
		# 			AND t.posting_date BETWEEN '{0}' AND '{1}'
		# 			AND t.party = '{2}'
		# 			AND t.currency = '{3}'""".format(filters.from_date, filters.to_date, filters.supplier, filters.currency)
		query1 = """SELECT  
						d.posting_date, d.name,
						case when d.currency != "BTN"
							then di.taxable_amount
							else 0 
						end 
						as tds_taxable_amount, 
						d.tds_percent as tds_rate,  
						case when d.currency != "BTN"
							then di.tds_amount
							else 0 
						end
						as tds_amount,
						(select cheque_no from `tabTDS Receipt Entry` rr where rr.invoice_no = d.name limit 1) as cheque_no,
						(select cheque_date from `tabTDS Receipt Entry` rr where rr.invoice_no = d.name limit 1) as cheque_date,
						(select receipt_number from `tabTDS Receipt Entry` rr where rr.invoice_no = d.name limit 1) as receipt_number,
						(select receipt_date from `tabTDS Receipt Entry` rr where rr.invoice_no = d.name limit 1) as receipt_date
					FROM 
						`tabDirect Payment` AS d
					INNER JOIN 
						`tabDirect Payment Item` AS di ON di.parent = d.name 
					WHERE d.posting_date BETWEEN '{0}' AND '{1}'
					AND 
						di.party = '{2}'
					AND EXISTS(select 1 from `tabTDS Receipt Entry` rr where rr.invoice_no = d.name)
					AND d.currency = '{3}'
					""".format(filters.from_date, filters.to_date, filters.supplier, filters.currency)
		je_entries = get_journal_entries(filters)
	elif filters.party_type == "Customer" and filters.customer:
		query = []
		# query = """SELECT 
		# 				b.posting_date,i.taxable_amount as tds_taxable_amount,
		# 				 i.tds_percent as tds_rate,	i.tds_amount, 
		# 				rr.cheque_number,  rr.cheque_date, rr.receipt_number, rr.receipt_date  
		# 			FROM `tabBTL Sales` b 
		# 			INNER JOIN 
		# 				`tabBTL Sales Item` i ON b.name = i.parent
		# 			INNER JOIN
		# 				`tabRRCO Receipt Entries` AS rr ON rr.purchase_invoice = b.name
		# 			WHERE b.required_commission = 1 
		# 			AND b.docstatus = 1
		# 			AND b.posting_date BETWEEN '{0}' AND '{1}'
		# 			AND i.tds_amount > 0 
		# 			AND rr.supplier = '{2}'
		# 			AND b.customer = '{2}'
		# """.format(str(filters.from_date), str(filters.to_date), filters.customer)
		# query1 = """SELECT i.transaction_date, i.payable_amount as tds_taxable_amount, 
		# 					2 as tds_rate, i.tds as tds_amount, rr.cheque_number,  
		# 					rr.cheque_date, rr.receipt_number, rr.receipt_date  
		# 			FROM `tabBilling Data` i 
		# 			INNER JOIN
		# 			`tabRRCO Receipt Entries` AS rr ON rr.purchase_invoice = i.parent 
		# 			WHERE i.parenttype = 'Airtime Collections'
		# 			AND i.docstatus = 1
		# 			AND i.tds > 0
		# 			AND i.transaction_date BETWEEN '{0}' AND '{1}'
		# 			AND rr.supplier = '{2}'
		# 			AND i.customer = '{2}'
		# """.format(str(filters.from_date), str(filters.to_date), filters.customer)
	if not query:
		return []
	# return frappe.db.sql(query,as_dict=1) + frappe.db.sql(query1,as_dict=1) + je_entries
	return frappe.db.sql(query,as_dict=1) + je_entries

def get_journal_entries(filters):
	return frappe.db.sql("""
			SELECT t.posting_date, t1.taxable_amount as tds_taxable_amount,
				t1.rate tds_rate, t1.tax_amount as tds_amount, rr.cheque_no,
				rr.cheque_date, rr.receipt_number, rr.receipt_date
			FROM `tabJournal Entry` t
			JOIN `tabJournal Entry Account` t1 ON t1.parent = t.name
			INNER JOIN `tabTDS Receipt Entry` AS rr ON rr.invoice_no = t.name
			WHERE t.posting_date BETWEEN '{from_date}' AND '{to_date}' 
			AND t.docstatus = 1
			AND t1.apply_tds = 1
			AND t1.party = "{supplier}"
			group by t1.name
			
		""".format(supplier = filters.supplier, from_date = str(filters.from_date), to_date = str(filters.to_date)), as_dict=True)