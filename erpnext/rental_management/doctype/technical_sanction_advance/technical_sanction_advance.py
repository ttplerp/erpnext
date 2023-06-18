# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import money_in_words, cint, flt, nowdate, now_datetime
from erpnext.accounts.doctype.business_activity.business_activity import get_default_ba

class TechnicalSanctionAdvance(Document):
	def validate(self):
		self.advance_amount = self.advance_amount_requested
		self.set_status()
		self.set_defaults()
	
	def set_defaults(self):
		if self.docstatus < 2:
			self.journal_entry = None
			self.journal_entry_status = None
			self.paid_amount = 0
			self.received_amount = 0
			self.adjustment_amount = 0
			self.balance_amount = 0
			self.payment_type  = "Receive" if self.party_type == "Customer" else "Pay" 
		
		if self.technical_sanction:
			ts = frappe.get_doc("Technical Sanction", self.technical_sanction)

			if ts.docstatus in (2, 0):
				frappe.throw("Technical Sanction: {} has been cancelled!".format(self.technical_sanction))

			values = frappe.db.get_value("Branch", ts.branch, ['cost_center', 'company'],as_dict=1)
			self.cost_center      = values.cost_center
			self.branch           = ts.branch
			self.company          = values.company

			# fetch party information
			self.party_type = self.party_type if self.party_type else ts.party_type 
			self.party      = self.party if self.party else ts.party
			if self.party_type and self.party:
				doc = frappe.get_doc(self.party_type, self.party)
				self.party_address = doc.get("customer_details") if self.party_type == "Customer" else doc.get("supplier_details") if self.party_type == "Supplier" else doc.get("employee_name")
						
	def set_status(self):
		self.status = {
			"0": "Draft",
			"1": "Submitted",
			"2": "Cancelled"
		}[str(self.docstatus or 0)]

	

	def on_submit(self):
		if flt(self.advance_amount) <= 0:
			frappe.throw(_("Please input valid advance amount."), title="Invalid Amount")
		
		if str(self.advance_date) > '2017-09-30':
			self.post_journal_entry()
		self.ts_advance_item_entry()

	def on_cancel(self):
		self.ts_advance_item_entry()

	def on_update_after_submit(self):
		self.ts_advance_item_entry()
		

	def ts_advance_item_entry(self):
		if self.docstatus == 2:
			frappe.db.sql("delete from `tabTechnical Sanction Advance Item` where parent='{ts}' and advance_name = '{advance_name}'".format(ts=self.technical_sanction, advance_name=self.name))
		else:
			if not frappe.db.exists("Technical Sanction Advance Item", {"parent": self.technical_sanction, "advance_name": self.name}):
				doc = frappe.get_doc("Technical Sanction", self.technical_sanction)
				row = doc.append("technical_sanction_advance", {})
				row.advance_name        = self.name
				row.advance_date        = self.advance_date
				row.advance_amount      = flt(self.received_amount)+flt(self.paid_amount)
				row.received_amount     = flt(self.received_amount)
				row.paid_amount         = flt(self.paid_amount)
				row.adjustment_amount   = flt(self.adjustment_amount)
				row.balance_amount      = flt(self.balance_amount)
				row.save(ignore_permissions=True)
			else:
				row = frappe.get_doc("Technical Sanction Advance Item", {"parent": self.technical_sanction, "advance_name": self.name})
				row.advance_date        = self.advance_date
				row.advance_amount      = flt(self.received_amount)+flt(self.paid_amount)
				row.received_amount     = flt(self.received_amount)
				row.paid_amount         = flt(self.paid_amount)
				row.adjustment_amount   = flt(self.adjustment_amount)
				row.balance_amount      = flt(self.balance_amount)
				row.save(ignore_permissions=True)


	def post_journal_entry(self):
		default_ba =  get_default_ba()
		# Fetching Advance GL
		adv_gl_field = "ts_advance_account" if self.party_type == "Customer" else "ts_advance_supplier"
		adv_gl = frappe.db.get_value("Technical Sanction Account Setting",fieldname=adv_gl_field)

		if self.advance_account:
				adv_gl = self.advance_account

		if not adv_gl:
				frappe.throw(_("Advance GL is not defined in Projects Accounts Settings."))
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
							"reference_type": "Technical Sanction Advance",
							"reference_name": self.name,
							"technical_sanction": self.technical_sanction,
							"business_activity": default_ba
		})

		if self.party_type == "Customer":
				accounts.append({"account": rev_gl,
									"debit_in_account_currency": flt(self.advance_amount),
									"cost_center": self.cost_center,
									"party_check": 0,
									"account_type": rev_gl_det.account_type,
									"is_advance": "Yes" if rev_gl_det.is_an_advance_account == 1 else "No",
									"business_activity": default_ba
				})
		else:
				accounts.append({"account": exp_gl,
									"credit_in_account_currency": flt(self.advance_amount),
									"cost_center": self.cost_center,
									"party_check": 0,
									"account_type": exp_gl_det.account_type,
									"is_advance": "Yes" if exp_gl_det.is_an_advance_account == 1 else "No",
									"business_activity": default_ba
				})

		je = frappe.new_doc("Journal Entry")
		
		je.update({
				"doctype": "Journal Entry",
				"voucher_type": "Bank Entry",
				"naming_series": "Bank Receipt Voucher" if self.payment_type == "Receive" else "Bank Payment Voucher",
				"title": "Tech Sanction Advance - "+self.technical_sanction,
				"user_remark": "Technical Sanction Advance - "+self.technical_sanction,
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
				frappe.msgprint(_('Journal Entry <a href="#Form/Journal Entry/{0}">{0}</a> posted to accounts').format(je.name))

