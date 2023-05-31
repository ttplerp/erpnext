# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt, get_last_day, date_diff, add_to_date, cint
from frappe import _
from erpnext.accounts.general_ledger import make_gl_entries
from erpnext.controllers.accounts_controller import AccountsController

class RentalPayment(AccountsController):
	def validate(self):
		self.validate_rental_bill_gl_entry()
		self.generate_penalty()
		self.calculate_discount()
		self.calculate_totals()
		self.set_missing_value()
		if self.is_nhdcl_employee:
			self.bank_account = ''

	def on_submit(self):
		self.update_rental_bill()
		self.post_gl_entry()

	def on_cancel(self):
		self.flags.ignore_links = True
		if self.clearance_date:
			frappe.throw("Already done bank reconciliation. Cannot cancel.")
		self.post_gl_entry()
		self.update_rental_bill()

	def validate_rental_bill_gl_entry(self):
		counts = 0
		for d in self.get('items'):
			if d.security_deposit_amount > 0 and not d.rental_bill:
				continue
			else:
				counts += 1
				chk_gl_post = frappe.db.get_value("Rental Bill", d.rental_bill, "gl_entry")
				if not chk_gl_post:
					frappe.throw(_("#Row {}, Rental Bill {} of Tenant {} is not posted to accounts").format(d.idx, d.rental_bill, d.tenant))
		# count only the rental bills
		self.number_of_rental_bill = counts

	def generate_penalty(self):
		if self.items and not self.write_off_penalty:
			total_penalty = 0.00
			for a in self.items:
				if not a.write_off_penalty:
					if a.bill_amount:
						if a.auto_calculate_penalty:
							bill_date = frappe.db.get_value("Rental Bill", a.rental_bill, "posting_date")
							last_date = get_last_day(bill_date)
							no_of_days = date_diff(self.posting_date, last_date)
							examption_days = frappe.db.get_single_value("Rental Setting", "payment_due_on")
							penalty_rate = frappe.db.get_single_value("Rental Setting", "penalty_rate")
							if examption_days and penalty_rate:
								from datetime import datetime
								from dateutil import relativedelta
								start_penalty_from = add_to_date(last_date, days=cint(examption_days))
								date1 = datetime.strptime(str(start_penalty_from), '%Y-%m-%d')
								date2 = datetime.strptime(str(self.posting_date), '%Y-%m-%d')
								months = (date2.year - date1.year) * 12 + (date2.month - date1.month)
								penalty_amt = 0.00
								if flt(no_of_days) > flt(examption_days):
									penalty_on = 0.00
									if not a.dont_apply_discount and a.discount_amount > 0:
										penalty_on = flt(a.bill_amount) - flt(a.discount_amount)
									else:
										penalty_on = flt(a.bill_amount)
									penalty_amt =  flt(penalty_rate)/100.00 * flt(months +1) * flt(penalty_on)
								a.penalty = round(penalty_amt)
								total_penalty += a.penalty
							else:
								frappe.throw("Penalty Rate and Payment Due Date are missing in Rental Setting")
						else:
							if a.penalty > 0:
								total_penalty += a.penalty
				else:
					a.penalty = 0.00					
			self.penalty_amount = round(total_penalty)
		else:
			for a in self.item:
				a.write_off_penalty = 1
				a.penalty = 0.00
			self.penalty_amount = 0.00

	def calculate_discount(self):
		if self.discount_percent > 0:
			discount_amount = 0.00
			for a in self.items:
				if not a.dont_apply_discount:
					discount = round(flt(a.bill_amount) * flt(self.discount_percent)/100)
					a.discount_amount = flt(discount)
					discount_amount += flt(discount)
			self.discount_amount = discount_amount

	def calculate_totals(self):	
		# if not self.tenant:
		# 	self.tenant_name = ""
		rent_received = security_deposit = total_amount_received = excess = pre_rent = tds_amount = write_off_amount = 0.00
		for a in self.items:
			rent_received_amt = flt(a.rent_received) + flt(a.tds_amount) + flt(a.discount_amount)
			a.total_amount_received = flt(a.rent_received) + flt(a.security_deposit_amount) + flt(a.penalty) + flt(a.excess_amount) + flt(a.pre_rent_amount)
			if a.rent_write_off:
				a.balance_rent = flt(a.bill_amount) - flt(a.rent_received) - flt(a.tds_amount) - flt(a.discount_amount) - flt(a.rent_write_off_amount)
			else:
				a.balance_rent = flt(a.bill_amount) - flt(a.rent_received) - flt(a.tds_amount) - flt(a.discount_amount)

			if flt(rent_received_amt) > flt(a.bill_amount):
				a.rent_received = flt(a.bill_amount) - flt(a.tds_amount) - flt(a.discount_amount)
				a.balance_rent = flt(a.bill_amount) - flt(a.rent_received) - flt(a.tds_amount) - flt(a.discount_amount)
				
				frappe.msgprint("Rent Received amount is changed to {} as the total of Rent receive + Discount + TDS cannot be more than Bill Amount {} for tenant {}".format(a.rent_received, a.bill_amount, a.tenant_name))
			
			if a.balance_rent > 0 and (a.pre_rent_amount > 0 or a.excess_amount > 0):
				frappe.throw("Pre rent and excess rent collection not allowed as current rent is not settled")

			write_off_amount += flt(a.rent_write_off_amount)
			tds_amount += flt(a.tds_amount)
			rent_received += flt(a.rent_received)
			security_deposit += flt(a.security_deposit_amount)
			excess += flt(a.excess_amount)
			pre_rent += flt(a.pre_rent_amount)
			total_amount_received += flt(a.rent_received) + flt(a.security_deposit_amount) + flt(a.penalty) + flt(a.excess_amount) + flt(a.pre_rent_amount)

		if self.rent_write_off:
			self.rent_write_off_amount = write_off_amount
		self.rent_received = rent_received
		self.security_deposit_amount = security_deposit
		self.excess_amount = excess
		self.pre_rent_amount = pre_rent
		self.tds_amount = tds_amount
		self.total_amount_received = flt(total_amount_received)
		if self.tds_amount > 0 and not self.tds_account:
			frappe.throw("Please select TDS Account")

	def set_missing_value(self):
		if self.tds_amount and not self.tds_account:
			self.tds_account = frappe.db.get_value("Company", self.company, "tds_deducted")
			if not self.tds_account:
				frappe.throw("Missing value for TDS Deducted by Customer in Company")

	def update_rental_bill(self):					
		if self.docstatus == 1:
			for a in self.get('items'):
				if a.rental_bill:
					doc = frappe.get_doc("Rental Bill", a.rental_bill)
					if doc.docstatus != 1:
						frappe.throw("#Row {}, Rental Bill {} is not valide".format(a.idx, doc.name))

					doc.append("rental_payment_details",{
									"reference_type"   : "Rental Payment",
									"reference"        : self.name,
									"received_amount"  : flt(a.rent_received),
									"pre_rent_amount"  : flt(a.pre_rent_amount),
									"discount_amount"  : flt(a.discount_amount),
									"tds_amount" 	   : flt(a.tds_amount),
									"excess_amount" 	: flt(a.excess_amount),
									"penalty_amount" 	: flt(a.penalty),
									"rent_write_off_amount" : flt(a.rent_write_off_amount),
									"payment_date" 	   : self.posting_date
								})
					doc.received_amount = flt(doc.received_amount) + flt(a.rent_received)
					doc.pre_rent_amount = flt(doc.pre_rent_amount) + flt(a.pre_rent_amount)
					doc.tds_amount = flt(doc.tds_amount) + flt(a.tds_amount)
					doc.discount_amount = flt(doc.discount_amount) + flt(a.discount_amount)
					doc.penalty = flt(doc.penalty) + flt(a.penalty)
					doc.rent_write_off_amount = flt(doc.rent_write_off_amount) + flt(a.rent_write_off_amount)
					doc.save()
					""" update Tenant Information for Security Deposit Received check """
					if a.security_deposit_amount > 0:
						ti_doc = frappe.get_doc("Tenant Information", a.tenant)
						if flt(a.security_deposit_amount) != flt(ti_doc.security_deposit):
							frappe.throw("Security deposit amount {} at Tenant Information is not equal with {}".format(ti_doc.security_deposit, a.security_deposit_amount))
						ti_doc.security_deposit_received = 1
						ti_doc.save()
		else:
			for a in self.get('items'):
				if a.rental_bill:
					doc = frappe.get_doc("Rental Bill", a.rental_bill)
					if doc.docstatus != 1:
						frappe.throw("#Row {}, Rental Bill {} is not valide".format(a.idx, doc.name))

					doc.received_amount = flt(doc.received_amount) - flt(a.rent_received)
					doc.pre_rent_amount = flt(doc.pre_rent_amount) - flt(a.pre_rent_amount)
					doc.tds_amount = flt(doc.tds_amount) - flt(a.tds_amount)
					doc.discount_amount = flt(doc.discount_amount) - flt(a.discount_amount)
					doc.penalty = flt(doc.penalty) - flt(a.penalty)
					doc.rent_write_off_amount = flt(doc.rent_write_off_amount) - flt(a.rent_write_off_amount)
					doc.save()
					""" update Tenant Information for Security Deposit Received check """
					if a.security_deposit_amount > 0:
						ti_doc = frappe.get_doc("Tenant Information", a.tenant)
						ti_doc.security_deposit_received = 0
						ti_doc.save()

			frappe.db.sql("delete from `tabRental Payment Details` where reference='{0}'".format(self.name))
			frappe.db.commit()

	def post_gl_entry(self):
		gl_entries = []
		cost_center = frappe.db.get_value("Branch", self.branch, "cost_center")
		business_activity = frappe.db.get_single_value("Rental Setting", "business_activity")
		debtor_rental = frappe.db.get_single_value("Rental Account Setting", "revenue_claim_account")
		pre_rent_account = frappe.db.get_single_value("Rental Account Setting", "pre_rent_account")
		penalty_account = frappe.db.get_single_value("Rental Account Setting", "penalty_account")
		excess_payment_account = frappe.db.get_single_value("Rental Account Setting", "excess_payment_account")
		discount_account = frappe.db.get_single_value("Rental Account Setting", "discount_account")
		security_deposit_account = frappe.db.get_single_value("Rental Account Setting", "security_deposit_account")
		
		if self.is_nhdcl_employee:
			self.post_debit_account(gl_entries, cost_center, business_activity)
		else:
			if not self.rent_write_off and not self.bank_account:
				frappe.throw(_("Bank Account is missing."))
			gl_entries.append(
				self.get_gl_dict({
					"account": self.bank_account if not self.rent_write_off else self.rent_write_off_account,
					"debit": self.total_amount_received if not self.rent_write_off else self.rent_write_off_amount,
					"debit_in_account_currency": self.total_amount_received if not self.rent_write_off else self.rent_write_off_amount,
					"voucher_no": self.name,
					"voucher_type": "Rental Payment",
					"cost_center": cost_center,
					"company": self.company,
					"remarks": self.remarks,
					"business_activity": business_activity
				})
			)
		
		for a in self.get('items'):
			# frappe.throw(a.tenant)
			# party_name = frappe.db.get_value("Customer", {"customer_code": frappe.db.get_value("Tenant Information", a.tenant, "customer_code")},"name")
			party_name = a.customer
			account_type = frappe.db.get_value("Account", debtor_rental, "account_type") or ""
			# frappe.throw(party_name)
			if account_type in ["Receivable", "Payable"]:
				party = party_name
				party_type = "Customer"
			else:
				party = None
				party_type = None

			debtor_amount = flt(a.rent_received) + flt(a.discount_amount) + flt(a.tds_amount) + flt(a.rent_write_off_amount)
			if debtor_amount > 0:
				gl_entries.append(
					self.get_gl_dict({
						"account": debtor_rental,
						"credit": debtor_amount,
						"credit_in_account_currency": debtor_amount,
						"voucher_no": self.name,
						"voucher_type": "Rental Payment",
						"against_voucher_type": "Rental Bill",
						"against_voucher": a.rental_bill,
						"cost_center": cost_center,
						"party": party,
						"party_type": party_type,
						"company": self.company,
						"remarks": self.remarks,
						"business_activity": business_activity
					})
				)
			if a.pre_rent_amount > 0:
				account_type = frappe.db.get_value("Account", pre_rent_account, "account_type") or ""
				if account_type in ["Receivable", "Payable"]:
					party = party_name
					party_type = "Customer"
				else:
					party = None
					party_type = None

				gl_entries.append(
					self.get_gl_dict({
						"account": pre_rent_account,
						"credit": flt(a.pre_rent_amount),
						"credit_in_account_currency": flt(a.pre_rent_amount),
						"voucher_no": self.name,
						"voucher_type": "Rental Payment",
						"cost_center": cost_center,
						"party": party,
						"party_type": party_type,
						"company": self.company,
						"remarks": self.remarks,
						"business_activity": business_activity
					})
				)
			
			if a.security_deposit_amount > 0:
				account_type = frappe.db.get_value("Account", security_deposit_account, "account_type") or ""
				if account_type in ["Receivable", "Payable"]:
					party = party_name
					party_type = "Customer"
				else:
					party = None
					party_type = None
				gl_entries.append(
					self.get_gl_dict({
						"account": security_deposit_account,
						"credit": flt(a.security_deposit_amount),
						"credit_in_account_currency": flt(a.security_deposit_amount),
						"voucher_no": self.name,
						"voucher_type": "Rental Payment",
						"cost_center": cost_center,
						"party": party,
						"party_type": party_type,
						"company": self.company,
						"remarks": self.remarks,
						"business_activity": business_activity
					})
				)

		if self.tds_amount > 0:
			gl_entries.append(
				self.get_gl_dict({
					"account": self.tds_account,
					"debit": self.tds_amount,
					"debit_in_account_currency": self.tds_amount,
					"voucher_no": self.name,
					"voucher_type": self.doctype,
					"cost_center": cost_center,
					"company": self.company,
					"remarks": self.remarks,
					"business_activity": business_activity
					})
				)
		
		if self.discount_amount > 0:
			gl_entries.append(
				self.get_gl_dict({
					"account": discount_account,
					"debit": self.discount_amount,
					"debit_in_account_currency": self.discount_amount,
					"voucher_no": self.name,
					"voucher_type": self.doctype,
					"cost_center": cost_center,
					"company": self.company,
					"remarks": self.remarks,
					"business_activity": business_activity
					})
				)
		if self.penalty_amount > 0 and not self.write_off_penalty:
			gl_entries.append(
				self.get_gl_dict({
					"account": penalty_account,
					"credit": self.penalty_amount,
					"credit_in_account_currency": self.penalty_amount,
					"voucher_no": self.name,
					"voucher_type": self.doctype,
					"cost_center": cost_center,
					"company": self.company,
					"remarks": self.remarks,
					"business_activity": business_activity
					})
				)

		if self.excess_amount > 0:
			gl_entries.append(
				self.get_gl_dict({
					"account": excess_payment_account,
					"credit": self.excess_amount,
					"credit_in_account_currency": self.excess_amount,
					"voucher_no": self.name,
					"voucher_type": self.doctype,
					"cost_center": cost_center,
					"company": self.company,
					"remarks": self.remarks,
					"business_activity": business_activity
					})
				)
		make_gl_entries(gl_entries, cancel=(self.docstatus == 2),update_outstanding="Yes", merge_entries=False)

	def post_debit_account(self, gl_entries, cost_center, business_activity):
		for a in self.get('item'):
			party = frappe.db.get_value("Tenant Information", a.tenant, "nhdcl_employee")
			party_type = "Employee"
			if not self.debit_account:
				frappe.throw(_("Debit Account is missing."))
			if a.total_amount_received > 0:
				gl_entries.append(
					self.get_gl_dict({
						"account": self.debit_account,
						"debit": a.total_amount_received,
						"debit_in_account_currency": a.total_amount_received,
						"voucher_no": self.name,
						"voucher_type": "Rental Payment",
						"cost_center": cost_center,
						"party": party,
						"party_type": party_type,
						"company": self.company,
						"remarks": self.remarks,
						"business_activity": business_activity
					})
				)
		return gl_entries

	@frappe.whitelist()
	def get_rental_bills(self):
		self.set('items', [])
		total_bill_amount = rent_write_off_amount = 0
		rentals = self.get_rental_list()
		if not rentals:
			frappe.throw(_("No rental bill for the mentioned criteria"))

		for d in rentals:
			# self.append('items', d)
			row = self.append('items', {})
			if self.rent_write_off:
				row.rent_write_off = 1
				row.rent_write_off_amount = flt(d.bill_amount)
				rent_write_off_amount += flt(d.bill_amount)
			else:
				row.rent_received = flt(d.bill_amount)
				row.total_amount_received = flt(d.bill_amount)
				row.auto_calculate_penalty = 1
			total_bill_amount += flt(d.bill_amount)
			row.update(d)
		self.number_of_rental_bill = len(rentals)
		return {"number_of_rental_bill":self.number_of_rental_bill, "total_bill_amount":total_bill_amount, "rent_write_off_amount":rent_write_off_amount}

	def get_rental_list(self):
		condition = " and branch='{0}' and fiscal_year='{1}'".format(self.branch, self.fiscal_year)
		if self.month:
			condition += " and month='{}'".format(self.month)
		if self.tenant:
			condition += " and tenant='{}'".format(self.tenant)
		if self.is_nhdcl_employee:
			condition += " and is_nhdcl_employee=1"
		if self.dzongkhag:
			condition += " and dzongkhag='{}'".format(self.dzongkhag)
		if self.ministry_and_agency:
			condition += " and ministry_agency='{}'".format(self.ministry_and_agency)
		if self.tenant_department_name:
			condition += " and department='{}'".format(self.tenant_department_name)

		rental_bills = frappe.db.sql("""select name as rental_bill, tenant, tenant_name, customer, 
						(receivable_amount - received_amount - discount_amount - tds_amount - adjusted_amount - rent_write_off_amount) as bill_amount, 
						fiscal_year, month, ministry_agency as ministry_and_agency, department as tenant_department
						from `tabRental Bill` 
						where docstatus=1 and outstanding_amount > 0 {cond} 
						order by tenant_name""".format(cond=condition), as_dict=1)
		if not rental_bills:
			frappe.msgprint(_("No rental bill found for processing rental payment"))

		return rental_bills
