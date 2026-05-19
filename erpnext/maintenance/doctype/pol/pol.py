# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txtd

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import cstr, flt, fmt_money, formatdate, nowtime, getdate
from erpnext.accounts.utils import get_fiscal_year
from erpnext.custom_utils import check_future_date, get_branch_cc, prepare_gl, prepare_sl, check_budget_available
from erpnext.controllers.stock_controller import StockController
from erpnext.maintenance.maintenance_utils import get_without_fuel_hire, get_equipment_ba
from erpnext.accounts.doctype.business_activity.business_activity import get_default_ba
from frappe import _

class POL(StockController):
	def validate(self):
		check_future_date(self.posting_date)
		self.validate_data()
		self.validate_uom_is_integer("stock_uom", "qty")
		self.validate_item()
		self.calculate_amount()
		self.calculate_km_diff()
		if not self.direct_consumption:
			self.get_advance()
		

	def calculate_amount(self):
		total_amount = 0
		total_qty = 0
		for item in self.get("items"):
			if flt(item.qty) <= 0 or flt(item.rate) <= 0:
				frappe.throw("Quantity and Rate should be greater than 0 in row #{}".format(frappe.bold(item.idx)))
			item.amount = flt(item.qty, 2) * flt(item.rate, 2)
			total_amount += flt(item.amount, 2)
			total_qty += flt(item.qty, 2)

		self.total_amount = flt(total_amount, 2)
		self.outstanding_amount = flt(total_amount, 2)
		self.qty = total_qty

	def calculate_km_diff(self):
		previous_km_reading = frappe.db.sql("""
			SELECT 
				current_km_reading
			FROM `tabPOL` 
			WHERE 
				equipment = '{}'
			AND
				docstatus = 1
			ORDER BY 
				posting_date DESC,
				posting_time DESC
			limit 1;
		""".format(self.equipment),as_dict=True)

		pv_km = 0
		if previous_km_reading:
			pv_km = flt(previous_km_reading[0].current_km_reading)
		else:
			pv_km = frappe.db.get_value("Equipment", self.equipment, "initial_km_reading")
			if not pv_km:
				frappe.throw("Please set initial km reading in equimpment {}".format(frappe.get_desk_link("Equipment", self.equipment)))
		
		if flt(pv_km) >= flt(self.current_km_reading):
			frappe.throw("Current KM Reading cannot be less than Previous KM Reading<b>({})</b> for Vehicle Number <b>{}</b>".format(pv_km,self.equipment_number))
		self.km_difference = flt(self.current_km_reading) - flt(pv_km)
		self.mileage = flt(self.km_difference) / self.qty

	def before_submit(self):
		if not self.direct_consumption:
			self.paid_amount = self.outstanding_amount
			self.outstanding_amount = 0
		
	def on_submit(self):
		self.validate_data()
		self.update_advance()
		self.make_pol_entry()
		if self.direct_consumption:
			self.post_journal_entry()

	def on_cancel(self):
		self.delete_pol_entry()
		self.update_advance()

	def validate_data(self):
		for i in self.items:
			if i.uom != self.stock_uom:
				frappe.throw("Row #{}'s uom must be in {}".format(
					frappe.bold(i.idx),
					frappe.bold(self.stock_uom)
				))

		if not self.equipment_branch:
			frappe.throw("Fuelbook and Equipment Branch are mandatory")

		if not self.equipment_category:
			frappe.throw("Equipment Category Missing")

		if self.book_type == "Own":
			if self.fuelbook != frappe.db.get_value("Equipment", self.equipment, "fuelbook"):
				frappe.throw("Fuelbook (<b>" + str(self.fuelbook) + "</b>) is not registered to <b>" + str(self.equipment) + "</b>")

	def validate_item(self):
		is_stock, is_pol = frappe.db.get_value("Item", self.pol_type, ["is_stock_item", "is_pol_item"])
		if not is_stock:
			frappe.throw(str(self.item_name) + " is not a stock item")

		if not is_pol:
			frappe.throw(str(self.item_name) + " is not a POL item")

	def post_journal_entry(self):
		veh_cat = frappe.db.get_value("Equipment", self.equipment, "equipment_category")
		if veh_cat:
			if veh_cat == "Pool Vehicle":
				pol_account = frappe.db.get_single_value("Maintenance Accounts Settings", "pool_vehicle_pol_expenses")
			else:
				pol_account = frappe.db.get_single_value("Maintenance Accounts Settings", "default_pol_expense_account")
		else:
			frappe.throw("Can not determine machine category")

		expense_bank_account = frappe.db.get_value("Company", self.company, "default_payable_account")

		if not expense_bank_account:
			frappe.throw("No Default Payable Account set in Company")
		
		if expense_bank_account and pol_account:
			je = frappe.new_doc("Journal Entry")
			je.flags.ignore_permissions = 1 
			je.title = "POL (" + self.pol_type + " for " + self.equipment_number + ")"
			je.voucher_type = 'Bank Entry'
			je.naming_series = 'Bank Payment Voucher'
			je.remark = 'Payment against : ' + self.name;
			je.posting_date = self.posting_date
			je.branch = self.branch
			je.company = self.company,
			je.mode_of_payment = 'ePayment',

			je.append("accounts", {
					"account": pol_account,
					"cost_center": self.cost_center,
					"reference_type": "POL",
					"reference_name": self.name,
					# "party_type": "Supplier",
					# "party": self.supplier,
					"debit_in_account_currency": flt(self.total_amount),
					"debit": flt(self.total_amount),
					"business_activity": self.business_activity,
				})

			je.append("accounts", {
					"account": expense_bank_account,
					"cost_center": self.cost_center,
					"party_type": "Supplier",
					"party": self.supplier,
					"credit_in_account_currency": flt(self.total_amount),
					"credit": flt(self.total_amount),
					"business_activity": self.business_activity
				})

			je.insert()
			self.db_set("jv", je.name)
			frappe.msgprint(_('Journal Entry {} posted to accounts').format(frappe.get_desk_link(je.doctype,je.name)))

		else:
			frappe.throw("Define POL expense account in Maintenance Setting or Expense Bank in Branch")
		
	def make_pol_entry(self):
		if getdate(self.posting_date) <= getdate("2018-03-31"):
			return

		container = frappe.db.get_value("Equipment Type", frappe.db.get_value("Equipment", self.equipment, "equipment_type"), "is_container")
		if self.book_type == "Own":
			own = 1
		else:
			own = 0

		con = frappe.new_doc("POL Entry")
		con.flags.ignore_permissions = 1	
		con.equipment = self.equipment
		con.pol_type = self.pol_type
		con.branch = self.equipment_branch
		con.date = self.posting_date
		con.posting_time = self.posting_time
		con.qty = self.qty
		con.company = self.company
		con.reference_type = "POL"
		con.reference_name = self.name
		con.is_opening = 0
		con.own_cost_center = own
		if container:
			con.type = "Stock"
			con.submit()
		
		if self.direct_consumption:
			con1 = frappe.new_doc("POL Entry")
			con1.flags.ignore_permissions = 1	
			con1.company = self.company
			con1.equipment = self.equipment
			con1.pol_type = self.pol_type
			con1.branch = self.equipment_branch
			con1.date = self.posting_date
			con1.posting_time = self.posting_time
			con1.qty = self.qty
			con1.reference_type = "POL"
			con1.reference_name = self.name
			con1.type = "Receive"
			con1.is_opening = 0
			con1.own_cost_center = own
			con1.submit()
			
			if container:
				con2 = frappe.new_doc("POL Entry")
				con2.flags.ignore_permissions = 1	
				con2.company = self.company
				con2.equipment = self.equipment
				con2.pol_type = self.pol_type
				con2.branch = self.equipment_branch
				con2.date = self.posting_date
				con2.posting_time = self.posting_time
				con2.qty = self.qty
				con2.reference_type = "POL"
				con2.reference_name = self.name
				con2.type = "Issue"
				con2.is_opening = 0
				con2.own_cost_center = own
				con2.submit()

	def delete_pol_entry(self):
		frappe.db.sql("delete from `tabPOL Entry` where reference_name = %s", self.name)

	def update_advance(self):
		if self.docstatus == 2 :
			for item in self.advances:
				doc = frappe.get_doc("Pol Advance", {'name':item.reference,'equipment_number':self.equipment_number})
				doc.balance_amount  = flt(doc.balance_amount) + flt(item.allocated_amount)
				doc.adjusted_amount = flt(doc.adjusted_amount) - flt(item.allocated_amount)
				if item.has_od:
					doc.od_amount = flt(doc.od_amount) - flt(self.od_amount) 
					doc.od_outstanding_amount = flt(doc.od_outstanding_amount) - flt(self.od_amount)
				doc.save(ignore_permissions=True)
			return
		for item in self.advances:
			doc = frappe.get_doc("Pol Advance", {'name':item.reference,'equipment_number':self.equipment_number})
			doc.balance_amount  = flt(item.advance_balance) - flt(item.allocated_amount)
			doc.adjusted_amount = flt(doc.adjusted_amount) + flt(item.allocated_amount)
			if item.has_od:
				doc.od_amount = flt(doc.od_amount) + flt(self.od_amount)
				doc.od_outstanding_amount = flt(doc.od_outstanding_amount) + flt(self.od_amount)
			doc.save(ignore_permissions=True)

	@frappe.whitelist()
	def get_advance(self):
		# self.calculate_km_diff()
		data = []
		data = frappe.db.sql("""
				SELECT 
					a.name, 
					a.amount,
					a.balance_amount, 
					a.journal_entry
				FROM `tabPol Advance` a
				WHERE 
					a.docstatus = 1 
					AND a.fuelbook = '{}'
					AND a.balance_amount > 0
					AND a.equipment_number = '{}'
					AND a.company = '{}'
				ORDER BY a.entry_date
			""".format(self.fuelbook, self.equipment_number, self.company), as_dict=True)
		self.set('advances', [])

		allocated_amount = self.total_amount
		total_amount_adjusted = 0

		if not data:
			frappe.throw("No POL Advance")

		temp_balance = 0
		for d in data:
			is_submitted = False

			if d.journal_entry:
				doc = frappe.get_doc('Journal Entry', d.journal_entry)
				if doc.docstatus == 1:
					is_submitted = True
			else:
				is_submitted = True

			if is_submitted:
				row = self.append('advances',{})
				row.reference         = d.name
				row.advance_amount    = d.amount 
				row.advance_balance      = d.balance_amount
				if row.advance_balance >= allocated_amount:
					row.allocated_amount = allocated_amount
					row.amount = allocated_amount
					total_amount_adjusted += flt(row.allocated_amount)
					allocated_amount = 0
				elif row.advance_balance < allocated_amount:
					row.allocated_amount = row.advance_balance
					row.amount = allocated_amount
					total_amount_adjusted += flt(row.allocated_amount)
					allocated_amount = flt(allocated_amount) - flt(row.advance_balance)
					if temp_balance < 0:
						row.amount = -(temp_balance)
				row.balance = flt(row.advance_balance) - flt(row.amount) #jai
				temp_balance = row.balance

		if not self.advances:
			frappe.throw("NO POL Advance")

		if total_amount_adjusted < flt(self.total_amount):
			self.od_amount = flt(self.total_amount) - total_amount_adjusted 
			self.advances[len(self.advances)-1].has_od = 1
		else:
			self.od_amount = 0