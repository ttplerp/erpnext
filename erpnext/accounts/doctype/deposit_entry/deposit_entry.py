# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt
from erpnext.accounts.utils import get_account_currency

class DepositEntry(Document):
	def validate(self):
		self.bank_account =	frappe.db.get_value('POS Payment Method',{'mode_of_payment':'Online Payment','parent':self.pos_profile},'account')
		self.cash_account =	frappe.db.get_value('POS Payment Method',{'mode_of_payment':'Cash','parent':self.pos_profile},'account')
		total = 0
		for d in self.items:
			total += flt(d.cash_amount)
		self.total_amount = total
	def on_submit(self):
		self.post_gl_entry_for_cash()
		self.update_pos_voucher()
	def on_cancel(self):
		self.update_pos_voucher()
		self.post_gl_entry_for_cash()

	def update_pos_voucher(self):
		for d in self.items:
			doc = frappe.get_doc('POS Closing Entry',d.pos_closing_entry)
			if self.docstatus == 1:
				doc.db_set('payment_status','Deposited')
			elif self.docstatus == 2 :
				doc.db_set('payment_status','Not Deposited')
	def post_gl_entry_for_cash(self):
		gl_entries = []
		for item in self.items:
			account_currency = get_account_currency(self.cash_account)
			gl_entries.append(frappe._dict(
				{
					"account": self.cash_account,
					"credit": flt(item.cash_amount),
					"credit_in_account_currency": (flt(item.cash_amount, item.precision("cash_amount"))
						if account_currency==self.currency
						else flt(item.cash_amount, item.precision("cash_amount"))),
					"cost_center": self.cost_center,
					"company":self.company,
					"currency":self.currency,
					"voucher_type":self.doctype,
					"voucher_no":item.pos_closing_entry,
					"posting_date":self.deposited_date
				}))
			account_currency = get_account_currency(self.bank_account)
			gl_entries.append(frappe._dict(
				{
					"account": self.bank_account,
					"debit": flt(item.cash_amount),
					"debit_in_account_currency": (flt(item.cash_amount, item.precision("cash_amount"))
						if account_currency==self.currency
						else flt(item.cash_amount, item.precision("cash_amount"))),
					"cost_center": self.cost_center,
					"company":self.company,	
					"currency":self.currency,
					"voucher_type":self.doctype,
					"voucher_no":item.pos_closing_entry,
					"posting_date":self.deposited_date
				}))
		from erpnext.accounts.general_ledger import make_gl_entries
		make_gl_entries(gl_entries, cancel=(self.docstatus == 2), update_outstanding="No", merge_entries=False, from_repost=False)
		
	def delete_gl_enteries(self):
		for item in self.items:
			frappe.db.sql("""delete from `tabGL Entry` where voucher_type='POS Closing Voucher' and voucher_no=%s""",
				(item.pos_voucher_closing))
			
	@frappe.whitelist()
	def get_pos_voucher(self):
		if not self.pos_profile:
			frappe.msgprint('POS Profile is mandatory',raise_exception=1)
		if self.from_date > self.to_date :
			frappe.msgprint('From Date cannot be after To Date',raise_exception=1)
		total = 0
		self.set('items',[])
		for d in frappe.db.sql('''SELECT p.name as pos_closing_entry,
							pi.closing_amount as cash_amount, p.posting_date, p.user as cashier
							FROM `tabPOS Closing Entry` p INNER JOIN `tabPOS Closing Entry Detail` pi
							ON p.name = pi.parent
							WHERE pi.mode_of_payment = 'Cash' AND p.pos_profile = '{}' 
							AND pi.closing_amount > 0
							AND p.posting_date BETWEEN '{}' AND '{}' 
							AND p.docstatus = 1
							AND NOT EXISTS(select 1 from `tabDeposit Entry Item` where pos_closing_entry = p.name and parent != '{}' and docstatus = 1)
					'''.format(self.pos_profile,self.from_date,self.to_date,self.name),as_dict=1):
			row = self.append('items',{})
			row.update(d)
			total += flt(d.cash_amount)
		if total == 0:
			frappe.msgprint('No Data found')
		return total
