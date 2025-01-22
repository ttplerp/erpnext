# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from functools import reduce
from frappe.model.document import Document
from frappe import _, qb, throw, bold
from erpnext.custom_utils import check_future_date
from erpnext.controllers.accounts_controller import AccountsController
from frappe.utils import flt, cint, money_in_words, nowdate, getdate
from frappe import ValidationError, _, qb, scrub, throw
from erpnext.accounts.utils import get_tds_account, get_account_type
from erpnext.accounts.general_ledger import (make_gl_entries, merge_similar_entries)
from erpnext.accounts.party import get_party_account
from frappe.model.naming import make_autoname
from erpnext.accounts.utils import (
	get_account_currency,
	get_balance_on,
	get_outstanding_invoices,
	check_clearance_date,
)
from erpnext.accounts.doctype.journal_entry.journal_entry import get_default_bank_cash_account
from erpnext.accounts.doctype.bank_account.bank_account import (
	get_bank_account_details,
	get_party_bank_account,
)


class TransportationandHireCharges(AccountsController):
	def autoname(self):
		abbr = frappe.db.get_value("Charge Type", self.invoice_type, "abbr")
		if abbr:
			self.name = make_autoname(f"{abbr}-.YYYY.-.MM.-.####")
		else:
			frappe.throw(_("Abbreviation not found for Charge Type: {0}").format(self.invoice_type), title="Missing Abbreviation")

	def validate(self):
		check_future_date(self.posting_date)		
		self.calculate_totals()
		self.validate_amount()

	def on_submit(self):
		self.update_reference_document()
		self.make_gl_entry()

	def on_cancel(self):
		self.update_reference_document()
		self.make_gl_entry(cancel=True)

	def validate_amount(self):
		for d in self.material_issue_details:
			if flt(d.allocated_amount) > flt(d.total_amount):
				frappe.throw("Row #{}. Allocated amount {} cannot be more than {}".format(
					frappe.bold(d.idx), 
					frappe.bold(frappe.format_value(d.allocated_amount, {"fieldtype":"Currency"})),
					frappe.bold(frappe.format_value(d.total_amount, {"fieldtype":"Currency"}))
				))
		
		if flt(self.net_payable) < 0:
			frappe.throw("{} has more deduction than grand total {}".format(
				frappe.bold(self.supplier), 
				frappe.bold(frappe.format_value(self.amount, {"fieldtype":"Currency"}))
			))

	@frappe.whitelist()
	def get_equiment_issue_detail(self):
		if self.party_type == "Customer":
			return
		
		res = frappe.db.sql("""
							select name, outstanding_amount, posting_date, debit_account
							from `tabEquipment Material Issue`
							where docstatus = 1
							and supplier = %s 
					  		and outstanding_amount > 0
							""", self.party, as_dict=True)
		self.set("material_issue_details", [])

		if res:
			for a in res:
				entry = {
					'reference_name': a.name,
					'posting_date': a.posting_date,
					'total_amount': a.outstanding_amount,
					'allocated_amount': a.outstanding_amount,
					'account': a.debit_account,
				}
				self.append("material_issue_details", entry)
		# else:
		# 	frappe.msgprint("No entries found.")

	def get_total_allocated(self):
		total = 0
		for d in self.material_issue_details:
			total += flt(d.allocated_amount)
		return total
	
	def get_total_deduction(self):
		total = 0
		for d in self.deduction_items:
			total += flt(d.amount)
		return total
	
	def get_total_additional(self):
		total = 0
		for d in self.addition_items:
			total += flt(d.amount)
		return total

	@frappe.whitelist()
	def calculate_totals(self):
		self.total_additional_amount = self.get_total_additional()
		self.total_allocated_amount = self.get_total_allocated()
		self.total_deduction_amount = self.get_total_deduction()
		self.grand_total = flt(self.amount) + flt(self.total_additional_amount) if self.total_additional_amount else self.amount
		
		if self.tds_percent:
			self.tds_amount = flt(flt(self.grand_total, 2) * flt(self.tds_percent, 2) / 100.0, 2)
			self.tds_account = get_tds_account(self.tds_percent, self.company, self.party_type)
		else:
			self.tds_amount = 0
			self.tds_account = None

		self.net_payable = self.outstanding_amount = flt(self.grand_total) - flt(self.total_deduction_amount) - flt(self.total_allocated_amount) - flt(self.tds_amount)

	def update_reference_document(self, cancel=False):
		for item in self.material_issue_details:
			allocated_amount = 0.0
			if flt(item.allocated_amount) > 0:
				balance_amount = frappe.db.get_value("Equipment Material Issue", item.reference_name, "outstanding_amount")
				if flt(balance_amount) < flt(item.allocated_amount) and self.docstatus < 2:
					frappe.throw(_("Row #{0} : Allocated amount Nu. {1}/- cannot be more than Advance Balance Nu. {2}/-").format(item.reference_name, "{:,.2f}".format(flt(item.allocated_amount)),"{:,.2f}".format(flt(balance_amount))))
				else:
					allocated_amount = -1 * flt(item.allocated_amount) if cancel else flt(item.allocated_amount)
					doc = frappe.get_doc("Equipment Material Issue", item.reference_name)
					doc.outstanding_amount = flt(doc.outstanding_amount) - flt(allocated_amount)
					doc.save(ignore_permissions = True)

	def make_gl_entry(self, cancel=False):
		gl_entries = []
		self.make_party_gl_entries(gl_entries)
		self.make_additional_gl_entries(gl_entries)
		self.deduction_gl_entries(gl_entries)
		self.make_tds_gl_entries(gl_entries)
		self.make_material_issue_gl_entries(gl_entries)
		# frappe.throw("<pre>{}</pre>".format(frappe.as_json(gl_entries)))

		gl_entries = merge_similar_entries(gl_entries)
		
		make_gl_entries(gl_entries, update_outstanding="No", cancel=cancel)
	

	def deduction_gl_entries(self, gl_entries):
		if self.deduction_items:
			for d in self.deduction_items:
				entry = {
					"account": d.account,
					"against_voucher": self.name,
					"against_voucher_type": self.doctype,
					"party_type": self.party_type,
					"party": self.party,
					"cost_center": self.cost_center,
					"voucher_type": self.doctype,
					"voucher_no": self.name,
				}

				if self.party_type == "Supplier":
					entry.update({
						"credit": flt(d.amount),
						"credit_in_account_currency": flt(d.amount),
					})
				else:
					entry.update({
						"debit": flt(d.amount),
						"debit_in_account_currency": flt(d.amount),
					})
				gl_entries.append(self.get_gl_dict(entry, self.currency))

	def make_material_issue_gl_entries(self, gl_entries):
		if self.material_issue_details:
			for d in self.material_issue_details:
				gl_entries.append(
					self.get_gl_dict({
						"account": d.account,
						"credit": flt(d.allocated_amount),
						"credit_in_account_currency": flt(d.allocated_amount),
						"against_voucher": self.name,
						"against_voucher_type": self.doctype,
						"party_type": self.party_type,
						"party": self.party,
						"cost_center": self.cost_center,
						"voucher_type": self.doctype,
						"voucher_no": self.name,
					}, self.currency)
				)
	
	def make_additional_gl_entries(self, gl_entries):
		if self.addition_items:
			for d in self.addition_items:
				entry = {
					"account": d.account,
					"against_voucher": self.name,
					"against_voucher_type": self.doctype,
					"party_type": self.party_type,
					"party": self.party,
					"cost_center": self.cost_center,
				}

				if self.party_type == "Supplier":
					entry.update({
						"debit": flt(d.amount),
						"debit_in_account_currency": flt(d.amount),
					})
				else:
					entry.update({
						"credit": flt(d.amount),
						"credit_in_account_currency": flt(d.amount),
					})
				gl_entries.append(self.get_gl_dict(entry, self.currency))

	def make_tds_gl_entries(self, gl_entries):
		if flt(self.tds_amount) > 0:
			def add_tds_gl_entry(account, debit=0, credit=0):
				gl_entries.append(
					self.get_gl_dict({
						"account": account,
						"debit": debit,
						"credit": credit,
						"debit_in_account_currency": debit,
						"credit_in_account_currency": credit,
						"against_voucher": self.name,
						"against_voucher_type": self.doctype,
						"party_type": self.party_type,
						"party": self.party,
						"cost_center": self.cost_center,
						"voucher_type": self.doctype,
						"voucher_no": self.name,
					}, self.currency)
				)

			if self.party_type == "Supplier":
				add_tds_gl_entry(self.tds_account, 0, flt(self.tds_amount, 2))
			else:
				add_tds_gl_entry(self.tds_account, flt(self.tds_amount, 2), 0)

			
	def make_party_gl_entries(self, gl_entries):
		def add_gl_entry(account, debit, credit):
			gl_entries.append(
				self.get_gl_dict({
					"account": account,
					"debit": debit,
					"credit": credit,
					"debit_in_account_currency": debit,
					"credit_in_account_currency": credit,
					"against_voucher": self.name,
					"against_voucher_type": self.doctype,
					"party_type": self.party_type,
					"party": self.party,
					"cost_center": self.cost_center,
					"voucher_type": self.doctype,
					"voucher_no": self.name,
				}, self.currency)
			)

		if self.party_type == "Supplier":
			party_account = frappe.db.get_value("Charge Type", self.invoice_type, "default_expense_account")
			payable_account = frappe.db.get_value("Charge Type", self.invoice_type, "default_payable_account")
			
			if not party_account:
				frappe.throw("The default expense account is not set for the selected Charge Type. Please configure it in the Charge Type record: {}".format(frappe.get_desk_link("Charge Type", self.invoice_type)), title="Expense Account Missing")
			if not payable_account:
				frappe.throw("The default payable account is not set for the selected Charge Type. Please configure it in the Charge Type record: {}".format(frappe.get_desk_link("Charge Type", self.invoice_type)), title="Payable Account Missing")

			add_gl_entry(party_account, self.amount, 0)
			add_gl_entry(payable_account, 0, flt(self.outstanding_amount))
			
		else:
			party_account = frappe.db.get_value("Equipment Type", self.equipment_type, "default_income_account")

			Customer = frappe.qb.DocType("Customer")
			PartyAccount = frappe.qb.DocType("Party Account")

			query = (
				frappe.qb.from_(Customer)
				.join(PartyAccount)
				.on(Customer.name == PartyAccount.parent)
				.where(PartyAccount.company == self.company)
				.select(PartyAccount.account)
			)
			result = query.run()
			if result:
				default_receivable_account = result[0][0]
			else:
				default_receivable_account = None
			
			if not party_account:
				frappe.throw("The default income account is not set for the selected Equipment Type. Please configure it in the Equipment Type record: {}".format(frappe.get_desk_link("Equipment Type", self.equipment_type)), title="Income Account Missing")
			if not default_receivable_account:
				frappe.throw("The default receivable account is not set for the selected Customer. Please configure it in the Customer: {}".format(frappe.get_desk_link("Customer", self.party)), title="Default Receivable Account Missing")

			add_gl_entry(party_account, 0, self.amount)
			add_gl_entry(default_receivable_account, flt(self.outstanding_amount), 0)

@frappe.whitelist()
def make_payment_entry(dt,
	dn,
	party_type=None,
	party=None,
	party_amount=None,
	bank_account=None,
	bank_amount=None,
	payment_type=None,
):
	
	reference_doc = None

	doc = frappe.get_doc(dt, dn)
	
	party_account = set_party_account(dt, dn, doc, party_type)

	party_account_currency = set_party_account_currency(dt, party_account, doc)

	grand_total, outstanding_amount = set_grand_total_and_outstanding_amount(
		party_amount, dt, party_account_currency, doc
	)

	bank = get_bank_cash_account(doc, bank_account)
	if party_type == "Supplier":
		payment_type = "Pay"
	else:
		payment_type = "Receive"

	paid_amount, received_amount = set_paid_amount_and_received_amount(
		dt, party_account_currency, bank, outstanding_amount, payment_type, bank_amount, doc
	)

	paid_amount, received_amount, discount_amount = apply_early_payment_discount(
		paid_amount, received_amount, doc
	)

	pe = frappe.new_doc("Payment Entry")
	pe.branch = doc.branch
	pe.payment_type = payment_type
	pe.company = doc.company
	pe.cost_center = doc.get("cost_center")
	pe.posting_date = nowdate()
	pe.mode_of_payment = doc.get("mode_of_payment")
	pe.party_type = party_type
	pe.party = party
	pe.contact_person = doc.get("contact_person")
	pe.contact_email = doc.get("contact_email")
	pe.ensure_supplier_is_not_blocked()

	pe.paid_from = party_account if payment_type == "Receive" else bank.account
	pe.paid_to = party_account if payment_type == "Pay" else bank.account

	pe.paid_from_account_currency = (
		party_account_currency if payment_type == "Receive" else bank.account_currency
	)
	pe.paid_to_account_currency = (
		party_account_currency if payment_type == "Pay" else bank.account_currency
	)
	pe.paid_amount = paid_amount
	pe.received_amount = received_amount
	pe.letter_head = doc.get("letter_head")

	if pe.party_type in ["Customer", "Supplier"]:
		bank_account = get_party_bank_account(pe.party_type, pe.party)
		pe.set("bank_account", bank_account)
		pe.set_bank_account_data()
	
		pe.append(
			"references",
			{
				"reference_doctype": dt,
				"reference_name": dn,
				"bill_no": doc.get("bill_no"),
				"due_date": doc.get("due_date"),
				"total_amount": grand_total,
				"outstanding_amount": outstanding_amount,
				"allocated_amount": outstanding_amount,
			},
		)

	pe.setup_party_account_field()
	pe.set_missing_values()

	if party_account and bank:
		pe.set_exchange_rate(ref_doc=reference_doc)
		pe.set_amounts()
		if discount_amount:
			pe.set_gain_or_loss(
				account_details={
					"account": frappe.get_cached_value(
						"Company", pe.company, "default_discount_account"
					),
					"cost_center": pe.cost_center
					or frappe.get_cached_value("Company", pe.company, "cost_center"),
					"amount": discount_amount * (-1 if payment_type == "Pay" else 1),
				}
			)
			pe.set_difference_amount()

	return pe

def set_party_account(dt, dn, doc, party_type):
	if party_type == "Supplier":
		party_account = frappe.db.get_value("Charge Type", doc.invoice_type, "default_expense_account")
		
		if not party_account:
			frappe.throw("The default expense account is not set for the selected Charge Type. Please configure it in the Charge Type record: {}".format(frappe.get_desk_link("Charge Type", doc.invoice_type)), title="Expense Account Missing")
	else:
		party_account = frappe.db.get_value("Equipment Type", doc.equipment_type, "default_income_account")
		
		if not party_account:
			frappe.throw("The default income account is not set for the selected Equipment Type. Please configure it in the Equipment Type record: {}".format(frappe.get_desk_link("Equipment Type", doc.equipment_type)), title="Income Account Missing")
	return party_account

def set_party_account_currency(dt, party_account, doc):
	party_account_currency = get_account_currency(party_account)
	return party_account_currency


def set_grand_total_and_outstanding_amount(party_amount, dt, party_account_currency, doc):
	grand_total = outstanding_amount = 0
	grand_total = doc.get("amount")
	outstanding_amount =  doc.get("outstanding_amount")
	return grand_total, outstanding_amount

def get_bank_cash_account(doc, bank_account):
	bank = get_default_bank_cash_account(
		doc.company, "Bank", mode_of_payment=doc.get("mode_of_payment"), account=bank_account
	)

	if not bank:
		bank = get_default_bank_cash_account(
			doc.company, "Cash", mode_of_payment=doc.get("mode_of_payment"), account=bank_account
		)
	return bank

def set_paid_amount_and_received_amount(
	dt, party_account_currency, bank, outstanding_amount, payment_type, bank_amount, doc
):
	paid_amount = received_amount = 0
	if party_account_currency == bank.account_currency:
		paid_amount = received_amount = abs(outstanding_amount)
	elif payment_type == "Receive":
		paid_amount = abs(outstanding_amount)
		if bank_amount:
			received_amount = bank_amount
		else:
			received_amount = paid_amount * doc.get("conversion_rate", 1)
	else:
		received_amount = abs(outstanding_amount)
		if bank_amount:
			paid_amount = bank_amount
		else:
			# if party account currency and bank currency is different then populate paid amount as well
			paid_amount = received_amount * doc.get("conversion_rate", 1)

	return paid_amount, received_amount

def apply_early_payment_discount(paid_amount, received_amount, doc):
	total_discount = 0
	eligible_for_payments = ["Sales Order", "Sales Invoice", "Purchase Order", "Purchase Invoice"]
	has_payment_schedule = hasattr(doc, "payment_schedule") and doc.payment_schedule

	if doc.doctype in eligible_for_payments and has_payment_schedule:
		for term in doc.payment_schedule:
			if (
				not term.discounted_amount
				and term.discount
				and getdate(nowdate()) <= term.discount_date
			):
				if term.discount_type == "Percentage":
					discount_amount = flt(doc.get("grand_total")) * (term.discount / 100)
				else:
					discount_amount = term.discount

				discount_amount_in_foreign_currency = discount_amount * doc.get(
					"conversion_rate", 1
				)

				if doc.doctype == "Sales Invoice":
					paid_amount -= discount_amount
					received_amount -= discount_amount_in_foreign_currency
				else:
					received_amount -= discount_amount
					paid_amount -= discount_amount_in_foreign_currency

				total_discount += discount_amount

		if total_discount:
			money = frappe.utils.fmt_money(total_discount, currency=doc.get("currency"))
			frappe.msgprint(_("Discount of {} applied as per Payment Term").format(money), alert=1)

	return paid_amount, received_amount, total_discount

def get_reference_as_per_payment_terms(
	payment_schedule, dt, dn, doc, grand_total, outstanding_amount
):
	references = []
	for payment_term in payment_schedule:
		payment_term_outstanding = flt(
			payment_term.payment_amount - payment_term.paid_amount,
			payment_term.precision("payment_amount"),
		)

		if payment_term_outstanding:
			references.append(
				{
					"reference_doctype": dt,
					"reference_name": dn,
					"bill_no": doc.get("bill_no"),
					"due_date": doc.get("due_date"),
					"total_amount": grand_total,
					"outstanding_amount": outstanding_amount,
					"payment_term": payment_term.payment_term,
					"allocated_amount": payment_term_outstanding,
				}
			)

	return references