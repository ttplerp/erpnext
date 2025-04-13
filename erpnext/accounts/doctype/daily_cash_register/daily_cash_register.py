# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import cint, flt, nowdate, add_days, getdate, fmt_money, add_to_date, DATE_FORMAT, date_diff, get_last_day

class DailyCashRegister(Document):
	def validate(self):
		self.validate_duplicate()
		self.fetch_opening_balance()
		self.calculate_closing()

	def validate_duplicate(self):
		closing_dtl = frappe.db.sql("""
							select name from `tabDaily Cash Register`
							where company='{0}' and cash_account='{1}'
							and date='{2}'
							and docstatus != 2
							and name != '{3}'
					""".format(self.company, self.cash_account, self.date, self.name), as_dict=True)
		if closing_dtl:
			frappe.throw("Daily Cash Closing for {}, {} and {} is already done with \
						<b>{}</b>".format(self.cash_account, self.company, self.date, closing_dtl[0].name))

	def fetch_opening_balance(self):
		if self.date:
			closing_date = getdate(add_days(self.date, -1))
			dtl = frappe.db.sql("""
							select closing_balance, this_closing from `tabDaily Cash Register`
							where company='{0}' and cash_account='{1}'
							and date='{2}'
							and docstatus=1
					""".format(self.company, self.cash_account, closing_date), as_dict=True)
			if dtl:
				self.opening_balance = dtl[0].closing_balance
				self.last_closed_on = dtl[0].this_closing
			else:
				frappe.msgprint("No Daily Cash Register for <b>{}</b>".format(closing_date))
	
	def calculate_closing(self):
		self.custody = self.total_cash_in
		self.returns = self.total_cash_out
		if not self.custody or not self.returns:
			self.closing_balance = flt(self.opening_balance + self.custody - self.returns,2)

		self.over_short =flt(self.closing_balance-self.net_amount,2)

	@frappe.whitelist()
	def get_gl_entries(self, cash_in_out=None):
		cond = ""
		col = ""
		total_cash = closing_balance = 0.00
		if cash_in_out == "In":
			cond = " and (debit > 0 or debit_in_account_currency > 0) "
			col = " debit as amount "
			self.set('cash_in_entries', [])
		else:
			cond = " and (credit > 0 or credit_in_account_currency > 0) "
			col = " credit as amount "
			self.set('cash_out_entries', [])
	
		dtl=frappe.db.sql("""
					select name as gl_entry, account, voucher_type, 
					voucher_no, remarks, posting_date as date, {4}
					from `tabGL Entry`
					where account='{0}'
					and company='{1}' and posting_date='{2}'
					and docstatus != 2
					and is_cancelled != 1
					{3}
				""".format(self.cash_account, self.company, self.date, cond, col), as_dict=True)
		if dtl:
			for a in dtl:
				total_cash += flt(a.amount)
				if cash_in_out=="In":
					row = self.append('cash_in_entries', {})
				else:
					row = self.append('cash_out_entries', {})
				row.update(a)
		#else:
		#	frappe.msgprint("Transaction not available")
			
		if cash_in_out=="In":
			self.db_set("total_cash_in",total_cash)
			self.db_set("custody",total_cash)
		else:
			self.db_set("total_cash_out", total_cash)
			self.db_set("returns", total_cash)
		closing = flt(self.opening_balance + self.custody - self.returns, 2)
		self.db_set("closing_balance", closing_balance)
