# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
from frappe.model.mapper import get_mapped_doc
from frappe.utils import cstr, flt, fmt_money, formatdate, nowdate, cint, money_in_words
from erpnext.controllers.accounts_controller import AccountsController
from erpnext.accounts.doctype.business_activity.business_activity import get_default_ba
from erpnext.custom_utils import check_tds_remittance
from erpnext.accounts.doctype.journal_entry.journal_entry import get_tds_account

class TechnicalSanctionBill(AccountsController):
	def validate(self):
		self.calculate_total_amount()
	
	def calculate_total_amount(self):
		self.total_deduction_amount = 0
		total = tdsAmount = 0
		for item in self.deduction: 
			self.total_deduction_amount += item.deduction_amount

		for item in self.advance:
			self.total_deduction_amount += item.allocated_amount

		for item in self.items: 
			total += item.total
		
		if self.tds_amount > 0:
			tdsAmount = self.tds_amount
		self.total_amount = total - self.total_deduction_amount - tdsAmount

		self.total_gross_amount = total

	def on_submit(self):
		self.make_gl_entries()
		self.update_linked_docs()
		self.update_advance_balance()
	
	def make_gl_entries(self):
		if self.total_amount:
			cost_center = frappe.db.get_value("Branch", self.branch, "cost_center")
			from erpnext.accounts.general_ledger import make_gl_entries
			gl_entries = []
			currency = frappe.db.get_value(doctype=self.party_type, filters=self.party, fieldname=["default_currency"], as_dict=True)
			default_ba =  get_default_ba()

			if self.party_type not in ["Customer","Supplier"]:
				frappe.throw("Party type can only be Customer or Supplier!")

			if self.party_type == "Supplier":
				inv_gl = frappe.db.get_value(doctype="Technical Sanction Account Setting",fieldname="expense_account")
				rec_gl = frappe.db.get_value(doctype="Company",filters=self.company,fieldname="default_payable_account")
				if self.expense_account:
					inv_gl = self.expense_account
			else:
				inv_gl = frappe.db.get_value(doctype="Technical Sanction Account Setting",fieldname="income_account")
				rec_gl = frappe.db.get_value(doctype="Company",filters=self.company,fieldname="default_receivable_account")
				if self.expense_account:
					inv_gl = self.expense_account

			if not inv_gl:
				frappe.throw(_("Project Invoice Account is not defined in Technical Sanction Account Setting"))

			if not rec_gl:
				frappe.throw(_("Default Receivable Account is not defined in Company Settings."))
					
			gl_entries.append(
				self.get_gl_dict({
					"account":  rec_gl,
					"party_type": self.party_type,
					"party": self.party,
					"against": inv_gl,
					"credit" if self.party_type == "Supplier" else "debit": self.total_amount,
					"credit_in_account_currency" if self.party_type == "Supplier" else "debit_in_account_currency": self.total_amount,
					"against_voucher": self.name,
					"against_voucher_type": self.doctype,
					"technical_sanction_bill": self.name,
					"cost_center": cost_center,
					"business_activity": default_ba
				}, currency.default_currency)
			)

			gl_entries.append(
				self.get_gl_dict({
					"account":  inv_gl,
					"against": self.party,
					"debit" if self.party_type == "Supplier" else "credit": self.total_gross_amount,
					"debit_in_account_currency" if self.party_type == "Supplier" else "credit_in_account_currency": self.total_gross_amount,
					"technical_sanction_bill": self.name,
					"cost_center": cost_center,
					"business_activity": default_ba
				}, currency.default_currency)
			)

			# OTHER DEDUCTIONS
			if self.deduction:
				for item in self.deduction:
					deduction_account_type = frappe.db.get_value(doctype="Account", filters=item.account, fieldname=["account_type"])
					gl_entries.append(
						self.get_gl_dict({
							"account": item.account,
							"credit" if self.party_type == "Supplier" else "debit": flt(item.deduction_amount),
							"credit_in_account_currency" if self.party_type == "Supplier" else "debit_in_account_currency": flt(item.deduction_amount),
							"cost_center": cost_center,
							"account_type": deduction_account_type,
							"is_advance": "No",
							"technical_sanction_bill": self.name,
							"party_check": 1 if deduction_account_type in ("Payable","Receivable") else 0,
							"party_type": self.party_type,
							"party": self.party,
							"business_activity": default_ba
						}, currency.default_currency)
					)

			# ADVANCE DEDUCTION
			if self.advance:
				tot_advance = 0.0
				for adv in self.advance:
					tot_advance += flt(adv.allocated_amount)

				if flt(tot_advance) > 0:
					advance_map = {"Supplier": "ts_advance_supplier", "Customer": "ts_advance_account"}
					advance_account = frappe.db.get_value(doctype="Technical Sanction Account Setting",fieldname=advance_map[self.party_type])

					if not advance_account:
						frappe.throw(_("Technical Sanction Advance Account for party type {0} is not defined under Technical Sanction Accounts Settings").format(self.party_type))
					
					advance_account_type = frappe.db.get_value(doctype="Account", filters=advance_account, fieldname=["account_type"])                   
					
					gl_entries.append(
						self.get_gl_dict({
							"account": advance_account,
							"credit" if self.party_type == "Supplier" else "debit": flt(tot_advance),
							"credit_in_account_currency" if self.party_type == "Supplier" else "debit_in_account_currency": flt(tot_advance),
							"cost_center": cost_center,
							"party_check": 1 if advance_account_type in ("Payable","Receivable") else 0,
							"party_type": self.party_type,
							"party": self.party,
							"account_type": advance_account_type,
							"is_advance": "No",
							"technical_sanction_bill": self.name,
							"business_activity": default_ba
						}, currency.default_currency)
					)

			if flt(self.tds_amount) > 0:
				gl_entries.append(
					self.get_gl_dict({
						"account": self.tds_account,
						"credit": self.tds_amount,
						"credit_in_account_currency": self.tds_amount,
						"cost_center": cost_center,
						"company": self.company,
						"technical_sanction_bill": self.name,
						"business_activity": default_ba,
					})
				)
			# frappe.throw("stopped!")
			make_gl_entries(gl_entries, cancel=(self.docstatus == 2),update_outstanding="No", merge_entries=False)

	def update_linked_docs(self):
		if self.technical_sanction: 
			frappe.db.sql("update `tabTechnical Sanction` set bill = '{bill}' where name ='{ts}'".format(bill=self.name, ts=self.technical_sanction))
		if self.revised_technical_sanction:
			frappe.db.sql("update `tabRevised Technical Sanction` set bill = '{bill}' where name ='{rts}'".format(bill=self.name, rts=self.technical_sanction))

	def on_cancel(self):
		check_tds_remittance(self.name)
		self.cancel_linked_docs()
		self.make_gl_entries()
		self.update_advance_balance()
	
	def cancel_linked_docs(self): 
		if self.technical_sanction: 
			frappe.db.sql("update `tabTechnical Sanction` set bill = '' where name ='{ts}'".format(ts=self.technical_sanction))
		if self.revised_technical_sanction:
			frappe.db.sql("update `tabRevised Technical Sanction` set bill = '' where name ='{rts}'".format(rts=self.technical_sanction))

	def update_advance_balance(self):
		for adv in self.advance:
			allocated_amount = 0.0
			if flt(adv.allocated_amount) > 0:
				balance_amount = frappe.db.get_value("Technical Sanction Advance", adv.reference_name, "balance_amount")

				if flt(balance_amount) < flt(adv.allocated_amount) and self.docstatus < 2:
					frappe.throw(_("Advance#{0} : Allocated amount Nu. {1}/- cannot be more than Advance Balance Nu. {2}/-").format(adv.reference_name, "{:,.2f}".format(flt(adv.allocated_amount)),"{:,.2f}".format(flt(balance_amount))))
				else:
					allocated_amount = -1*flt(adv.allocated_amount) if self.docstatus == 2 else flt(adv.allocated_amount)

					adv_doc = frappe.get_doc("Technical Sanction Advance", adv.reference_name)
					adv_doc.adjustment_amount = flt(adv_doc.adjustment_amount) + flt(allocated_amount)
					adv_doc.balance_amount    = flt(adv_doc.balance_amount) - flt(allocated_amount)
					adv_doc.save(ignore_permissions = True)

	@frappe.whitelist()
	def get_tds_details(self, tax_withholding_category):
		# frappe.throw(tax_withholding_category)
		tds_account  = get_tds_account(tax_withholding_category)
		return tds_account

	@frappe.whitelist()
	def make_journal_entry(self):
		if not self.total_amount:
			frappe.throw(_("Amount should be greater than zero"))
		self.posting_date = nowdate()
		ba = get_default_ba()

		payable_account = frappe.db.get_value("Company", self.company,"default_payable_account")
		bank_account = frappe.db.get_value("Company", self.company,"default_bank_account")
		cost_center = frappe.db.get_value("Branch", self.branch, "cost_center")

		if not bank_account:
			frappe.throw("Setup Default Bank Account in Company Setting")
		if not payable_account:
			frappe.throw("Setup Payable Bank Account in Company Setting")

		# tds_rate, tds_account = 0, ""
		# if self.tds_amount > 0:
		# 	tds_dtls = self.get_tax_details()
		# 	tds_rate = tds_dtls['rate']
		# 	tds_account = tds_dtls['account']

		# r = []
		# if self.remarks:
		# 	r.append(_("Note: {0}").format(self.remarks))

		# remarks = ("").join(r) 

		je = frappe.new_doc("Journal Entry")

		je.update({
			"doctype": "Journal Entry",
			"voucher_type": "Bank Entry",
			"naming_series": "Bank Payment Voucher",
			"title": "Technical Sanction Bill - " + self.name,
			# "user_remark": remarks if remarks else "Note: " + "Technical Sanction Bill - " + self.name,
			"user_remark": "Note: " + "Technical Sanction Bill - " + self.name,
			"posting_date": self.posting_date,
			"company": self.company,
			"total_amount_in_words": money_in_words(self.total_amount),
			"branch": self.branch,
			# "apply_tds": 1 if self.tds_amount > 0 else 0,
			# "tax_withholding_category": self.tax_withholding_category
		})

		je.append("accounts",{
			"account": payable_account,
			"debit_in_account_currency": self.total_amount,
			"cost_center": cost_center,
			"party_check": 0,
			"party_type": "Supplier",
			"party": self.party,
			"reference_type": "Technical Sanction Bill",
			"reference_name": self.name,
			"business_activity": ba,
			# "apply_tds": 1 if self.tds_amount > 0 else 0,
			# "add_deduct_tax": "Deduct" if self.tds_amount > 0 else "",
			# "tax_account": tds_account,
			# "rate": tds_rate,
			# "tax_amount_in_account_currency": self.tds_amount,
			# "tax_amount": self.tds_amount
		})

		je.append("accounts",{
			"account": bank_account,
			"credit_in_account_currency": self.total_amount,
			"cost_center": cost_center,
			"business_activity": ba,
		})

		je.insert()
		self.db_set("journal_entry",je.name)
		frappe.msgprint(_('Journal Entry {} posted to Accounts').format(frappe.get_desk_link(je.doctype,je.name)))

@frappe.whitelist()
def make_payment(source_name, target_doc=None):
	def update_docs(obj, target, source_parent):
		target.posting_date = nowdate()
		target.payment_for = "Maintenance Payment"
		payable_amount = flt(obj.total_amount)
		target.total_amount = payable_amount
		target.net_amount = payable_amount
		target.actual_amount = payable_amount

		target.append("maintenance_payment_item", {
			"technical_sanction_bill": obj.name,
			"service_charges": obj.total_amount,
			"material_charges": obj.material_charges,
			"payable_amount": payable_amount
		})

	doc = get_mapped_doc("Technical Sanction Bill", source_name, {
		"Technical Sanction Bill": {
			"doctype": "Mechanical Payment",
			"field_map":{
				"party": "supplier"
			},	
			"postprocess": update_docs,
			"validation": {"docstatus": ["=", 1]}
		},
	}, target_doc)
	return doc


# added by phuntsho on july 27, 2021
@frappe.whitelist()
def get_advance_list(technical_sanction, party, party_type):
	result = frappe.db.sql("""
			select *
			from `tabTechnical Sanction Advance`
			where technical_sanction = '{ts}'
			and party_type = '{party_type}'
			and party = '{party}'
			and docstatus = 1
			and balance_amount > 0
			""".format(ts=technical_sanction, party_type=party_type, party=party), as_dict=True)
	return result

