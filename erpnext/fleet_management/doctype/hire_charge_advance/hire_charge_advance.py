# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
import erpnext
from frappe import _
from frappe.model.document import Document
from erpnext.accounts.party import get_party_account
from erpnext.setup.utils import get_exchange_rate
from frappe.utils import flt, money_in_words, now_datetime, nowdate

class HireChargeAdvance(Document):
	def valiate(self):
		self.set_status()
		self.set_defaults()

	def on_submit(self):
		if flt(self.advance_amount <= 0):
			frappe.throw(_("Please input valid advance amount"), title="Invalid Amount")
		self.post_journal_entry()
	
	def set_status(self):
		self.status = {
			"0": "Draft",
			"1": "Submitted",
			"2": "Cancelled"
		}[str(self.docstatus or 0)]

	@frappe.whitelist()
	def set_defaults(self):
		if self.docstatus < 2:
			self.journal_entry = None
			self.journal_entry_status = None
			self.paid_amount = 0
			self.received_amount = 0
			self.adjustment_amount = 0
			self.balance_amount = 0
			self.payment_type  = "Receive" if self.party_type == "Customer" else "Pay"
		
		if not self.advance_account:
			self.advance_account = get_party_account(self.party_type, self.party, self.company, is_advance=True)

		if self.company and not self.exchange_rate:
			company_currency = erpnext.get_company_currency(self.company)
			if company_currency == self.currency:
				self.exchange_rate = 1
			else:
				self.exchange_rate = get_exchange_rate(self.currency, company_currency)
			self.exchange_rate_original = self.exchange_rate

		if self.advance_amount_requested and not self.advance_amount:
			self.advance_amount = flt(self.advance_amount_requested)*flt(self.exchange_rate)
	
	def post_journal_entry(self):
		if self.advance_account:
			adv_gl = self.advance_account

		if not adv_gl:
			frappe.throw(_("Advance GL is not defined."))
		adv_gl_det = frappe.db.get_value(doctype="Account", filters=adv_gl, fieldname=["account_type","is_an_advance_account"], as_dict=True)

		# Fetching Revenue & Expense GLs
		rev_gl, exp_gl = frappe.db.get_value("Branch",self.branch,["revenue_bank_account", "expense_bank_account"])
		if self.payment_type == "Receive":
			if not rev_gl:
				frappe.throw(_("Revenue GL is not defined for this Branch '{0}'.").format(self.branch), title="Data Missing")
			rev_gl_det = frappe.db.get_value(doctype="Account", filters=rev_gl, fieldname=["account_type","is_an_advance_account"], as_dict=True)
		else:
			if not exp_gl:
					frappe.throw(_("Expense GL is not defined for this Branch '{0}'.").format(self.branch), title="Data Missing")
			exp_gl_det = frappe.db.get_value(doctype="Account", filters=exp_gl, fieldname=["account_type","is_an_advance_account"], as_dict=True)

		# Posting Journal Entry
		accounts = []
		accounts.append({"account": adv_gl,
			"credit_in_account_currency" if self.party_type == "Customer" else "debit_in_account_currency": flt(self.advance_amount),
			"cost_center": self.cost_center,
			"party_check": 1,
			"party_type": self.party_type,
			"party": self.party,
			"account_type": adv_gl_det.account_type,
			"is_advance": "Yes" if adv_gl_det.is_an_advance_account == 1 else None,
			"reference_type": "Hire Charge Advance",
			"reference_name": self.name,
		})

		if self.party_type == "Customer":
			accounts.append({"account": rev_gl,
				"debit_in_account_currency": flt(self.advance_amount),
				"cost_center": self.cost_center,
				"party_check": 0,
				"account_type": rev_gl_det.account_type,
				"is_advance": "Yes" if rev_gl_det.is_an_advance_account == 1 else "No",
			})
		else:
			accounts.append({"account": exp_gl,
				"credit_in_account_currency": flt(self.advance_amount),
				"cost_center": self.cost_center,
				"party_check": 0,
				"account_type": exp_gl_det.account_type,
				"is_advance": "Yes" if exp_gl_det.is_an_advance_account == 1 else "No",
			})

		je = frappe.new_doc("Journal Entry")
		
		je.update({
				"doctype": "Journal Entry",
				"voucher_type": "Bank Entry",
				"naming_series": "Bank Receipt Voucher" if self.payment_type == "Receive" else "Bank Payment Voucher",
				"title": "Hire Charge Advance - "+self.name,
				"user_remark": "Hire Charge Advance - "+self.name,
				"posting_date": nowdate(),
				"company": self.company,
				"total_amount_in_words": money_in_words(self.advance_amount),
				"accounts": accounts,
				"branch": self.branch
		})

		if self.advance_amount:
			je.save(ignore_permissions = True)
			self.db_set("journal_entry", je.name)
			self.db_set("journal_entry_status", "Forwarded to accounts for processing payment on {0}".format(now_datetime().strftime('%Y-%m-%d %H:%M:%S')))
			frappe.msgprint(_('{} posted to accounts').format(frappe.get_desk_link(je.doctype,je.name)))
