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
		self.check_on_dry_hire()
		# self.validate_warehouse()
		self.validate_data()
		self.validate_posting_time()
		self.validate_uom_is_integer("stock_uom", "qty")
		self.validate_item()
		self.calculate_km_diff()
		self.populate_child_table()
		self.calculate_amount()

	def calculate_amount(self):
		if self.qty and self.rate:
			amount = self.qty*self.rate
			self.amount = flt(amount)

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
		if flt(pv_km) >= flt(self.current_km_reading):
			frappe.throw("Current KM Reading cannot be less than Previous KM Reading<b>({})</b> for Vehicle Number <b>{}</b>".format(pv_km,self.equipment_number))
		self.km_difference = flt(self.current_km_reading) - flt(pv_km)
		self.mileage = flt(self.km_difference) / self.qty

	def before_submit(self):
		self.paid_amount = self.outstanding_amount
		self.outstanding_amount = 0
		
	def on_submit(self):
		self.validate_data()
		self.check_on_dry_hire()
		if not self.direct_consumption:
			self.update_stock_ledger()
		self.update_advance()
		self.make_pol_entry()
		if self.settled_using_imprest:
			self.make_gl_entry()

	def on_cancel(self):
		self.update_stock_ledger()
		docstatus = frappe.db.get_value("Journal Entry", self.jv, "docstatus")
		if docstatus and docstatus != 2:
			frappe.throw("Cancel the Journal Entry " + str(self.jv) + " and proceed.")

		self.db_set("jv", "")
		# self.cancel_budget_entry()
		self.delete_pol_entry()
		self.update_advance()
		if self.settled_using_imprest:
			self.make_gl_entry()

	def validate_warehouse(self):
		self.validate_warehouse_branch(self.warehouse, self.branch)
		self.validate_warehouse_branch(self.equipment_warehouse, self.equipment_branch)
		if self.hiring_branch:
			self.validate_warehouse_branch(self.hiring_warehouse, self.hiring_branch)

	def check_on_dry_hire(self):
		# record = get_without_fuel_hire(self.equipment, self.posting_date, self.posting_time)
		# if record:
		# 	data = record[0]
		# 	self.hiring_cost_center = data.cc
		# 	self.hiring_branch =  data.br
		# else:
		self.hiring_cost_center = None
		self.hiring_branch =  None
		self.hiring_warehouse = None

	def validate_data(self):
		if not self.fuelbook_branch or not self.equipment_branch:
			frappe.throw("Fuelbook and Equipment Branch are mandatory")

		if flt(self.qty) <= 0 or flt(self.rate) <= 0:
			frappe.throw("Quantity and Rate should be greater than 0")

		if not self.warehouse:
			frappe.throw("Warehouse is Mandatory. Set the Warehouse in Cost Center")

		if not self.equipment_category:
			frappe.throw("Equipment Category Missing")

		if self.book_type == "Own":
			if self.fuelbook != frappe.db.get_value("Equipment", self.equipment, "fuelbook"):
				frappe.throw("Fuelbook (<b>" + str(self.fuelbook) + "</b>) is not registered to <b>" + str(self.equipment) + "</b>")

	def validate_item(self):
		is_stock, is_hsd, is_pol = frappe.db.get_value("Item", self.pol_type, ["is_stock_item", "is_hsd_item", "is_pol_item"])
		if not is_stock:
			frappe.throw(str(self.item_name) + " is not a stock item")

		if not is_hsd and not is_pol:
			frappe.throw(str(self.item_name) + " is not a HSD/POL item")
	
	def check_budget(self):
		if self.hiring_cost_center:
			cc = self.hiring_cost_center
		else:
			cc = get_branch_cc(self.equipment_branch)
		account = frappe.db.get_value("Equipment Category", self.equipment_category, "budget_account")
		if not self.is_hsd_item:
			account = frappe.db.get_value("Item", self.pol_type, "expense_account")
		
		check_budget_available(cc, account, self.posting_date, self.total_amount, self.business_activity)
		self.consume_budget(cc, account)

	def consume_budget(self, cc, account):
		bud_obj = frappe.get_doc({
			"doctype": "Committed Budget",
			"account": account,
			"cost_center": cc,
			"po_no": self.name,
			"po_date": self.posting_date,
			"amount": self.total_amount,
			"item_code": self.pol_type,
			"poi_name": self.name,
			"business_activity": self.business_activity,
			"date": frappe.utils.nowdate()
			})
		bud_obj.flags.ignore_permissions = 1
		bud_obj.submit()

		consume = frappe.get_doc({
			"doctype": "Consumed Budget",
			"account": account,
			"cost_center": cc,
			"po_no": self.name,
			"po_date": self.posting_date,
			"amount": self.total_amount,
			"pii_name": self.name,
			"item_code": self.pol_type,
			"com_ref": bud_obj.name,
			"business_activity": self.business_activity,
			"date": frappe.utils.nowdate()})
		consume.flags.ignore_permissions=1
		consume.submit()

	def update_stock_ledger(self):
		if self.hiring_warehouse:
			wh = self.hiring_warehouse
		else:
			wh = self.equipment_warehouse

		sl_entries = []
		sl_entries.append(prepare_sl(self, 
			{
				"actual_qty": flt(self.qty), 
				"warehouse": wh, 
				"incoming_rate": round(flt(self.total_amount) / flt(self.qty) , 2)
			}))

		if self.docstatus == 2:
			sl_entries.reverse()

		self.make_sl_entries(sl_entries, self.amended_from and 'Yes' or 'No')

	def get_gl_entries(self, warehouse_account):
		gl_entries = []
		
		creditor_account = frappe.db.get_value("Company", self.company, "default_payable_account")
		if not creditor_account:
			frappe.throw("Set Default Payable Account in Company")

		expense_account = self.get_expense_account()

		if self.hiring_cost_center:
			cost_center = self.hiring_cost_center
		else:
			cost_center = get_branch_cc(self.equipment_branch)

		ba = get_equipment_ba(self.equipment)
		default_ba = get_default_ba()

		gl_entries.append(
			prepare_gl(self, {"account": expense_account,
					 "debit": flt(self.total_amount),
					 "debit_in_account_currency": flt(self.total_amount),
					 "cost_center": cost_center,
					 "business_activity": ba
					})
			)

		gl_entries.append(
			prepare_gl(self, {"account": creditor_account,
					 "credit": flt(self.total_amount),
					 "credit_in_account_currency": flt(self.total_amount),
					 "cost_center": self.cost_center,
					 "party_type": "Supplier",
					 "party": self.supplier,
					 "against_voucher": self.name,
										 "against_voucher_type": self.doctype,
					 "business_activity": default_ba
					})
			)

		if self.hiring_branch:
			comparing_branch = self.hiring_branch
		else:
			comparing_branch = self.equipment_branch

		if comparing_branch != self.fuelbook_branch:
			allow_inter_company_transaction = frappe.db.get_single_value("Accounts Settings", "auto_accounting_for_inter_company")
			if allow_inter_company_transaction:
				ic_account = frappe.db.get_single_value("Accounts Settings", "intra_company_account")
				if not ic_account:
					frappe.throw("Setup Intra-Company Account in Accounts Settings")

				customer_cc = get_branch_cc(comparing_branch)

				gl_entries.append(
					prepare_gl(self, {"account": ic_account,
							 "credit": flt(self.total_amount),
							 "credit_in_account_currency": flt(self.total_amount),
							 "cost_center": customer_cc,
							 "business_activity": default_ba
							})
					)

				gl_entries.append(
					prepare_gl(self, {"account": ic_account,
							 "debit": flt(self.total_amount),
							 "debit_in_account_currency": flt(self.total_amount),
							 "cost_center": self.cost_center,
							 "business_activity": default_ba
							})
					)

		return gl_entries

	def get_expense_account(self):
		if self.direct_consumption or getdate(self.posting_date) <= getdate("2018-03-31"):
			if self.is_hsd_item:
				expense_account = frappe.db.get_value("Equipment Category", self.equipment_category, "budget_account")
			else:
				expense_account = frappe.db.get_value("Item", self.pol_type, "expense_account")

			if not expense_account:
				frappe.throw("Set Budget Account in Equipment Category or Item Master")		
		else:
			if self.hiring_warehouse:
				wh = self.hiring_warehouse
			else:
				wh = self.equipment_warehouse
			expense_account = frappe.db.get_value("Account", {"account_type": "Stock", "warehouse": wh}, "name")
			if not expense_account:
					frappe.throw(str(wh) + " is not linked to any account.")
		return expense_account

	def cancel_budget_entry(self):
		frappe.db.sql("delete from `tabCommitted Budget` where reference_no = %s", self.name)
		frappe.db.sql("delete from `tabConsumed Budget` where reference_no = %s", self.name)

	def post_journal_entry(self):
		veh_cat = frappe.db.get_value("Equipment", self.equipment, "equipment_category")
		if veh_cat:
			if veh_cat == "Pool Vehicle":
				pol_account = frappe.db.get_single_value("Maintenance Accounts Settings", "pool_vehicle_pol_expenses")
			else:
				pol_account = frappe.db.get_single_value("Maintenance Accounts Settings", "default_pol_expense_account")
		else:
			frappe.throw("Can not determine machine category")

		expense_bank_account = frappe.db.get_value("Company", frappe.defaults.get_user_default("Company"), "default_payable_account")
		if not expense_bank_account:
 			frappe.throw("No Default Payable Account set in Company")

		ba = get_equipment_ba(a.equipment) 

		if expense_bank_account and pol_account:
			je = frappe.new_doc("Journal Entry")
			je.flags.ignore_permissions = 1 
			je.title = "POL (" + self.pol_type + " for " + self.equipment_number + ")"
			je.voucher_type = 'Bank Entry'
			je.naming_series = 'Bank Payment Voucher'
			je.remark = 'Payment against : ' + self.name;
			je.posting_date = self.posting_date
			je.branch = self.branch

			je.append("accounts", {
					"account": pol_account,
					"cost_center": self.cost_center,
					"reference_type": "POL",
					"reference_name": self.name,
					"debit_in_account_currency": flt(self.total_amount),
					"debit": flt(self.total_amount),
					"business_activity": ba
				})

			je.append("accounts", {
					"account": expense_bank_account,
					"cost_center": self.cost_center,
					"party_type": "Supplier",
					"party": self.supplier,
					"credit_in_account_currency": flt(self.total_amount),
					"credit": flt(self.total_amount),
					"business_activity": ba
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
		if self.equipment_branch == self.fuelbook_branch:
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
			for item in self.items:
				doc = frappe.get_doc("Pol Advance", {'name':item.reference,'equipment_number':self.equipment_number})
				doc.balance_amount  = flt(doc.balance_amount) + flt(item.allocated_amount)
				doc.adjusted_amount = flt(doc.adjusted_amount) - flt(item.allocated_amount)
				if item.has_od:
					doc.od_amount = flt(doc.od_amount) - flt(self.od_amount) 
					doc.od_outstanding_amount = flt(doc.od_outstanding_amount) - flt(self.od_amount)
				doc.save(ignore_permissions=True)
			return
		for item in self.items:
			doc = frappe.get_doc("Pol Advance", {'name':item.reference,'equipment_number':self.equipment_number})
			doc.balance_amount  = flt(item.advance_balance) - flt(item.allocated_amount)
			doc.adjusted_amount = flt(doc.adjusted_amount) + flt(item.allocated_amount)
			if item.has_od:
				doc.od_amount = flt(doc.od_amount) + flt(self.od_amount)
				doc.od_outstanding_amount = flt(doc.od_outstanding_amount) + flt(self.od_amount)
			doc.save(ignore_permissions=True)

	@frappe.whitelist()
	def populate_child_table(self):
		self.calculate_km_diff()
		data = []
		data = frappe.db.sql("""
				SELECT 
					a.name, a.amount,a.balance_amount, a.journal_entry
				FROM `tabPol Advance` a
				WHERE docstatus = 1 
				AND fuelbook = '{}'
				AND fuelbook_branch = '{}'
				AND balance_amount > 0
				AND equipment_number = '{}' 
				ORDER BY entry_date""".format(self.fuelbook,self.equipment_branch,self.equipment_number),as_dict=True)
		self.set('items',[])

		if not data:
			data = frappe.db.sql("""
						SELECT 
							a.name, a.amount,a.balance_amount, a.journal_entry
						FROM `tabPol Advance` a
						WHERE docstatus = 1 
						AND fuelbook = '{}'
						AND fuelbook_branch = '{}'
						AND balance_amount = 0
						AND equipment_number = '{}' 
						ORDER BY entry_date desc limit 1""".format(self.fuelbook,self.equipment_branch,self.equipment_number),as_dict=True)
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
				row = self.append('items',{})
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

		if not self.items:
			frappe.throw("NO POL Advance")

		if total_amount_adjusted < flt(self.total_amount):
			self.od_amount = flt(self.total_amount) - total_amount_adjusted 
			self.items[len(self.items)-1].has_od = 1
			
	def make_gl_entry(self):
		from erpnext.accounts.general_ledger import make_gl_entries
		debit_account= frappe.db.get_value("Item", self.pol_type, "expense_account")
		creditor_account= frappe.get_doc("Company", self.company).default_payable_account
		if not creditor_account:
			frappe.throw("Setup Default Payable Account in Company")
		
		gl_entries = []
		gl_entries.append(
			self.get_gl_dict({"account": debit_account,
						"debit": flt(self.total_amount),
						"debit_in_account_currency": flt(self.total_amount),
						"cost_center": self.cost_center,
						"reference_type": self.doctype,
						"reference_name": self.name,
						"business_activity": self.business_activity,
						"remarks": self.remarks
					})
			)
		gl_entries.append(
			self.get_gl_dict({"account": creditor_account,
						"debit": flt(self.total_amount),
						"debit_in_account_currency": flt(self.total_amount),
						"cost_center": self.cost_center,
						"reference_type": self.doctype,
						"party_type": "Supplier",
						"party": self.supplier,
						"reference_name": self.name,
						"business_activity": self.business_activity,
						"remarks": self.remarks
					})
			)
		gl_entries.append(
			self.get_gl_dict({"account": creditor_account,
						"credit": flt(self.total_amount),
						"credit_in_account_currency": flt(self.total_amount),
						"cost_center": self.cost_center,
						"reference_type": self.doctype,
						"party_type": "Supplier",
						"party": self.supplier,
						"reference_name": self.name,
						"business_activity": self.business_activity,
						"remarks": self.remarks
					})
			)
		gl_entries.append(
			self.get_gl_dict({"account": self.credit_account,
						"credit": flt(self.total_amount),
						"credit_in_account_currency": flt(self.total_amount),
						"cost_center": self.cost_center,
						"party_type": self.party_type,
						"party": self.party,
						"reference_type": self.doctype,
						"reference_name": self.name,
						"business_activity": self.business_activity,
						"remarks": self.remarks
					})
			)
		
		make_gl_entries(gl_entries, cancel=(self.docstatus == 2), update_outstanding="No", merge_entries=False)