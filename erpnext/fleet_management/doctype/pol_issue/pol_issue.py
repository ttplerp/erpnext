# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _, qb, throw
from erpnext.custom_utils import check_future_date
from frappe.utils import flt, cint, cstr, money_in_words
from erpnext.controllers.stock_controller import StockController
from erpnext.fleet_management.fleet_utils import get_pol_till, get_pol_till, get_previous_km
from erpnext.accounts.doctype.business_activity.business_activity import get_default_ba

class POLIssue(StockController):
	def __init__(self, *args, **kwargs):
		super(POLIssue, self).__init__(*args, **kwargs)
	def validate(self):
		check_future_date(self.posting_date)
		self.validate_uom_is_integer("stock_uom", "qty")
		self.update_items()
		self.validate_data()
	
	def validate_data(self):
		if not self.cost_center :
			frappe.throw("Cost Center and Warehouse are Mandatory")
		if self.tanker and self.receive_in_barrel == 1:
			frappe.throw("Cannot Issue In Barrel if Tanker is selected.")
		total_quantity = 0
		for a in self.items:
			if flt(a.qty) <= 0:
				frappe.throw("Quantity for <b>"+str(a.equipment)+"</b> should be greater than 0")
			total_quantity = flt(total_quantity) + flt(a.qty)
			previous_km_reading = frappe.db.sql('''
				select cur_km_reading
				from `tabPOL Issue` p inner join `tabPOL Issue Items` pi on p.name = pi.parent	
				where p.docstatus = 1 and p.name != '{}' and pi.equipment = '{}'
				and pi.uom = '{}' 
				order by p.posting_date desc, p.posting_time desc
				limit 1
			'''.format(self.name, a.equipment, a.uom))
			previous_pol_rev_km_reading = frappe.db.sql('''
				select cur_km_reading from `tabPOL Receive` where equipment = '{}' and docstatus = 1 and uom = '{}'
				order by posting_date desc, posting_time desc
				limit 1
			'''.format(a.equipment,a.uom))
			pv_km = 0
			if not previous_km_reading and previous_pol_rev_km_reading:
				previous_km_reading = previous_pol_rev_km_reading
			elif previous_km_reading and previous_pol_rev_km_reading:
				if flt(previous_km_reading[0][0]) < previous_pol_rev_km_reading[0][0]:
					previous_km_reading = previous_pol_rev_km_reading

			if not previous_km_reading:
				pv_km = frappe.db.get_value("Equipment",a.equipment,"initial_km_reading")
			else:
				pv_km = previous_km_reading[0][0]

			if flt(pv_km) >= flt(a.cur_km_reading):
				frappe.throw("Current KM/Hr Reading cannot be less than Previous KM/Hr Reading({}) for Equipment Number <b>{}</b>".format(pv_km,a.equipment))
			a.km_difference = flt(a.cur_km_reading) - flt(pv_km)
			if a.uom == "Hour":
				a.mileage = flt(a.qty) / flt(a.km_difference)
			else :
				a.mileage = flt(a.km_difference) / a.qty
			a.previous_km = pv_km
			a.amount = flt(a.rate) * flt(a.qty)
		self.total_quantity = total_quantity
	
	def on_submit(self):
		if self.receive_in_barrel == 0:
			self.check_tanker_hsd_balance()
		elif self.receive_in_barrel == 1:
			self.update_stock_ledger()
			self.post_journal_entry()
		self.make_pol_entry()

	def before_cancel(self):
		if self.receive_in_barrel == 1:
			self.cancel_je()

	def cancel_je(self):
		if self.journal_entry:
			je = frappe.get_doc("Journal Entry", self.journal_entry)
			if frappe.db.get_value("Journal Entry", self.journal_entry, "docstatus") == 1:
				je.flags.ignore_permissions = 1
				je.cancel()
			elif frappe.db.get_value("Journal Entry", self.journal_entry, "docstatus") == 0:
				for a in je.accounts:
					child_doc = frappe.get_doc("Journal Entry Account", a.name)
					child_doc.db_set("reference_type", None)
					child_doc.db_set("reference_name", None)
				frappe.db.commit()
				frappe.db.sql("""
					delete from `tabJournal Entry` where name = '{}'
				""".format(self.journal_entry))
				frappe.db.sql("""
					delete from `tabJournal Entry Account` where parent = '{}'
				""".format(self.journal_entry))


	def on_cancel(self):
		if self.receive_in_barrel == 1:
			self.update_stock_ledger()
		self.delete_pol_entry()
	
	def check_tanker_hsd_balance(self):
		if not self.tanker:
			return
		received_till = get_pol_till("Stock", self.tanker, self.posting_date, self.pol_type, self.posting_time)
		issue_till = get_pol_till("Issue", self.tanker, self.posting_date, self.pol_type)
		balance = flt(received_till) - flt(issue_till)
		if flt(self.total_quantity) > flt(balance):
			frappe.throw("Not enough balance in tanker to issue. The balance is " + str(balance))	

	def post_journal_entry(self):
		total_amount = 0
		for a in self.items:
			total_amount += flt(a.amount)
		if not total_amount:
			frappe.throw(_("Amount should be greater than zero"))
		credit_account = frappe.get_value("Company", self.company, "default_bank_account")
		# if self.settle_imprest_advance == 1:
		# 	credit_account = frappe.get_value("Company", self.company, "imprest_advance_account")
		# debit_account = frappe.db.get_value("Equipment Category", self.equipment_category, "r_m_expense_account")
		debit_account = frappe.db.get_value("Company", self.company, "pol_expense_account")
		credit_account = frappe.db.get_value("Warehouse", self.warehouse, "account")
		# Posting Journal Entry
		je = frappe.new_doc("Journal Entry")
		je.flags.ignore_permissions=1
		accounts = []
		accounts.append({
				"account": credit_account,
				"credit_in_account_currency": flt(total_amount,2),
				"credit": flt(total_amount,2),
				"cost_center": self.cost_center,
				"reference_type": "POL Issue",
				"reference_name": self.name,
				"business_activity": get_default_ba
			})
		accounts.append({
				"account": debit_account,
				"debit_in_account_currency": flt(total_amount,2),
				"debit": flt(total_amount,2),
				"cost_center": self.cost_center,
				"business_activity": get_default_ba
			})
		
		je.update({
			"doctype": "Journal Entry",
			"voucher_type": "Journal Entry",
			"naming_series": "Journal Voucher",
			"title": "POL Issue - " + self.name,
			"user_remark": "Note: " + "POL Issue - " + self.name,
			"posting_date": self.posting_date,
			"company": self.company,
			"total_amount_in_words": money_in_words(total_amount),
			"branch": self.branch,
			"accounts":accounts,
			"total_debit": flt(total_amount,2),
			"total_credit": flt(total_amount,2)
		})

		# frappe.throw('{}'.format(accounts))
		je.insert()
		#Set a reference to the claim journal entry
		self.db_set("journal_entry",je.name)
		# self.db_set("journal_entry_status", "Forwarded to accounts for processing payment on {0}".format(now_datetime().strftime('%Y-%m-%d %H:%M:%S')))
		frappe.msgprint(_('{} posted to accounts').format(frappe.get_desk_link('Journal Entry',je.name)))
		# frappe.throw('Here!')

	def make_pol_entry(self):
		if self.tanker and self.receive_in_barrel == 0:
			con1 = frappe.new_doc("POL Entry")
			con1.flags.ignore_permissions = 1	
			con1.equipment = self.tanker
			con1.pol_type = self.pol_type
			con1.branch = self.branch
			con1.posting_date = self.posting_date
			con1.posting_time = self.posting_time
			con1.qty = self.total_quantity
			con1.reference_type = self.doctype
			con1.reference = self.name
			con1.type = "Issue"
			con1.is_opening = 0
			con1.cost_center = self.cost_center
			con1.submit()
		if self.tanker and self.receive_in_barrel == 0:
			for item in self.items:
				con = frappe.new_doc("POL Entry")
				con.flags.ignore_permissions = 1	
				con.equipment = item.equipment
				con.pol_type = self.pol_type
				con.branch = self.branch
				con.posting_date = self.posting_date
				con.posting_time = self.posting_time
				con.qty = item.qty
				con.reference_type = self.doctype
				con.reference = self.name
				con.is_opening = 0
				con.uom = item.uom
				con.cost_center = self.cost_center
				con.current_km = item.cur_km_reading
				con.mileage = item.mileage
				con.type = "Receive"
				con.submit()

	def delete_pol_entry(self):
		frappe.db.sql("delete from `tabPOL Entry` where reference = %s", self.name)

	def update_items(self):
		for a in self.items:
			# item code 
			a.item_code = self.pol_type
			# cost center
			a.cost_center = self.cost_center		
			# Warehouse
			a.warehouse = self.warehouse
			# Expense Account
			a.equipment_category = frappe.db.get_value("Equipment", a.equipment, "equipment_category")
			budget_account = frappe.db.get_value("Equipment Category", a.equipment_category, "budget_account")
			if not budget_account:
				budget_account = frappe.db.get_value("Item Default", {'parent':self.pol_type}, "expense_account")
			if not budget_account:
				frappe.throw("Set Budget Account in Equipment Category")
			a.expense_account = budget_account

	def update_stock_ledger(self):
		sl_entries = []
		# finished_item_row = self.get_finished_item_row()

		# make sl entries for source warehouse first
		self.get_sle_for_source_warehouse(sl_entries)

		# SLE for target warehouse
		# self.get_sle_for_target_warehouse(sl_entries)

		# reverse sl entries if cancel
		if self.docstatus == 2:
			sl_entries.reverse()

		self.make_sl_entries(sl_entries)

	def get_sle_for_source_warehouse(self, sl_entries):
		if cstr(self.warehouse):
			for a in self.items:
				sle = self.get_sl_entries(
					{"item_code":self.pol_type, "name":self.name},
					{
						"warehouse": cstr(self.warehouse),
						"actual_qty": -1*flt(a.qty),
						"incoming_rate": flt(a.rate),
						"valuation_rate":flt(a.rate),
					},
				)

				sl_entries.append(sle)

	@frappe.whitelist()
	def get_rate(self):
		from erpnext.stock.utils import get_incoming_rate
		if self.pol_type and self.receive_in_barrel and self.warehouse:
			args = frappe._dict(
				{
					"item_code": self.pol_type,
					"warehouse": self.warehouse,
					"posting_date": self.posting_date,
					"posting_time": self.posting_time,
					"voucher_type": self.doctype,
					"voucher_no": self.name
				}
			)
			rate = get_incoming_rate(args, True)
			return rate


	# def update_stock_ledger(self):
	# 	sl_entries = []
	# 	for a in self.items:
	# 		sl_entries.append(self.get_sl_entries(a, {
	# 			"actual_qty": -1 * flt(a.qty), 
	# 			"warehouse": self.warehouse, 
	# 			"incoming_rate": 0 
	# 		}))

	# 	if self.docstatus == 2:
	# 		sl_entries.reverse()
	# 	self.make_sl_entries(sl_entries, self.amended_from and 'Yes' or 'No')