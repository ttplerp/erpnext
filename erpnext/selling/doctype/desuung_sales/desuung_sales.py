# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt, cstr, cint, getdate, get_datetime, get_url, nowdate, now_datetime, money_in_words
from erpnext.accounts.general_ledger import make_gl_entries
from frappe import _
from erpnext.controllers.accounts_controller import AccountsController
from erpnext.custom_utils import check_future_date
from erpnext.accounts.utils import get_fiscal_year

class DesuungSales(Document):
	#code to fetch selling price for items after selecting item_code
	@frappe.whitelist()
	def get_selling_price(self, item_code = None, branch = None, posting_date = None):
		if not item_code:
			return
		selling_price = ""
		if not branch or branch == None:
			frappe.throw("Please select branch first")
		else:
			selling_price = frappe.db.sql("""
				SELECT 
					spr.selling_price as selling_price, sp.name as name 
				FROM `tabSelling Price Rate` spr, `tabSelling Price` sp, `tabSelling Price Branch` spb 
				WHERE spr.parent = spb.parent 
				AND spr.particular = '{0}' 
				AND spb.branch = '{1}' 
				AND '{2}' BETWEEN sp.from_date 
				AND sp.to_date""".format(item_code, branch, posting_date), as_dict = True)
		return selling_price
	#end

	def validate(self):
		check_future_date(self.posting_date)
		self.get_amount()
	
	def get_amount(self):
		
		Amount = 0
		for item in self.items:
			if not item.qty or not item.rate:
				frappe.throw("Please enter qty or rate")
			item.amount = flt(item.qty) * flt(item.rate)
			Amount += item.amount
		self.total = Amount
	
	def on_submit(self):
		self.post_gl_entry()
		self.update_stock_ledger()
		#self.consume_budget()
	
	def on_cancel(self):
		self.post_gl_entry()
		self.update_stock_ledger()
		#self.cancel_budget_entry()

	def post_gl_entry(self):
		gl_entries = []
		if self.company == "De-Suung":
			gl_entries.append(
				self.get_gl_dict({
						"account": self.debit_account,
						"debit": self.total,
						"debit_in_account_currency": self.total,
						"voucher_no": self.name,
						"voucher_type": self.doctype,
						"cost_center": self.cost_center,					
						"company": self.company,
						"remarks": self.remarks,
						"business_activity": self.business_activity,
					})
				)
			gl_entries.append(
				self.get_gl_dict({
						"account": self.credit_account,
						"credit": self.total,
						"credit_in_account_currency": self.total,
						"voucher_no": self.name,
						"voucher_type": self.doctype,
						"cost_center": self.cost_center,
						"company": self.company,
						"remarks": self.remarks,
						"business_activity": self.business_activity,
					})
				)
		make_gl_entries(gl_entries, cancel=(self.docstatus == 2), update_outstanding="No", merge_entries=False)

	def update_stock_ledger(self):
			sl_entries = []
			for d in self.items:
					if d.warehouse and self.docstatus==1:
							sl_entries.append(self.get_sl_entries(d, {
								"actual_qty": -1*flt(d.qty),
								"incoming_rate": d.rate
							}))
					if d.warehouse and self.docstatus==2:
							sl_entries.append(self.get_sl_entries(d, {
								"actual_qty": -1*flt(d.qty),
								"incoming_rate": d.rate
							}))
	
			self.make_sl_entries(sl_entries)

	def get_sl_entries(self, d, args):
		sl_dict = frappe._dict({
			"item_code": d.get("item_code", None),
			"warehouse": d.get("warehouse", None),
			"posting_date": self.posting_date,
			"posting_time": self.posting_time,
			'fiscal_year': get_fiscal_year(self.posting_date, company=self.company)[0],
			"voucher_type": self.doctype,
			"voucher_no": self.name,
			"voucher_detail_no": d.name,
			"actual_qty": (self.docstatus==1 and 1 or -1)*flt(d.get("stock_qty")),
			"stock_uom": frappe.db.get_value("Item", args.get("item_code") or d.get("item_code"), "stock_uom"),
			"incoming_rate": 0,
			"company": self.company,
			"batch_no": cstr(d.get("batch_no")).strip(),
			"serial_no": d.get("serial_no"),
			"project": d.get("project"),
			"is_cancelled": self.docstatus==2 and "Yes" or "No"
		})

		sl_dict.update(args)
		return sl_dict

	def make_sl_entries(self, sl_entries, is_amended=None, allow_negative_stock=False,
			via_landed_cost_voucher=False):
		from erpnext.stock.stock_ledger import make_sl_entries
		make_sl_entries(sl_entries, allow_negative_stock, via_landed_cost_voucher)

	
