# -*- coding: utf-8 -*-
# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt
from frappe.model.document import Document

class RRCOReceiptTool(Document):
	def validate(self):		
		self.get_invoices()
		self.validate_data()

	def validate_data(self):
		if self.purpose == "Employee Salary":
			if not self.fiscal_year and not self.month:
				frappe.throw("Fiscal Year and Month values are missing")
			else:
				if frappe.db.exists("RRCO Receipt Entries", {"fiscal_year":self.fiscal_year, "month": self.month}):
					frappe.throw("RRCO Receipt and date has been already assigned for the given month {} and fiscal year {}".format(self.month, self.fiscal_year))

		elif self.purpose in ["PBVA","Annual Bonus"]:
			if not self.fiscal_year:
				frappe.throw("Fiscal Year value is missing")

			if frappe.db.exists("RRCO Receipt Entries", {"fiscal_year":self.fiscal_year, "purpose": self.purpose}):
				frappe.throw("RRCO Receipt and date has been already assigned for {} and fiscal year {}".format(self.purpose, self.fiscal_year))
	
	def on_submit(self):
		self.rrco_receipt_entry()

	def on_cancel(self):
		if frappe.db.exists("RRCO Receipt Entries", {"rrco_receipt_tool": str(self.name)}):
			frappe.db.sql("delete from `tabRRCO Receipt Entries` where rrco_receipt_tool = '{}'".format(self.name))
		else:
			frappe.msgprint("No RRCO Receipt Entries found for this record")

	def rrco_receipt_entry(self):
		if self.purpose in ["Leave Encashment", "Purchase Invoices"]:
			if self.item:
				for a in self.item:
					if a.transaction == "Direct Payment":
						bill_no = a.invoice_no
					elif a.transaction == "Leave Encashment":
						employee, employee_name = frappe.db.get_value("Leave Encashment", a.invoice_no, ["employee","employee_name"])
						bill_no = str(employee_name + "(" + a.invoice_no + ")")
					elif a.transaction == "Purchase Invoice":
						bill_no = a.invoice_no

					rrco = frappe.new_doc("RRCO Receipt Entries")
					rrco.purpose = str(self.purpose)
					rrco.supplier = a.party
					rrco.bill_no = bill_no
					rrco.purchase_invoice = a.invoice_no
					rrco.receipt_date = self.tds_receipt_date
					rrco.receipt_number = self.tds_receipt_number
					rrco.cheque_number = self.cheque_number
					rrco.cheque_date = self.cheque_date
					rrco.branch = self.branch
					rrco.rrco_receipt_tool = self.name
					rrco.flags.ignore_permissions = True
					rrco.submit()
					
		elif self.purpose in ["Employee Salary","PBVA","Annual Bonus"]:
			rrco = frappe.new_doc("RRCO Receipt Entries")
			rrco.purpose = str(self.purpose)
			rrco.fiscal_year = str(self.fiscal_year)
			rrco.receipt_date = self.tds_receipt_date
			rrco.receipt_number = str(self.tds_receipt_number)
			rrco.cheque_number = str(self.cheque_number)
			rrco.cheque_date = self.cheque_date
			rrco.rrco_receipt_tool = self.name

			if self.purpose == "Employee Salary":
				rrco.month = str(self.month)
			rrco.flags.ignore_permissions = True
			rrco.submit()

	@frappe.whitelist()
	def get_invoices(self):
		if self.purpose in ["Leave Encashment", "Purchase Invoices"]:
			if not self.branch and not self.tds_rate and not self.from_date and not self.to_date:
				frappe.throw("Select the details to retrieve the invoices")
			cond = ''
			cond1 = ''
			if self.branch:
				cond += " AND a.branch = '{}'".format(self.branch)
				cond1 += " AND eb.branch = '{}'".format(self.branch)

			if self.purpose == 'Leave Encashment':
				query = """
					SELECT  
						"Leave Encashment" as transaction, 
						a.name, 
			   			a.encashment_date as posting_date, 
						a.encashment_amount as invoice_amount, 
		 				a.encashment_tax as tax_amount, 
			 			a.employee as party
					FROM `tabLeave Encashment` AS a, `tabJournal Entry` je 
	  					WHERE a.docstatus = 1
						AND a.encashment_tax > 0
						AND je.name = a.journal_entry
						AND je.posting_date BETWEEN '{0}' AND '{1}'
						AND je.docstatus = 1
						{2} 
						AND NOT EXISTS (SELECT 1 
									FROM `tabRRCO Receipt Entries` AS b 
									WHERE b.purchase_invoice = a.name)
						""".format(self.from_date, self.to_date, cond)
				query += """
					UNION SELECT 
						"Employee Benefits" as transaction, 
						eb.name, 
						je.posting_date, 
						t1.amount as invoice_amount, 
						t1.tax_amount as tax_amount, 
						eb.employee as party
					FROM `tabEmployee Benefits` AS eb, `tabSeparation Item` t1, `tabJournal Entry` je
						WHERE eb.docstatus = 1 
						AND t1.parent = eb.name
      					AND eb.journal = je.name
						AND je.posting_date BETWEEN '{0}' AND '{1}'
						AND t1.tax_amount > 0 {2}
	  					AND t1.benefit_type = 'Balance EL reimbursement'
						""".format(self.from_date, self.to_date, cond1)
			else:
				query = """
					SELECT "Purchase Invoice" as transaction, 
						p.name, 
						p.posting_date, 
	  					p.total as invoice_amount,  
						t.tax_amount, p.supplier as party
					FROM `tabPurchase Invoice` as p
					INNER JOIN `tabPurchase Taxes and Charges` t 
						on p.name = t.parent
					WHERE p.docstatus = 1 AND 
						p.posting_date BETWEEN '{0}' AND '{1}' 
						AND t.rate = '{2}' {3} 
						AND NOT EXISTS (SELECT 1 
						FROM `tabRRCO Receipt Entries` AS b 
						WHERE b.purchase_invoice = p.name)
						AND EXISTS (
							select 1
							from `tabTDS Remittance`  as r, `tabTDS Remittance Item` ri
							where r.name = ri.parent
							and r.docstatus = 1
							and ri.invoice_no = p.name
						)
					UNION 
						SELECT "Journal Entry" as transaction, 
							d.name, 
							d.posting_date, 
							di.taxable_amount as invoice_amount, 
							di.tax_amount as tds_amount, 
							di.party
						FROM `tabJournal Entry` AS d 
							LEFT JOIN `tabJournal Entry Account` as di on di.parent = d.name
							WHERE d.docstatus = 1 
							AND di.apply_tds = 1 
							AND d.posting_date BETWEEN '{0}' AND '{1}'
							AND d.tax_withholding_category = '{2}' 
							{4} 
							AND NOT EXISTS (SELECT 1 
								FROM `tabRRCO Receipt Entries` AS b 
								WHERE b.purchase_invoice = d.name)
							AND EXISTS (
								select 1
								from `tabTDS Remittance`  as r, `tabTDS Remittance Item` ri
								where r.name = ri.parent
								and r.docstatus = 1 
								and ri.invoice_no = d.name
								and ri.party = di.party
							)
							""".format(self.from_date, self.to_date, self.tds_rate, cond1,cond)

			self.set('item', [])
			total_invoice_amount = total_tax_amount = 0
			for a in frappe.db.sql(query, as_dict=True):
				row = self.append('item', {})
				d 	= {
						'transaction'	: a.transaction, 
						'invoice_no'	: a.name, 
						'invoice_date'	: a.posting_date, 
						'invoice_amount': flt(a.invoice_amount,2), 
						'tax_amount'	: flt(a.tax_amount,2), 
						'party'			: a.party
				   	}
				total_invoice_amount	+= flt(a.invoice_amount,2)
				total_tax_amount 		+= flt(a.tax_amount,2)
				row.update(d)
			self.total_invoice_amount 	= flt(total_invoice_amount,2)
			self.total_tax_amount 		= flt(total_tax_amount,2)
		else:
			if self.item:
				to_remove= []
				for d in self.item:
					to_remove.append(d)
				[self.remove(d) for d in to_remove]
	
# Following code added by SHIV on 2021/05/13
def get_permission_query_conditions(user):
	if not user: user = frappe.session.user
	user_roles = frappe.get_roles(user)

	if user == "Administrator" or "System Manager" in user_roles or "Accounts User" in user_roles: 
		return

	return """(
		exists(select 1
			from `tabEmployee` as e
			where e.branch = `tabRRCO Receipt Tool`.branch
			and e.user_id = '{user}')
		or
		exists(select 1
			from `tabEmployee` e, `tabAssign Branch` ab, `tabBranch Item` bi
			where e.user_id = '{user}'
			and ab.employee = e.name
			and bi.parent = ab.name
			and bi.branch = `tabRRCO Receipt Tool`.branch)
	)""".format(user=user)
