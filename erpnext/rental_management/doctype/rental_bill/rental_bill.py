# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import formatdate, flt
from erpnext.accounts.general_ledger import make_gl_entries
from frappe.model.naming import make_autoname
from erpnext.controllers.accounts_controller import AccountsController

class RentalBill(AccountsController):
	def autoname(self):
		if not self.dzongkhag:
			frappe.throw("Dzongkhag name is missing")
		dz = self.dzongkhag
		dzo_prefix = dz[:3]
		prefix = dzo_prefix.upper()
		
		bill_code = str(prefix) + "/" + str(formatdate(self.fiscal_year, "YY")) + str(self.month) + '/.####'
		self.name = make_autoname(bill_code)
	
	def on_cancel(self):
		self.ignore_linked_doctypes = (
			"GL Entry",
			"Payment Ledger Entry",
		)
		# account_frozen_date = frappe.db.get_single_value("Accounts Settings", "acc_frozen_upto")
		# if getdate(self.posting_date) < getdate(account_frozen_date):
		# 	frappe.throw("Not permitted to Cancel this Document.")
		# frappe.db.sql("delete from `tabGL Entry` where voucher_no = '{}'".format(self.name))
		self.cancel_gl_entry()

	def cancel_gl_entry(self):
		cost_center = frappe.db.get_value("Branch", self.branch, "cost_center")
		revenue_claim_account = frappe.db.get_single_value("Rental Account Setting", "revenue_claim_account")
		for a in frappe.db.sql("""
				select t.name as rental_bill, t.tenant, c.name as customer, t.receivable_amount, t.building_category
				from `tabRental Bill` t left join `tabCustomer` c on t.customer_code = c.customer_code
				where t.name = '{name}'
			""".format(name=self.name), as_dict=True):
			gl_entries = []
			pre_rent_account = frappe.db.get_single_value("Rental Account Setting", "pre_rent_account")
			pre_rent_amount = frappe.db.sql("""
									select ifnull(amount, 0) as pre_rent_amount
									from `tabPayment Ledger Entry` 
									Where voucher_no='{name}' 
									and party = '{party}' and account = '{account}'
								""".format(party=a.customer, account=pre_rent_account, name=self.name))[0][0]
			pre_rent_adjustment_amount, balance_receivable_amount = 0,0
			if pre_rent_amount > 0:
				if a.receivable_amount <= pre_rent_amount:
					pre_rent_adjustment_amount = flt(a.receivable_amount)
				else:
					pre_rent_adjustment_amount = flt(pre_rent_amount)
					balance_receivable_amount = flt(a.receivable_amount) - flt(pre_rent_amount)

				gl_entries.append(
					self.get_gl_dict({
						"account": pre_rent_account,
						"debit": flt(pre_rent_adjustment_amount),
						"debit_in_account_currency": flt(pre_rent_adjustment_amount),
						"voucher_no": a.rental_bill,
						"voucher_type": "Rental Bill",
						"cost_center": cost_center,
						"party": a.customer,
						"party_type": "Customer",
						"company": self.company,
						"remarks": str(a.tenant) + " Monthly Rental Bill for Year " + str(self.fiscal_year) + " Month " + str(self.month),
						# "business_activity": business_activity
					})
				)
			else:
				balance_receivable_amount = flt(a.receivable_amount)
			
			if balance_receivable_amount > 0:
				gl_entries.append(
					self.get_gl_dict({
						"account": revenue_claim_account,
						"debit": flt(balance_receivable_amount),
						"debit_in_account_currency": flt(balance_receivable_amount),
						"voucher_no": a.rental_bill,
						"voucher_type": "Rental Bill",
						"cost_center": cost_center,
						'party': a.customer,
						'party_type': 'Customer',
						"company": self.company,
						"remarks": str(a.tenant) + " Monthly Rental Bill for Year " + str(self.fiscal_year) + " Month " + str(self.month),
						# "business_activity": business_activity
					})
				)
			credit_account = frappe.db.get_value("Rental Account Setting Item",{"building_category":a.building_category}, "account")

			gl_entries.append(
				self.get_gl_dict({
					"account": credit_account,
					"credit": flt(a.receivable_amount),
					"credit_in_account_currency": flt(a.receivable_amount),
					"voucher_no": a.rental_bill,
					"voucher_type": "Rental Bill",
					"cost_center": cost_center,
					"company": self.company,
					"remarks": str(a.tenant) + " Rental Bill for " + str(a.building_category) +" Year "+ str(self.fiscal_year) + " Month " +str(self.month),
					# "business_activity": business_activity
					})
				)
			make_gl_entries(gl_entries, cancel=(self.docstatus == 2), update_outstanding="No", merge_entries=False)
			
			# doc = frappe.get_doc("Rental Bill", a.rental_bill)
			# self.gl_entry = 1
			# self.adjusted_amount = flt(pre_rent_adjustment_amount)
			# frappe.throw("<pre>{}</pre>".format(frappe.as_json(gl_entries)))
