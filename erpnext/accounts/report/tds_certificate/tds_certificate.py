# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt

def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data
def get_data(filters):
	data = []
	conditions = get_condition(filters)
	for d in frappe.db.sql('''
			SELECT ti.party, ti.posting_date, ti.bill_amount, t.tax_withholding_category, 
				ti.tds_amount, t.cheque_no, t.cheque_date, ti.invoice_no, ti.invoice_type,
				t.tds_receipt_number, t.tds_receipt_date
			FROM `tabTDS Receipt Update` t INNER JOIN `tabTDS Remittance Item` ti ON t.name = ti.parent
			WHERE t.docstatus = 1 AND t.purpose = 'Other Invoice' {condition}
		'''.format(condition=conditions), as_dict=True):
		match d.invoice_type:
			case "Purchase Invoice":
				d.update({
					"tds_rate": frappe.db.get_value("Purchase Taxes and Charges",{"parent":d.invoice_no},"rate")
				})
			case "Journal Entry":
				d.update({
					"tds_rate": frappe.db.get_value("Journal Entry Account",{"parent":d.invoice_no,"tax_amount":(">",0)},"rate")
				})
			case "Payment Entry":
				d.update({
					"tds_rate": frappe.db.get_value("Advance Taxes and Charges",{"parent":d.invoice_no,"tax_amount":(">",0)},"rate")
				})
			case "Transporter Invoice":
				d.update({
					"tds_rate": frappe.db.get_value("Transporter Invoice Deduction",{"parent":d.invoice_no,"amount":(">",0),"deduction_type":"TDS Deduction"},"percent")
				})
			case "EME Invoice":
				d.update({
					"tds_rate": frappe.db.get_value("EME Invoice",{"tds_amount":(">",0),"name":d.invoice_no},"tds_percent")
				})
		data.append(d)
	return data
def get_condition(filters):
	conditions = []
	if filters.get("party_type"):
		conditions.append("ti.party_type = '{}'".format(filters.get("party_type")))
	if filters.get("supplier") and filters.get("party_type") == "Supplier":
		conditions.append("ti.party = '{}'".format(filters.get("supplier")))
	if filters.get("customer") and filters.get("party_type") == "Customer":
		conditions.append("ti.party = '{}'".format(filters.get("supplier")))
	if filters.get("from_date") > filters.get("to_date"):
		frappe.throw("To Date cannot be greater than From Date")
	if filters.get("from_date") and filters.get("to_date"):
		conditions.append("ti.posting_date between '{}' and '{}'".format(filters.get("from_date"),filters.get("to_date")))

	return "and {}".format(" and ".join(conditions)) if conditions else ""
def get_columns():
	return [
		{
			"fieldname":"posting_date",
			"label":_("Invoice Date"),
			"fieldtype":"Date",
			"width":120
		},
		{
			"fieldname":"bill_amount",
			"label":_("Bill Amount"),
			"fieldtype":"Currency",
			"width":140
		},
		{
			"fieldname":"tds_rate",
			"label":_("TDS Rate(%)"),
			"fieldtype":"Percent",
			"width":130
		},
		{
			"fieldname":"tds_amount",
			"label":_("TDS Amount"),
			"fieldtype":"Currency",
			"width":140
		},
		{
			"fieldname":"cheque_no",
			"label":("Cheque Number"),
			"fieldtype":"Data",
			"width":140
		},
		{
			"fieldname":"cheque_date",
			"label":("Cheque Date"),
			"fieldtype":"Date",
			"width":120
		},
		{
			"fieldname":"tds_receipt_number",
			"label":("Receipt Number"),
			"fieldtype":"Data",
			"width":130
		},
		{
			"fieldname":"tds_receipt_date",
			"label":("Receipt Date"),
			"fieldtype":"Date",
			"width":120,
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

def get_datax(filters):
	query = query1 = ''
	je_entries = []
	if filters.customer_type == "Supplier" and filters.supplier:
		if frappe.db.get_single_value("Accounts Settings", "book_purchase_tax_charges") == "Purchase Invoice":
			query = """SELECT a.posting_date, t.total as tds_taxable_amount, round(t.rate) as tds_rate, t.tax_amount as tds_amount,
							b.cheque_number, b.cheque_date, 
							b.receipt_number, b.receipt_date 
							FROM `tabPurchase Invoice` AS a
							inner join `tabPurchase Taxes and Charges` t 
							on a.name = t.parent
							inner join `tabRRCO Receipt Entries` AS b
							on a.name = b.purchase_invoice
							AND a.posting_date BETWEEN '{0}' AND '{1}'
							AND a.supplier = '{2}'
							AND a.currency = '{3}' """.format(filters.from_date, filters.to_date, filters.supplier, filters.currency)
		else:
			query = """select t.posting_date,
					case when t.currency != "BTN" 
						then t1.base_total + t1.base_tax_amount 
						else t1.total end 
					as tds_taxable_amount,
					round(t1.rate) as tds_rate,
					case when t1.base_tax_amount > 0 
						then t1.base_tax_amount 
						else t1.tax_amount end 
					as tds_amount,
					b.cheque_number, b.cheque_date,
					b.receipt_number, b.receipt_date 
					FROM `tabPayment Entry` as t
					inner join `tabPurchase Taxes and Charges` t1
					on t.name = t1.parent
					inner join `tabRRCO Receipt Entries` AS b
					on t.name = b.purchase_invoice
					AND t.posting_date BETWEEN '{0}' AND '{1}'
					AND t.party = '{2}'
					AND t.currency = '{3}'""".format(filters.from_date, filters.to_date, filters.supplier, filters.currency)
		query1 = """SELECT  
						d.posting_date, d.name,
						case when d.currency != "BTN"
							then di.taxable_amount
							else di.base_taxable_amount end 
						as tds_taxable_amount, 
						d.tds_percent as tds_rate,  
						case when d.currency != "BTN"
							then di.tds_amount
							else di.base_tds_amount end
						as tds_amount,
						(select cheque_number from `tabRRCO Receipt Entries` rr where rr.purchase_invoice = d.name limit 1) as cheque_number,
						(select cheque_date from `tabRRCO Receipt Entries` rr where rr.purchase_invoice = d.name limit 1) as cheque_date,
						(select receipt_number from `tabRRCO Receipt Entries` rr where rr.purchase_invoice = d.name limit 1) as receipt_number,
						(select receipt_date from `tabRRCO Receipt Entries` rr where rr.purchase_invoice = d.name limit 1) as receipt_date
					FROM 
						`tabDirect Payment` AS d
					INNER JOIN 
						`tabDirect Payment Item` AS di ON di.parent = d.name 
					WHERE d.posting_date BETWEEN '{0}' AND '{1}'
					AND 
						di.party = '{2}'
					AND EXISTS(select 1 from `tabRRCO Receipt Entries` rr where rr.purchase_invoice = d.name and supplier = '{2}')
					AND d.currency = '{3}'
					""".format(filters.from_date, filters.to_date, filters.supplier, filters.currency)
		je_entries = get_journal_entries(filters)
	elif filters.customer_type == "Customer" and filters.customer:
		query = """SELECT 
						b.posting_date,i.taxable_amount as tds_taxable_amount,
						 i.tds_percent as tds_rate,	i.tds_amount, 
						rr.cheque_number,  rr.cheque_date, rr.receipt_number, rr.receipt_date  
					FROM `tabBTL Sales` b 
					INNER JOIN 
						`tabBTL Sales Item` i ON b.name = i.parent
					INNER JOIN
						`tabRRCO Receipt Entries` AS rr ON rr.purchase_invoice = b.name
					WHERE b.required_commission = 1 
					AND b.docstatus = 1
					AND b.posting_date BETWEEN '{0}' AND '{1}'
					AND i.tds_amount > 0 
					AND rr.supplier = '{2}'
					AND b.customer = '{2}'
		""".format(str(filters.from_date), str(filters.to_date), filters.customer)
		query1 = """SELECT i.transaction_date, i.payable_amount as tds_taxable_amount, 
							2 as tds_rate, i.tds as tds_amount, rr.cheque_number,  
							rr.cheque_date, rr.receipt_number, rr.receipt_date  
					FROM `tabBilling Data` i 
					INNER JOIN
					`tabRRCO Receipt Entries` AS rr ON rr.purchase_invoice = i.parent 
					WHERE i.parenttype = 'Airtime Collections'
					AND i.docstatus = 1
					AND i.tds > 0
					AND i.transaction_date BETWEEN '{0}' AND '{1}'
					AND rr.supplier = '{2}'
					AND i.customer = '{2}'
		""".format(str(filters.from_date), str(filters.to_date), filters.customer)
	if not query:
		return []
	return frappe.db.sql(query,as_dict=1) + frappe.db.sql(query1,as_dict=1) + je_entries

def get_journal_entries(filters):
	return frappe.db.sql("""
			SELECT t.posting_date, t2.debit as tds_taxable_amount,
				(CASE 
					WHEN t1.credit = ROUND(t2.debit*2/100,2) THEN 2
					WHEN t1.credit = ROUND(t2.debit*3/100,2) THEN 3
					WHEN t1.credit = ROUND(t2.debit*5/100,2) THEN 4
					WHEN t1.credit = ROUND(t2.debit*10/100,2) THEN 10
					ELSE 0
				END) tds_rate, t1.credit as tds_amount, rr.cheque_number,
				rr.cheque_date, rr.receipt_number, rr.receipt_date
			FROM `tabJournal Entry` t
			JOIN `tabJournal Entry Account` t1 ON t1.parent = t.name
			JOIN `tabJournal Entry Account` t2 ON t2.parent = t.name
					AND t2.debit > 0
					AND (
						t1.credit_in_currency = ROUND(t2.debit_in_currency*2/100,2)
						OR t1.credit_in_currency = ROUND(t2.debit_in_currency*3/100,2)
						OR t1.credit_in_currency = ROUND(t2.debit_in_currency*5/100,2)
						OR t1.credit_in_currency = ROUND(t2.debit_in_currency*10/100,2)
					)
			INNER JOIN `tabRRCO Receipt Entries` AS rr ON rr.purchase_invoice = t.name
			WHERE t.posting_date BETWEEN '{from_date}' AND '{to_date}' 
			AND t.docstatus = 1
			AND t1.credit > 0
			AND t2.party = "{supplier}"
			AND EXISTS(SELECT 1
				FROM `tabSingles` s
				WHERE s.doctype = 'Accounts Settings'
				AND s.field IN ('tds_2_account', 'tds_3_account', 'tds_5_account', 'tds_10_account')
				AND t1.account = s.value)
		""".format(supplier = filters.supplier, from_date = str(filters.from_date), to_date = str(filters.to_date)), as_dict=True)