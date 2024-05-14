# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt
import frappe
from frappe.model.document import Document
from frappe import _, qb, throw, msgprint
from erpnext.custom_utils import check_future_date
from erpnext.controllers.accounts_controller import AccountsController
from pypika import Case, functions as fn
from frappe.utils import flt, cint, money_in_words
from erpnext.accounts.utils import get_tds_account,get_account_type
from erpnext.accounts.general_ledger import (
	get_round_off_account_and_cost_center,
	make_gl_entries,
	make_reverse_gl_entries,
	merge_similar_entries,
)
import operator, math
from erpnext.accounts.party import get_party_account

class TransporterInvoice(AccountsController):
	def validate(self):
		check_future_date(self.posting_date)
		self.validate_dates()
		self.calculate_total()
		self.set_status()

	def on_submit(self):
		self.make_gl_entries()

	def on_cancel(self):
		self.ignore_linked_doctypes = ("GL Entry", "Stock Ledger Entry", "Payment Ledger Entry")
		self.make_gl_entries()

	def before_cancel(self):
		if self.journal_entry and frappe.db.exists("Journal Entry",self.journal_entry):
			doc = frappe.get_doc("Journal Entry", self.journal_entry)
			if doc.docstatus != 2:
				frappe.throw("Journal Entry exists for this transaction {}".format(frappe.get_desk_link("Journal Entry",self.journal_entry)))
			
	def validate_dates(self):
		if self.from_date > self.to_date:
			msgprint("From Date cannot be grater than To Date",title="Invalid Dates", raise_exception=True)
		if not self.remarks:
			self.remarks = "Payment for {0}".format(self.equipment)
		
	def set_status(self, update=False, status=None, update_modified=True):
		if self.is_new():
			self.status = "Draft"
			return

		outstanding_amount = flt(self.outstanding_amount,2)
		if not status:
			if self.docstatus == 2:
				status = "Cancelled"
			elif self.docstatus == 1:
				if outstanding_amount > 0 and flt(self.amount_payable) > outstanding_amount:
					self.status = "Partly Paid"
				elif outstanding_amount > 0 :
					self.status = "Unpaid"
				elif outstanding_amount <= 0:
					self.status = "Paid"
				else:
					self.status = "Submitted"
			else:
				self.status = "Draft"

		if update:
			self.db_set("status", self.status, update_modified=update_modified)

	def make_gl_entries(self):
		gl_entries = []
		self.make_supplier_gl_entry(gl_entries)
		self.make_item_gl_entries(gl_entries)
		self.unloading_gl_entries(gl_entries)
		self.deduction_gl_entries(gl_entries)
		self.make_pol_gl_entry(gl_entries)
		gl_entries = merge_similar_entries(gl_entries)
		make_gl_entries(gl_entries,update_outstanding="No",cancel=self.docstatus == 2)
		
	def make_supplier_gl_entry(self, gl_entries):
		if flt(self.amount_payable) > 0:
			# Did not use base_grand_total to book rounding loss gle
			gl_entries.append(
				self.get_gl_dict({
					"account": self.credit_account,
					"credit": flt(self.amount_payable,2),
					"credit_in_account_currency": flt(self.amount_payable,2),
					"against_voucher": self.name,
					"party_type": "Supplier",
					"party": self.supplier,
					"against_voucher_type": self.doctype,
					"cost_center": self.cost_center,
					"voucher_type":self.doctype,
					"voucher_no":self.name
				}, self.currency))

	def make_item_gl_entries(self, gl_entries):
		for d in self.items:
			gl_entries.append(
				self.get_gl_dict({
						"account":  d.expense_account,
						"debit": flt(d.transportation_amount,2),
						"debit_in_account_currency": flt(d.transportation_amount,2),
						"against_voucher": self.name,
						"against_voucher_type": self.doctype,
						"party_type": "Supplier",
						"party": self.supplier,
						"cost_center": self.cost_center,
						"voucher_type":self.doctype,
						"voucher_no":self.name
				}, self.currency)
			)
	def make_pol_gl_entry(self, gl_entries):
		expense_account = frappe.db.get_value("Company", self.company,'pol_expense_account')
		gl_entries.append(
			self.get_gl_dict({
				"account":  expense_account,
				"credit": flt(self.pol_amount,2),
				"credit_in_account_currency": flt(self.pol_amount,2),
				"against_voucher": self.name,
				"against_voucher_type": self.doctype,
				"party_type": "Supplier",
				"party": self.supplier,
				"cost_center": self.cost_center,
				"voucher_type":self.doctype,
				"voucher_no":self.name
			}, self.currency)
		)

	def unloading_gl_entries(self,gl_entries):
		if flt(self.unloading_amount):
			party = party_type = None
			account_type = get_account_type("Account", self.unloading_account)
			if account_type == "Receivable" or account_type == "Payable":
				party = self.supplier
				party_type = "Supplier"

			gl_entries.append(
				self.get_gl_dict({
					"account":  self.unloading_account,
					"debit": flt(self.unloading_amount,2),
					"debit_in_account_currency": flt(self.unloading_amount,2),
					"against_voucher": self.name,
					"against_voucher_type": self.doctype,
					"party_type": party_type,
					"party": party,
					"cost_center": self.cost_center,
					"reference_no": self.cheque_no,
					"reference_date": self.cheque_date,
					"equipment_number": self.registration_no
				}, self.currency)
			)
	def deduction_gl_entries(self,gl_entries):
		for d in self.deductions:
			gl_entries.append(
				self.get_gl_dict({
					"account":  d.account,
					"credit": flt(d.amount,2),
					"credit_in_account_currency": flt(d.amount,2),
					"against_voucher": self.name,
					"against_voucher_type": self.doctype,
					"party_type": "Supplier",
					"party": self.supplier,
					"cost_center": self.cost_center,
					"voucher_type":self.doctype,
					"voucher_no":self.name
				}, self.currency)
			)

	@frappe.whitelist()
	def get_payment_details(self):
		self.set('items', [])
		self.set('pols', [])
		# get stock enteris 
		stock_transfer = self.get_stock_entries()
		# get delivery note
		delivery_note = self.get_delivery_notes() 
		# get trip log data
		within_warehouse_trips = self.get_trip_log()

		# get Trips from production location based
		production_location = self.get_production_transportation("Location")
		# get Trips from production warehouse based
		production_warehouse = self.get_production_transportation("Warehouse")
		entries = stock_transfer + delivery_note + production_warehouse
		if not entries and not within_warehouse_trips and not production_location:
			msgprint("No Transportation Detail(s) for Equipment <b>{0} </b> ".format(self.equipment), raise_exception= True)
		self.total_trip = len(entries)
		trans_amount    = unload_amount = pol_amount = 0

		# populate items
		for d in entries:
			if d.transporter_rate_ref:
				d.transportation_rate 	= d.rate
				d.unloading_amount 		= 0
				d.transporter_rate 		= d.transporter_rate_reference
			else:
				tr = get_transporter_rate(d.from_warehouse, d.receiving_warehouse, d.posting_date, self.equipment_category, d.item_code)
				d.transporter_rate_ref = tr.name

				if cint(self.total_trip) > flt(tr.threshold_trip):
					d.transportation_rate = flt(tr.higher_rate)
				else:
					d.transportation_rate = flt(tr.lower_rate)

				d.unloading_rate  = tr.unloading_rate
				if d.unloading_by == "Transporter":
					d.unloading_amount = round(flt(d.unloading_rate) * flt(d.qty), 2)
				else:
					d.unloading_amount = 0
				d.expense_account 	= tr.expense_account
				
			d.transportation_amount = round(flt(d.transportation_rate) * flt(d.qty), 2)
			d.total_amount 		= flt(d.unloading_amount) + flt(d.transportation_amount)
			trans_amount 		+= flt(d.transportation_amount)
			unload_amount 		+= flt(d.unloading_amount)
			row = self.append('items', {})
			row.update(d)

		# populate items from Transporter Trips Log
		for d in within_warehouse_trips:
			d.total_amount 		= flt(d.transportation_amount)
			trans_amount 		+= flt(d.transportation_amount)
			row 				= self.append('items', {})
			row.update(d)
		
		# populate items from Production 
		for d in production_location:
			d.total_amount 	= flt(d.transportation_amount)
			trans_amount 	+= flt(d.transportation_amount)
			row = self.append('items', {})
			row.update(d)

		#POL Details
		for a in frappe.db.sql("""select posting_date, name as pol_receive, pol_type as item_code, 
										item_name, qty, rate, total_amount as amount, 
										total_amount as allocated_amount,
										fuelbook_branch, 'POL Receive' as reference_type, name as reference
									from `tabPOL Receive`  p
									where docstatus = 1 
									and posting_date between '{}' and '{}' and equipment = '{}'
									and NOT EXISTS(select 1 from `tabTransporter Invoice` ti inner join `tabTransporter Invoice Pol` tip 
											on ti.name = tip.parent 
											where ti.docstatus != 2 and ti.name != '{}'
											and reference_type = 'POL Receive' and reference = p.name)
									""".format(self.from_date, self.to_date, self.equipment,self.name), as_dict=1):
			row = self.append('pols', {})
			row.update(a)
		self.calculate_total()

	@frappe.whitelist()
	def post_journal_entry(self):
		if self.journal_entry and frappe.db.exists("Journal Entry",{"name":self.journal_entry,"docstatus":("!=",2)}):
			frappe.msgprint(_("Journal Entry Already Exists {}".format(frappe.get_desk_link("Journal Entry",self.journal_entry))))
		if not self.amount_payable:
			frappe.throw(_("Payable Amount should be greater than zero"))
			
		# default_ba = get_default_ba()

		credit_account = self.credit_account
	
		if not credit_account:
			frappe.throw("Expense Account is mandatory")
		r = []
		if self.remarks:
			r.append(_("Note: {0}").format(self.remarks))

		remarks = ("").join(r) #User Remarks is not mandatory
		bank_account = frappe.db.get_value("Branch",self.branch, "expense_bank_account")
		if not bank_account:
			frappe.throw(_("Default bank account is not set in company {}".format(frappe.bold(self.company))))
		# Posting Journal Entry
		je = frappe.new_doc("Journal Entry")
		je.flags.ignore_permissions=1
		je.update({
			"doctype": "Journal Entry",
			"voucher_type": "Bank Entry",
			"naming_series": "Bank Payment Voucher",
			"title": "Transporter Payment "+ self.supplier,
			"user_remark": "Note: " + "Transporter Payment - " + self.supplier,
			"posting_date": self.posting_date,
			"company": self.company,
			"total_amount_in_words": money_in_words(self.amount_payable),
			"branch": self.branch,
			"reference_type":self.doctype,
			"referece_doctype":self.name
		})
		je.append("accounts",{
			"account": credit_account,
			"debit_in_account_currency": self.amount_payable,
			"cost_center": self.cost_center,
			"party_check": 1,
			"party_type": "Supplier",
			"party": self.supplier,
			"reference_type": self.doctype,
			"reference_name": self.name
		})
		je.append("accounts",{
			"account": bank_account,
			"credit_in_account_currency": self.amount_payable,
			"cost_center": self.cost_center
		})

		je.insert()
		#Set a reference to the claim journal entry
		self.db_set("journal_entry",je.name)
		frappe.msgprint(_('Journal Entry {0} posted to accounts').format(frappe.get_desk_link("Journal Entry",je.name)))
	
	@frappe.whitelist()
	def calculate_total(self):
		if not self.credit_account:
			self.credit_account = get_party_account("Supplier",self.supplier,self.company)
		# transfer and delivery charges
		transfer_charges = 0
		delivery_charges = 0
		total_transporter_amount = 0
		unloading_amount = 0
		trip_log_charges = 0
		within_trip_count = 0
		production_transport_charges = 0
		production_trip_count = 0
		for i in self.items:
			if i.reference_type == 'Stock Entry':
				transfer_charges += flt(i.transportation_amount)

			if i.reference_type == 'Delivery Note':
				delivery_charges += flt(i.transportation_amount)

			if i.reference_type == 'Trip Log':
				trip_log_charges += flt(i.transportation_amount)
				within_trip_count += 1

			if i.reference_type == 'Production':
				production_transport_charges += flt(i.transportation_amount)
				production_trip_count += 1
				
			total_transporter_amount += flt(i.transportation_amount)
			unloading_amount += flt(i.unloading_amount)
			
		self.transfer_charges 	= flt(transfer_charges,2)
		self.delivery_charges  	= flt(delivery_charges,2)
		self.transportation_amount = flt(total_transporter_amount,2)
		self.within_warehouse_trip = within_trip_count
		self.production_trip_count = production_trip_count
		self.within_warehouse_amount = flt(trip_log_charges,2)
		self.unloading_amount 	= flt(unloading_amount,2)
		self.production_transport_amount = flt(production_transport_charges,2)
		self.gross_amount 	= flt(self.transportation_amount + self.unloading_amount,2)

		# pol
		pol_amount = 0
		for j in self.pols:
			if not flt(j.allocated_amount):
				j.allocated_amount = flt(j.amount,2)
			pol_amount += flt(j.allocated_amount,2)

		self.pol_amount  	= flt(pol_amount,2)

		# unloading
		if self.unloading_amount:
			self.unloading_account = frappe.db.get_value("Company", self.company, "default_unloading_account")
			if not self.unloading_account:
				msgprint(_("GL for {} is not set under {}")\
					.format(frappe.bold("Default Unloading Account"), frappe.bold("Company's Production Account Settings")), raise_exception=True)

		self.tds_amount = self.security_deposit_amount = self.weighbridge_amount = self.clearing_amount = other_deductions = 0
		for d in self.get("deductions"):
			# tds and security deposite
			if d.deduction_type in ["Security Deposit","TDS Deduction"]:
				if d.deduction_type == "TDS Deduction":
					if flt(d.percent) < 1:
						msgprint("Deduction Percent is required at row {} for deduction type {}".format(bold(d.idx),bold(d.deduction_type)), raise_exception=True)
					d.amount = flt(self.gross_amount) * flt(d.percent) / 100
					self.tds_amount += flt(d.amount)
					d.account = get_tds_account(d.percent, self.company)
					if not d.account:
						msgprint(_("GL for {} is not set under {}")\
						.format(frappe.bold("TDS Account"), frappe.bold("Company's Accounts Settings")), raise_exception=True)
				elif d.deduction_type == "Security Deposit":
					if flt(d.percent) > 0:
						d.amount = flt(self.gross_amount) * flt(d.percent) / 100
					else:
						d.amount = d.charge_amount
					d.account = frappe.db.get_value("Company", self.company, "security_deposit_account")
					self.security_deposit_amount += flt(d.amount)
					if not d.account:
						msgprint(_("GL for {} is not set under {}")\
							.format(frappe.bold("Security Deposit Received"), frappe.bold("Company's Accounts Settings")),raise_exception=True)
							
			elif d.deduction_type in ["Weighbridge Charge/Trip","Clearing Charge/Trip"]:
				d.amount = flt(self.total_trip) * flt(d.charge_amount)
				if d.deduction_type == "Weighbridge Charge/Trip":
					d.account = frappe.db.get_value("Company", self.company, "weighbridge_account")
					self.weighbridge_amount += flt(d.amount)
					if not d.account:
						msgprint(_("GL for {} is not set under {}")\
						.format(frappe.bold("Income from Weighbridge Account"), frappe.bold("Company's Accounts Settings")), raise_exception=True)
				elif d.deduction_type == "Clearing Charge/Trip":
					d.account = frappe.db.get_value("Company", self.company, "clearing_account")
					self.clearing_amount += flt(d.amount)
					if not d.account:
						msgprint(_("GL for {} is not set under {}")\
							.format(frappe.bold("Income from Clearing Account"), frappe.bold("Company's Accounts Settings")), raise_exception=True)
			else:
				other_deductions += flt(d.amount)
		self.total_trip = len(self.get("items"))
		self.other_deductions 	= flt(other_deductions + self.tds_amount + self.security_deposit_amount + self.weighbridge_amount + self.clearing_amount,2)	
		self.net_payable 		= flt(self.gross_amount - self.pol_amount - self.other_deductions,2)
		self.amount_payable 	= self.outstanding_amount 	= flt(self.net_payable,2)		
		self.grand_total 		= flt(self.gross_amount,2)

	def get_production_transportation(self, rate_base_on):
		return frappe.db.sql("""
					select
						b.name as reference_row,
						a.posting_date,
						'Production' as reference_type,
						a.name as reference_name,
						b.item_code,
						b.item_name,
						b.rate as transportation_rate,
						b.amount as transportation_amount,
						b.qty,
						b.unloading_by,
						b.equipment,
						a.warehouse as from_warehouse,
						if(a.transfer = 1, a.to_warehouse, a.warehouse) as receiving_warehouse,
						b.equipment,
						b.transporter_rate as transporter_rate_ref,
						b.transportation_expense_account as expense_account 
						from
						`tabProduction` a inner join `tabProduction Product Item` b 
						on a.name = b.parent
					where a.docstatus = 1 
						and a.posting_date between "{0}" and "{1}" 
						and b.equipment = "{2}" 
						and a.cost_center = '{3}' 
						and b.transporter_payment_eligible = 1 
						and a.transporter_rate_base_on = '{4}' 
						and NOT EXISTS
						(
							select 1 
							from `tabTransporter Invoice` p, `tabTransporter Invoice Item` i
							where p.name = i.parent 
							and i.reference_name = a.name
							and p.docstatus != 2
							and p.name != '{5}'
							and p.equipment = '{2}'
						)""".format(self.from_date, self.to_date, self.equipment, self.cost_center, rate_base_on, self.name), as_dict = True)

	def get_delivery_notes(self):
		return frappe.db.sql("""
				SELECT b.name as reference_row, a.posting_date, 
					'Delivery Note' as reference_type, a.name as reference_name, 
					b.item_code, b.item_name, 
					b.warehouse as from_warehouse, a.customer as receiving_warehouse, 
					b.qty as qty, '' as unloading_by, b.equipment,
					b.transporter_rate as rate, b.transporter_rate_ref,
					b.transporter_rate_expense_account as expense_account
				FROM `tabDelivery Note` a INNER JOIN `tabDelivery Note Item` b 
				ON b.parent = a.name
				WHERE a.docstatus = 1 AND a.posting_date BETWEEN "{0}" and "{1}" 
				AND b.equipment = "{2}" AND b.cost_center = "{3}" 
				AND b.others_equipment = 0
				AND a.is_return = 0
				AND NOT EXISTS(
					select 1 
					from `tabTransporter Invoice` p, `tabTransporter Invoice Item` i
					where p.name = i.parent 
					and i.reference_name = a.name
					and p.docstatus != 2
					and p.name != '{4}'
					and p.equipment = '{2}'
				)
				""".format(self.from_date, self.to_date, self.equipment, self.cost_center,self.name), as_dict = True)

	def get_stock_entries(self):
		return frappe.db.sql("""
			SELECT
				b.name as reference_row, a.posting_date, 
				'Stock Entry' as reference_type, a.name as reference_name, 
				b.item_code, b.item_name,b.s_warehouse as from_warehouse, 
				b.t_warehouse as receiving_warehouse, b.received_qty as qty, b.equipment,
				b.unloading_by
				FROM `tabStock Entry` a INNER JOIN `tabStock Entry Detail` b ON b.parent = a.name 
				WHERE a.docstatus = 1  
				AND a.stock_entry_type = 'Material Transfer' 
				AND a.posting_date between "{0}" and "{1}" 
				AND b.equipment = "{2}"
				AND b.cost_center = "{3}"
				AND NOT EXISTS(
					select 1 
					from `tabTransporter Invoice` p, `tabTransporter Invoice Item` i
					where p.name = i.parent 
					and p.docstatus != 2 
					and p.name != '{4}'
					and i.reference_name = a.name
					and p.equipment = '{2}'
				)
				""".format(self.from_date, self.to_date, self.equipment, self.cost_center,self.name), as_dict = True)

	def get_trip_log(self):
		return frappe.db.sql("""select b.name as reference_row, a.posting_date, 
					'Trip Log' as reference_type, a.name as reference_name, 
					b.item_code as item_code, b.item_name, b.amount as transportation_amount,
					a.warehouse as from_warehouse, a.warehouse as receiving_warehouse, 
					b.qty as qty, b.equipment, b.transporter_rate as transporter_rate_ref, 
					b.rate as transportation_rate, b.expense_account
				from `tabTrip Log` a, `tabTrip Log Item` b
				where a.name = b.parent 
				and a.docstatus = 1 
				and a.posting_date between "{0}" and "{1}" 
				and b.equipment = "{2}" 
				and a.cost_center = "{3}"
				and b.eligible_for_transporter_payment = 1
				and NOT EXISTS(
					select 1 
					from `tabTransporter Invoice` p, `tabTransporter Invoice Item` i
					where p.name = i.parent 
					and p.docstatus != 2
					and i.reference_row = b.name
					and p.name != '{4}'
					and p.equipment = '{2}')
				""".format(self.from_date, self.to_date, self.equipment, self.cost_center, self.name), as_dict = True)
# query permission
def get_permission_query_conditions(user):
	if not user: user = frappe.session.user
	user_roles = frappe.get_roles(user)

	if user == "Administrator" or "System Manager" in user_roles: 
		return

	return """(
		`tabTransporter Invoice`.owner = '{user}'
		or
		exists(select 1
			from `tabEmployee` as e
			where e.branch = `tabTransporter Invoice`.branch
			and e.user_id = '{user}')
		or
		exists(select 1
			from `tabEmployee` e, `tabAssign Branch` ab, `tabBranch Item` bi
			where e.user_id = '{user}'
			and ab.employee = e.name
			and bi.parent = ab.name
			and bi.branch = `tabTransporter Invoice`.branch)
	)""".format(user=user)