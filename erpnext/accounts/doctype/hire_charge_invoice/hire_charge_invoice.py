# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _, qb, throw, bold
from erpnext.custom_utils import check_future_date
from erpnext.controllers.accounts_controller import AccountsController
from pypika import Case, functions as fn
from erpnext.production.doctype.transporter_rate.transporter_rate import get_transporter_rate
from frappe.utils import flt, cint, money_in_words
from erpnext.accounts.utils import get_tds_account,get_account_type
from erpnext.accounts.general_ledger import (
	get_round_off_account_and_cost_center,
	make_gl_entries,
	make_reverse_gl_entries,
	merge_similar_entries,
)
from erpnext.accounts.party import get_party_account

class HireChargeInvoice(AccountsController):
	def validate(self):
		check_future_date(self.posting_date)
		if not self.arrear_eme_payment:
			self.check_remarks()
		else:
			self.update_rate_amount()
		self.calculate_totals()
		self.set_status()
		self.set_internal_cc_and_branch()
		self.set_internal_customer_account()

	def on_submit(self):
		self.update_logbook()
		self.make_gl_entries()

	def on_cancel(self):
		self.ignore_linked_doctypes = ("GL Entry", "Stock Ledger Entry", "Payment Ledger Entry")
		self.update_logbook()
		self.make_gl_entries()

	def update_logbook(self):
		for a in self.items:
			value = 1
			if self.docstatus == 2:
				value = 0
			logbook = frappe.get_doc("Logbook", a.logbook)
			logbook.db_set("paid", value)

			ehf_doc = frappe.get_doc("Equipment Hiring Form", {"name":logbook.equipment_hiring_form})
			ehf_doc.run_method("validate")
			ehf_doc.save(ignore_permissions=True)

	def before_cancel(self):
		if self.journal_entry and frappe.db.exists("Journal Entry",self.journal_entry):
			doc = frappe.get_doc("Journal Entry", self.journal_entry)
			if doc.docstatus != 2:
				frappe.throw("Journal Entry exists for this transaction {}".format(frappe.get_desk_link("Journal Entry",self.journal_entry)))
	
	@frappe.whitelist()
	def set_internal_cc_and_branch(self):
		if self.party_type == "Supplier":
			return
		else:
			if cint(self.is_internal_customer) == 1:
				branch, cc = frappe.db.get_value("Customer", {"name": self.party}, ["branch", "cost_center"])

				self.db_set("party_branch", branch)
				self.db_set("party_cost_center", cc)
	
	@frappe.whitelist()
	def set_internal_customer_account(self):
		if self.party_type == "Supplier":
			return
		else:
			if cint(self.is_internal_customer) == 1:
				income_account = frappe.db.get_single_value("Maintenance Settings", "equipment_hire_income_account")

				self.db_set("credit_account", income_account)

	#Function to pay arrear base on change in rate
	def update_rate_amount(self):
		for a in self.get("items"):
			rate = self.get_rate(a.equipment_hiring_form, d.posting_date)
			if rate:
				a.new_rate = flt(rate)
				a.rate   = flt(a.new_rate) - flt(a.prev_rate)
				a.amount = flt(a.rate)  * flt(a.total_hours)

	def check_remarks(self):
		if not self.remarks:
			self.remarks = "Hire Charge payment to {0}".format(self.party)
	
	def set_credit_account(self):
		if self.party:
			account = get_party_account(self.party_type, self.party, self.company)
			self.db_set("credit_account", account)
		else:
			frappe.msgprint(str("Pary is required."))
	# fetch rate base on equipment hiring form
	def get_rate(self, ehf):
		rate = frappe.db.sql('''
					select hiring_rate from `tabEHF Rate` where parent = '{ehf}' 
						and docstatus = 1 limit 1
					'''.format(ehf = ehf))
		if rate:
			return rate[0][0]
		else:
			throw("No rates defined in Equipment Hiring Form <b>{}</b>".format(frappe.get_desk_link("Equipment Hiring Form", ehf)),title="Hiring Rate Not Found")

	# def get_rate(self, ehf):
	# 	rate = frappe.db.sql('''
	# 				select hiring_rate from `tabEHF Rate` where parent = '{ehf}' 
	# 					and from_date <= '{posting_date}' 
	# 					and ifnull(to_date, NOW()) >= '{posting_date}' 
	# 					and docstatus = 1 limit 1
	# 				'''.format(ehf = ehf, posting_date = posting_date))
	# 	if rate:
	# 		return rate[0][0]
	# 	else:
	# 		throw("No rates defined in Equipment Hiring Form <b>{}</b> for date <b>{}</b>".format(frappe.get_desk_link("Equipment Hiring Form", ehf), posting_date),title="Hiring Rate Not Found")
	
	def set_status(self, update=False, status=None, update_modified=True):
		if self.is_new():
			self.status = "Draft"
			return

		if cint(self.is_internal_customer) == 0:
			outstanding_amount = flt(self.outstanding_amount, 2)
			if not status:
				if self.docstatus == 2:
					status = "Cancelled"
				elif self.docstatus == 1:
					if outstanding_amount > 0 and flt(self.payable_amount) > outstanding_amount:
						self.status = "Partly Paid"
					elif outstanding_amount > 0 :
						self.status = "Unpaid"
					elif outstanding_amount <= 0:
						self.status = "Paid"
					else:
						self.status = "Submitted"
				else:
					self.status = "Draft"
		else:
			if self.docstatus == 1:
				self.status = "Submitted"

		if update:
			self.db_set("status", self.status, update_modified=update_modified)

	# calculate total
	@frappe.whitelist()
	def calculate_totals(self):
		total = total_hrs = 0
		
		for a in self.items:
			total += flt(a.amount)
			total_hrs += flt(a.total_hours,2)
			if not a.expense_account and a.expense_head:
				a.expense_account = frappe.db.get_value("Expense Head",a.expense_head,"expense_account")
				if not a.expense_account:
					throw("Expense Account not defined in Expense Head {}".format(bold(a.expense_head)),title="Expense Account Not Found")
		self.grand_total = flt(total,2)

		# tds
		if self.tds_percent:
			self.tds_amount  = flt(flt(self.grand_total,2) * flt(self.tds_percent,2) / 100.0,2)
			self.tds_account = get_tds_account(self.tds_percent,self.company)
		else:
			self.tds_amount  = 0
			self.tds_account = None

		total_deductions = 0
		for d in self.get('deduct_items'):
			if d.amount <= 0:
				frappe.throw("Deduction amount should be more than zero")
			if not d.account:
				frappe.throw("Account is mandatory for deductions")
			total_deductions += flt(d.amount, 2)
		self.total_deduction = flt(total_deductions + self.tds_amount,2)
		self.payable_amount = self.outstanding_amount = flt(self.grand_total - self.total_deduction, 2)
		self.total_hours = total_hrs
		
	def make_gl_entries(self):
		gl_entries = []
		self.make_supplier_gl_entry(gl_entries)
		self.make_customer_gl_entry(gl_entries)
		self.make_item_gl_entries(gl_entries)
		self.deduction_gl_entries(gl_entries)
		self.make_tds_gl_entries(gl_entries)
		gl_entries = merge_similar_entries(gl_entries)
		make_gl_entries(gl_entries,update_outstanding="No",cancel=self.docstatus == 2)
	
	def deduction_gl_entries(self,gl_entries):
		for d in self.deduct_items:
			party_type = party = ''
			if get_account_type( d.account, self.company) in ["Receivable","Payable","Expense Account","Income Account"]:
				party_type = self.party_type
				party = self.party
			
			if self.party_type == "Supplier":
				gl_entries.append(
					self.get_gl_dict({
						"account":  d.account,
						"credit": flt(d.amount,2),
						"credit_in_account_currency": flt(d.amount,2),
						"against_voucher": self.name,
						"against_voucher_type": self.doctype,
						"party_type": party_type,
						"party": party,
						"cost_center": self.cost_center,
						"voucher_type":self.doctype,
						"voucher_no":self.name
					}, self.currency)
				)
			else:
				gl_entries.append(
					self.get_gl_dict({
						"account":  d.account,
						"debit": flt(d.amount,2),
						"debit_in_account_currency": flt(d.amount,2),
						"against_voucher": self.name,
						"against_voucher_type": self.doctype,
						"party_type": party_type,
						"party": party,
						"cost_center": self.cost_center,
						"voucher_type":self.doctype,
						"voucher_no":self.name
					}, self.currency)
				)

	def make_item_gl_entries(self, gl_entries):
		expense_account = frappe.db.get_single_value("Maintenance Settings", "equipment_hire_expense_account")
		for item in self.items:
			party_type = party = ''
			if  get_account_type( expense_account, self.company) in ["Receivable","Payable","Expense Account","Income Account"]:
				party_type = self.party_type
				party = self.party

			if self.party_type == "Supplier":
				gl_entries.append(
					self.get_gl_dict({
							"account":  expense_account,
							"debit": flt(item.amount,2),
							"debit_in_account_currency": flt(item.amount,2),
							"against_voucher": self.name,
							"against_voucher_type": self.doctype,
							"party_type": party_type,
							"party": party,
							"cost_center": self.cost_center,
							"voucher_type":self.doctype,
							"voucher_no":self.name
					}, self.currency)
				)
			else:
				if cint(self.is_internal_customer) == 0:
					gl_entries.append(
						self.get_gl_dict({
								"account": expense_account,
								"credit": flt(item.amount,2),
								"credit_in_account_currency": flt(item.amount,2),
								"against_voucher": self.name,
								"against_voucher_type": self.doctype,
								"party_type": party_type,
								"party": party,
								"cost_center": self.cost_center,
								"voucher_type":self.doctype,
								"voucher_no":self.name
						}, self.currency)
					)
				else:
					gl_entries.append(
						self.get_gl_dict({
								"account": expense_account,
								"debit": flt(item.amount,2),
								"debit_in_account_currency": flt(item.amount,2),
								"against_voucher": self.name,
								"against_voucher_type": self.doctype,
								"party_type": party_type,
								"party": party,
								"cost_center": self.party_cost_center,
								"voucher_type":self.doctype,
								"voucher_no":self.name
						}, self.currency)
					)

	def make_tds_gl_entries(self,gl_entries):
		if flt(self.tds_amount)> 0:
			party_type = party = ''
			if  get_account_type(self.tds_account, self.company) in ["Receivable","Payable","Expense Account","Income Account"]:
				party_type = self.party_type
				party = self.party
			if self.party_type == "Supplier":
				gl_entries.append(
					self.get_gl_dict({
							"account":  self.tds_account,
							"credit": flt(self.tds_amount,2),
							"credit_in_account_currency": flt(self.tds_amount,2),
							"against_voucher": self.name,
							"against_voucher_type": self.doctype,
							"party_type": party_type,
							"party": party,
							"cost_center": self.cost_center,
							"voucher_type":self.doctype,
							"voucher_no":self.name
					}, self.currency)
				)
			else:
				gl_entries.append(
					self.get_gl_dict({
							"account":  self.tds_account,
							"credit": flt(self.tds_amount,2),
							"credit_in_account_currency": flt(self.tds_amount,2),
							"against_voucher": self.name,
							"against_voucher_type": self.doctype,
							"party_type": party_type,
							"party": party,
							"cost_center": self.cost_center,
							"voucher_type":self.doctype,
							"voucher_no":self.name
					}, self.currency)
				)


	def make_supplier_gl_entry(self, gl_entries):
		if flt(self.payable_amount) > 0 and self.party_type == "Supplier":
			# Did not use base_grand_total to book rounding loss gle
			gl_entries.append(
				self.get_gl_dict({
					"account": self.credit_account,
					"credit": flt(self.payable_amount,2),
					"credit_in_account_currency": flt(self.payable_amount,2),
					"against_voucher": self.name,
					"party_type": self.party_type,
					"party": self.party,
					"against_voucher_type": self.doctype,
					"cost_center": self.cost_center,
					"voucher_type":self.doctype,
					"voucher_no":self.name
				}, self.currency))
	
	def make_customer_gl_entry(self, gl_entries):
		if flt(self.payable_amount) > 0 and self.party_type == "Customer":
			if cint(self.is_internal_customer) == 0:
				gl_entries.append(
					self.get_gl_dict({
							"account": self.credit_account,
							"party_type": self.party_type,
							"party": self.party,
							"debit": flt(self.payable_amount,2),
							"debit_in_account_currency": flt(self.payable_amount,2),
							"against_voucher": self.name,
							"against_voucher_type": self.doctype,
							"cost_center": self.cost_center,
							"voucher_type":self.doctype,
							"voucher_no":self.name
						}, self.currency))
			else:
				gl_entries.append(
					self.get_gl_dict({
							"account": self.credit_account,
							"party_type": self.party_type,
							"party": self.party,
							"credit": flt(self.payable_amount,2),
							"credit_in_account_currency": flt(self.payable_amount,2),
							"against_voucher": self.name,
							"against_voucher_type": self.doctype,
							"cost_center": self.cost_center,
							"voucher_type":self.doctype,
							"voucher_no":self.name
						}, self.currency))


	# fetch logbook details
	@frappe.whitelist()
	def get_logbooks(self):
		if not self.branch:
			frappe.throw("Select Branch")
		if not self.party:
			frappe.throw("Select Party")

		if not self.from_date or not self.to_date:
			frappe.throw("From Date and To Date are mandatory")

		l = qb.DocType("Logbook")
		li = qb.DocType("Logbook Item")
		eme = qb.DocType("Hire Charge Invoice")
		emei = qb.DocType("EME Invoice Item")
		entries = (qb.from_(l)
					.inner_join(li)
					.on(l.name == li.parent)
					.select((l.name).as_("logbook"),l.from_date,l.posting_date,l.to_date,
						l.equipment_hiring_form,
						li.expense_head,(li.hours).as_("total_hours"),
						l.equipment)
					.where((l.docstatus == 1) 
						& (l.party_type == self.party_type)
						& (l.party == self.party)
						& (l.cost_center == self.cost_center)
						& (l.from_date >= self.from_date)
						& (l.to_date <= self.to_date)
						& (l.paid == 0)
						& ((l.name).
								notin(qb.from_(eme).inner_join(emei).on(eme.name==emei.parent).select(emei.logbook)
									.where((eme.docstatus!=2)&(emei.logbook==l.name)&(eme.name != self.name)))
							))
					.orderby(l.posting_date,li.expense_head)
					).run(as_dict=True)

		self.set('items', [])
		if len(entries) == 0:
			frappe.msgprint("No valid logbooks found for owner {} between {} and {}.You must have pulled in other Hire Charge Invoices(including draft invoices)".format(frappe.bold(self.party), frappe.bold(self.from_date),frappe.bold(self.to_date)), raise_exception=True)

		total = 0
		exist_list = {}
		for d in entries:
			d.rate = self.get_rate(d.equipment_hiring_form)
			d.amount = flt(d.total_hours * d.rate, 2)
			row = self.append('items', {})
			row.update(d)
		# self.calculate_totals()

	@frappe.whitelist()
	def post_journal_entry(self):
		if self.journal_entry and frappe.db.exists("Journal Entry",{"name":self.journal_entry,"docstatus":("!=",2)}):
			frappe.msgprint(_("Journal Entry Already Exists {}".format(frappe.get_desk_link("Journal Entry",self.journal_entry))))
		if not self.payable_amount:
			frappe.throw(_("Amount Receivable or Payable Amount should be greater than zero"))
			
		credit_account = self.credit_account
	
		if not credit_account:
			frappe.throw("Account is mandatory")
		r = []
		if self.remarks:
			r.append(_("Note: {0}").format(self.remarks))

		remarks = ("").join(r) #User Remarks is not mandatory
		bank_account = frappe.db.get_value("Company",self.company, "default_bank_account")
		imprest_advance_account = frappe.db.get_value("Company",self.company, "imprest_advance_account")
		if self.settle_imprest_advance == 1 and self.party_type == "Supplier" and not imprest_advance_account:
			frappe.throw("Imprest Advance is not set in Company settings")
		if not bank_account:
			frappe.throw(_("Default bank account is not set in company {}".format(frappe.bold(self.company))))
		
		# Posting Journal Entry
		je = frappe.new_doc("Journal Entry")
		je.flags.ignore_permissions=1
		je.update({
			"doctype": "Journal Entry",
			"voucher_type": "Bank Entry",
			"naming_series": "Bank Payment Voucher",
			"title": "Hire Charge Invoice "+ self.party,
			"user_remark": "Note: " + "Hire Charge Payment - " + self.party if self.party_type=="Supplier" else "Note: " + "Hire Charge Receivable - " + self.party,
			"posting_date": self.posting_date,
			"company": self.company,
			"total_amount_in_words": money_in_words(self.payable_amount),
			"branch": self.branch,
			"reference_type":self.doctype,
			"referece_doctype":self.name,
		})
		if self.party_type == "Supplier":
			je.append("accounts",{
				"account": credit_account,
				"debit_in_account_currency": flt(self.payable_amount,2),
				"cost_center": self.cost_center,
				"party_check": 1,
				"party_type": self.party_type,
				"party": self.party,
				"reference_type": "Hire Charge Invoice",
				"reference_name": self.name
			})
			if self.
			je.append("accounts",{
				"account": bank_account,
				"credit_in_account_currency": flt(self.payable_amount,2),
				"cost_center": self.cost_center
			})
		else:
			je.append("accounts",{
				"account": credit_account,
				"credit_in_account_currency": flt(self.payable_amount,2),
				"cost_center": self.cost_center if cint(self.is_internal_customer) == 0 else self.party_cost_center,
				"party_check": 1,
				"party_type": self.party_type,
				"party": self.party,
				"reference_type": "Hire Charge Invoice",
				"reference_name": self.name
			})
			if self.settle_imprest_advance == 1:
				je.append("accounts",{
					"account": imprest_advance_account,
					"debit_in_account_currency": flt(self.payable_amount,2),
					"party_type": "Employee",
					"party": self.imprest_party,
					"cost_center": self.cost_center if cint(self.is_internal_customer) == 0 else self.party_cost_center
				})
			else:
				je.append("accounts",{
					"account": bank_account,
					"debit_in_account_currency": flt(self.payable_amount,2),
					"cost_center": self.cost_center if cint(self.is_internal_customer) == 0 else self.party_cost_center
				})

		je.insert()
		#Set a reference to the claim journal entry
		self.db_set("journal_entry",je.name)
		frappe.msgprint(_('{0} posted to accounts').format(frappe.get_desk_link("Journal Entry",je.name)))

def set_missing_values(source, target):
	target.run_method("set_missing_values")
	
@frappe.whitelist()
def make_arrear_payment(source_name, target_doc=None):
	from frappe.model.mapper import get_mapped_doc

	def postprocess(source, target_doc):
		set_missing_values(source, target_doc)

	def update_item(obj, target, source_parent):
		target.rate = 0.00

	doclist = get_mapped_doc("Hire Charge Invoice", source_name, 	{
		"Hire Charge Invoice": {
			"doctype": "Hire Charge Invoice",
			"field_map": {
				"naming_series": "naming_series",
			},
			"validation": {
				"docstatus": ["=", 1],
			}
		},
		"EME Invoice Item": {
			"doctype": "EME Invoice Item",
			"field_map": {
					"rate": "prev_rate"
				},
			"postprocess": update_item
		}
	}, target_doc, postprocess)

	return doclist

# query permission
def get_permission_query_conditions(user):
	if not user: user = frappe.session.user
	user_roles = frappe.get_roles(user)

	if user == "Administrator" or "System Manager" in user_roles: 
		return

	return """(
		`tabHire Charge Invoice`.owner = '{user}'
		or 
		exists(select 1
			from `tabEmployee` as e
			where e.branch = `tabHire Charge Invoice`.branch
			and e.user_id = '{user}')
		or
		exists(select 1
			from `tabEmployee` e, `tabAssign Branch` ab, `tabBranch Item` bi
			where e.user_id = '{user}'
			and ab.employee = e.name
			and bi.parent = ab.name
			and bi.branch = `tabHire Charge Invoice`.branch)
	)""".format(user=user)
	
