# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.mapper import get_mapped_doc
from frappe.model.document import Document
from erpnext.custom_utils import check_future_date
from erpnext.controllers.accounts_controller import AccountsController
from frappe import _
from frappe.utils import flt, money_in_words
from erpnext.accounts.party import get_party_account
from erpnext.accounts.general_ledger import make_gl_entries

class RepairAndServiceInvoice(AccountsController):
	def validate(self):
		self.calculate_total_amount()
		self.set_status()
		self.update_outstanding_amount()
		self.validate_imprest_party_amount()



	def on_submit(self):
		self.set_status(update=True)
		self.validate_amount()
		self.update_repair_and_service()
		self.update_supplier_advance()
		self.make_gl_entry()

	def on_cancel(self):
		self.update_repair_and_service()
		self.update_supplier_advance(cancel=True)
		self.ignore_linked_doctypes = (
			"GL Entry",
			"Stock Ledger Entry",
			"Payment Ledger Entry",
		)
		self.make_gl_entry()

	def validate_amount(self):
		if self.outstanding_amount < 0:
			frappe.throw(
				title="Invalid Outstanding Amount",
				msg="Outstanding amount cannot be negative: {}. Please adjust your advance amount.".format(
					frappe.bold(frappe.format_value(self.outstanding_amount, {"fieldtype": "Currency", "options": self.currency}))
				)
			)

	def update_repair_and_service(self):
		if not self.repair_and_services:
			return
		value = 1
		if self.docstatus == 2:
			value = 0
		doc = frappe.get_doc("Repair And Services", self.repair_and_services)
		doc.db_set("paid", value)

	def set_status(self, update=False, status=None, update_modified=True):
		if self.is_new():
			self.status = "Draft"
			return
		outstanding_amount = flt(self.outstanding_amount, 2)
		if not status:
			if self.docstatus == 2:
				status = "Cancelled"
			elif self.docstatus == 1:
				if update:
					if outstanding_amount > 0:
						amt_aft_tds_discount = 0.0
						amt_aft_tds_discount = flt(self.tds_amount)+flt(self.deduction_amount)
						temp = self.total_amount - amt_aft_tds_discount
						if temp == self.outstanding_amount:
							self.status = "Overdue"
						else:
							self.status = "Partly Paid"
					elif outstanding_amount == 0.00:
						self.status = "Paid"
				else:
					self.status = "Unpaid"
			else:
				self.status = "Draft"

		if update:
			self.db_set("status", self.status, update_modified=update_modified)

	def validate_imprest_party_amount(self):
		if self.settle_imprest_advance:
			self.imprest_amount = self.outstanding_amount
			self.outstanding_amount = 0.0

	def update_outstanding_amount(self):
			outstanding = flt(self.net_amount) + flt(self.gst_amount) - flt(self.tds_amount)-self.total_advance_allocated
			self.outstanding_amount = outstanding
			self.grand_total = outstanding

	def calculate_total_amount(self):

		self.total_amount = self.net_amount =  0
	
		total_allocated = self.calculate_allocated_amount()		
		deduction  = self.calculate_deductions()
		addition  = self.calculate_additions()

		
		for a in self.items:
			a.charge_amount = flt(flt(a.rate) * flt(a.qty))
			self.total_amount += flt(a.charge_amount)

		self.net_amount = flt(self.total_amount) - flt(deduction) + flt(addition)
		self.tds_amount = self.calculate_tds_amount(self.net_amount)
		# Calculate GST on net amount
		gst_amount = 0.0
		if self.gst_account and self.gst_amount:
			gst_amount = flt(self.gst_amount)
		
		# Calculate grand total: net amount + GST - TDS
		grand_total = flt(self.net_amount) + flt(gst_amount) - flt(self.tds_amount)

		

		# Set grand_total field (before advance allocation)
		self.grand_total = flt(grand_total)

	def calculate_tds_amount(self, amount):
		tds_amount = 0.0
		if self.tds_percent and self.tds_account:
			tds_amount = flt(self.tds_percent)/100 * flt(amount)
		return flt(tds_amount)
		
	def calculate_deductions(self):
		deduction = 0.0
		if self.deductions:
			for d in self.deductions:
				deduction += flt(d.amount)
		self.deduction_amount = flt(deduction)
		return deduction

	def calculate_additions(self):
		addition = 0.0
		if self.additions:
			for d in self.additions:
				addition += flt(d.amount)
		self.addition_amount = flt(addition)
		return addition

	def calculate_allocated_amount(self):
		allocated_amount = 0.0
		for adv in self.advances:
			allocated_amount += flt(adv.allocated_amount)
		self.total_advance_allocated = flt(allocated_amount)
		return allocated_amount
	
	def update_supplier_advance(self, cancel=False):
		if self.advances:
			query = """
				SELECT 
					name, 
					advance_type,
					advance_account, 
					advance_amount,
					adjusted_amount,
					balance_amount,
					advance_date
				FROM 
					`tabAdvance Item` 
				WHERE 
					advance_type = %s AND 
					parent = %s
			"""
			supplier_advances = frappe.db.sql(query, (self.advance_type, self.party), as_dict=True)

			if supplier_advances:
				allocated_amount = -1 * flt(self.total_advance_allocated) if cancel else flt(self.total_advance_allocated)
				
				adjusted_amount = flt(supplier_advances[0].adjusted_amount + allocated_amount)
				balance_amount = flt(supplier_advances[0].advance_amount - allocated_amount)

				frappe.db.sql(
					"""
					UPDATE
						`tabAdvance Item` 
					SET
						balance_amount = %s,
						adjusted_amount = %s
					WHERE 
						name = %s
					""",
					(balance_amount, adjusted_amount, supplier_advances[0].name),
				)

	def make_gl_entry(self):
		gl_entries = []

		if self.settle_imprest_advance:
			credit_account = frappe.db.get_value("Company", self.company, "imprest_advance_account")
			if not credit_account:
				frappe.throw(
					title="Missing Imprest Advance Account",
					msg="Please set the Imprest Advance Account in the company settings: {}".format(
						frappe.get_desk_link("Company", self.company)
					)
				)
		else:
			credit_account = frappe.db.get_value("Company", self.company, "default_payable_account")
			if not credit_account:
				frappe.throw(
					title="Missing Default Payable Account",
					msg="Please set the Default Payable Account in the company settings: {}".format(
						frappe.get_desk_link("Company", self.company)
					)
				)

		expense_account = frappe.db.get_value("Equipment Category", self.equipment_category, "r_m_expense_account")
		if not expense_account:
			expense_account = frappe.db.get_value("Company", self.company, "repair_and_service_expense_account")

		if not expense_account:
			frappe.throw(
				title="Missing Expense Account",
				msg="Please set up a Repair and Service Expense Account in the Equipment Category: {} or in the Company settings.".format(
					frappe.bold(self.equipment_category)
				)
			)

		gl_entries.append(
			self.get_gl_dict(
				{
					"account": expense_account,
					"debit": flt(self.total_amount),
					"debit_in_account_currency": flt(self.total_amount),
					"voucher_no": self.name,
					"voucher_type": self.doctype,
					"cost_center": self.cost_center,
				},
				self.currency,
			)
		)
		if self.additions:
				for d in self.additions:
					gl_entries.append(
						self.get_gl_dict(
							{
								"account": d.account,
								"party_type": self.party_type,
								"party": self.party,
								"debit": d.amount,
								"debit_in_account_currency": d.amount,
								"cost_center": self.cost_center,
							},
							self.currency,
						)
					)
					
		if self.gst_account and self.gst_amount > 0:
			gl_entries.append(
				self.get_gl_dict(
					{
						"account": self.gst_account,
						"debit": flt(self.gst_amount),
						"debit_in_account_currency": flt(self.gst_amount),
						"voucher_no": self.name,
						"voucher_type": self.doctype,
						"cost_center": self.cost_center,
					},
					self.currency,
				)
			)

		if self.advances:
			advance_account = frappe.get_value("Advance Type", self.advance_type, 'account')
			if not advance_account:
				frappe.throw(
					title="Missing Account in Advance Type",
					msg="Please set an account in the Advance Type: {}".format(
						frappe.bold(self.advance_type)
					)
				)
			
			gl_entries.append(
				self.get_gl_dict(
					{
						"account": advance_account,
						"party_type": self.party_type,
						"party": self.party,
						"credit": flt(self.total_advance_allocated),
						"credit_in_account_currency": flt(self.total_advance_allocated),
						"cost_center": self.cost_center,
						"voucher_no": self.name,
						"voucher_type": self.doctype,
					},
					self.currency,
				)
			)
		if self.outstanding_amount or self.imprest_amount:
			gl_entries.append(
				self.get_gl_dict(
					{
						"account": credit_account,
						"party_type": "Employee" if self.settle_imprest_advance else self.party_type,
						"party": self.imprest_party if self.settle_imprest_advance else self.party,
						"credit": flt(self.imprest_amount) if self.settle_imprest_advance else flt(self.outstanding_amount),
						"credit_in_account_currency": flt(self.imprest_amount) if self.settle_imprest_advance else flt(self.outstanding_amount),
						"cost_center": self.cost_center,
						"voucher_no": self.name,
						"voucher_type": self.doctype,
					},
					self.currency,
				))	

		if self.deductions:
			for d in self.deductions:
				gl_entries.append(
					self.get_gl_dict(
						{
							"account": d.account,
							"party_type": self.party_type,
							"party": self.party,
							"credit": d.amount,
							"credit_in_account_currency": d.amount,
							"cost_center": self.cost_center,
						},
						self.currency,
					)
				)
	
					
					
		if self.tds_account and self.tds_amount > 0:
			gl_entries.append(
				self.get_gl_dict(
					{
						"account": self.tds_account,
						"party_type": self.party_type,
						"party": self.party,
						"credit": self.tds_amount,
						"credit_in_account_currency": self.tds_amount,
						"cost_center": self.cost_center,
						"voucher_no": self.name,
						"voucher_type": self.doctype,
					},
					self.currency,
				)
			)
		
		payable_amount = flt(self.net_amount) + flt(self.gst_amount or 0) - flt(self.tds_amount)
		
		
		make_gl_entries(gl_entries, update_outstanding="No", cancel=(self.docstatus == 2), merge_entries=False)

	def make_filters(self):
		if not self.party or not self.advance_type:
			frappe.throw("Party and Advance Type filters are required.")
			
		filters = frappe._dict(
			party = self.party,
			advance_type = self.advance_type
		)
		return filters

	@frappe.whitelist()
	def fill_advance_details(self):
		filters = self.make_filters()
		advances = get_advance_list(filters=filters, as_dict=True)
		self.set("advances", [])

		if not advances:
			error_msg = _(
				"No advances found for the mentioned criteria:<br>Party: {0}"
			).format(
				frappe.bold(self.party),
			)
			if self.advance_type:
				error_msg += "<br>" + _("Advance Type: {0}").format(frappe.bold(self.advance_type))
			frappe.throw(error_msg, title=_("No advances found"))

		self.set("advances", advances)

def get_advance_list(
	filters,
	as_dict=True,
) -> list:
	Supplier = frappe.qb.DocType("Supplier")
	AdvanceItem = frappe.qb.DocType("Advance Item")

	query = (
		frappe.qb.from_(Supplier)
		.join(AdvanceItem)
		.on(Supplier.name == AdvanceItem.parent)
		.where(
			(Supplier.name == filters.party)
			& (AdvanceItem.advance_type == filters.advance_type)
			& (AdvanceItem.balance_amount > 0)
		)
		.select(
			AdvanceItem.balance_amount.as_("total_amount"),
			AdvanceItem.advance_type,
			AdvanceItem.balance_amount.as_("allocated_amount"),
			AdvanceItem.advance_account
		)
	)
	return query.run(as_dict=as_dict)


# permission query
def get_permission_query_conditions(user):
	if not user:
		user = frappe.session.user
	user_roles = frappe.get_roles(user)

	if user == "Administrator" or "System Manager" in user_roles:
		return

	return """(
		`tabRepair And Services Invoice`.owner = '{user}'
		or
		exists(select 1
			from `tabEmployee` as e
			where e.branch = `tabRepair And Services Invoice`.branch
			and e.user_id = '{user}')
		or
		exists(select 1
			from `tabEmployee` e, `tabAssign Branch` ab, `tabBranch Item` bi
			where e.user_id = '{user}'
			and ab.employee = e.name
			and bi.parent = ab.name
			and bi.branch = `tabRepair And Services Invoice`.branch)
	)""".format(
		user=user
	)