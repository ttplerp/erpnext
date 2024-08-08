# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _, qb, throw
from erpnext.custom_utils import check_future_date
from frappe.utils import (
	cint,
	comma_or,
	cstr,
	flt,
	format_time,
	formatdate,
	getdate,
	nowdate,
	nowtime,
	money_in_words
)
from erpnext.controllers.stock_controller import StockController
from erpnext.fleet_management.fleet_utils import (
	get_pol_till,
	get_pol_till,
	get_previous_km,
)
from erpnext.accounts.doctype.business_activity.business_activity import get_default_ba
from erpnext.stock.utils import get_bin, get_incoming_rate


class POLIssue(StockController):
	def __init__(self, *args, **kwargs):
		super(POLIssue, self).__init__(*args, **kwargs)

	def validate(self):
		check_future_date(self.posting_date)
		self.validate_uom_is_integer("stock_uom", "qty")
		self.update_items()
		if not self.receive_in_barrel:
			self.check_balance()
		self.validate_data()
		self.validate_posting_date_time()
		self.validate_barrel_or_tanker()

	def validate_barrel_or_tanker(self):
		if not self.tanker and not self.receive_in_barrel:
			frappe.throw("Please set Tanker or Barrel!")

	def validate_data(self):
		if not self.cost_center:
			frappe.throw("Cost Center and Warehouse are Mandatory")
		if self.tanker and self.receive_in_barrel == 1:
			frappe.throw("Cannot Issue In Barrel if Tanker is selected.")
		total_quantity = 0

		if self.hired_equipment:
			for a in self.hired_required_items:
				total_quantity = flt(total_quantity) + flt(a.qty)
		else:
			for a in self.items:
				if flt(a.qty) <= 0:
					frappe.throw(
						"Quantity for <b>"
						+ str(a.equipment)
						+ "</b> should be greater than 0"
					)
				total_quantity = flt(total_quantity) + flt(a.qty)
				previous_km_reading = frappe.db.sql(
					"""
					select cur_km_reading
					from `tabPOL Issue` p inner join `tabPOL Issue Items` pi on p.name = pi.parent	
					where p.docstatus = 1 and p.name != '{}' and pi.equipment = '{}'
					and pi.uom = '{}' 
					order by p.posting_date desc, p.posting_time desc
					limit 1
				""".format(
						self.name, a.equipment, a.uom
					)
				)
				previous_pol_rev_km_reading = frappe.db.sql(
					"""
					select cur_km_reading from `tabPOL Receive` where equipment = '{}' and docstatus = 1 and uom = '{}'
					order by posting_date desc, posting_time desc
					limit 1
				""".format(
						a.equipment, a.uom
					)
				)
				pv_km = 0
				if not previous_km_reading and previous_pol_rev_km_reading:
					previous_km_reading = previous_pol_rev_km_reading
				elif previous_km_reading and previous_pol_rev_km_reading:
					if flt(previous_km_reading[0][0]) < previous_pol_rev_km_reading[0][0]:
						previous_km_reading = previous_pol_rev_km_reading

				if not previous_km_reading:
					pv_km = frappe.db.get_value(
						"Equipment", a.equipment, "initial_km_reading"
					)
				else:
					pv_km = previous_km_reading[0][0]

				if flt(pv_km) >= flt(a.cur_km_reading):
					frappe.throw(
						"Current KM/Hr Reading cannot be less than Previous KM/Hr Reading({}) for Equipment Number <b>{}</b>".format(
							pv_km, a.equipment
						)
					)
				a.km_difference = flt(a.cur_km_reading) - flt(pv_km)
				if a.uom == "Hour":
					a.mileage = flt(a.qty) / flt(a.km_difference)
				else:
					a.mileage = flt(a.km_difference) / a.qty
				a.previous_km = pv_km
				a.amount = flt(a.rate) * flt(a.qty)
		self.total_quantity = total_quantity

	def on_submit(self):
		self.validate_barrel_or_tanker()
		if self.hired_equipment:
			if self.receive_in_barrel == 0:
				self.check_tanker_hsd_balance()
				if self.tanker:
					if self.fuel_policy == "Without Fuel":
						self.post_advance()
					else:
						self.post_journal_entry()
			elif self.receive_in_barrel == 1:
				self.update_stock_ledger()
				self.repost_future_sle_and_gle()
				if self.fuel_policy == "Without Fuel":
					self.post_advance()
				else:
					self.post_journal_entry()
		else:
			if self.receive_in_barrel == 0:
				self.check_tanker_hsd_balance()
				if self.tanker:
					self.post_journal_entry()
			elif self.receive_in_barrel == 1:
				self.update_stock_ledger()
				self.repost_future_sle_and_gle()
				self.post_journal_entry()
		self.make_pol_entry()

	def post_advance(self):
		for a in self.hired_required_items:
			advance = frappe.new_doc("Advance")
			advance.flags.ignore_permissions = 1
			advance_account = frappe.db.get_single_value("Maintenance Settings", "fuel_advance_account")
			if self.receive_in_barrel == 1:
				credit_account = frappe.db.get_value("Warehouse", self.warehouse, "account")
			else:
				credit_account = frappe.db.get_value("Equipment Category", frappe.db.get_value("Equipment", self.tanker, "equipment_category"), "pol_receive_account")
			if not credit_account:
				frappe.throw("Please set account in warehouse '{}'".format(self.warehouse))
			advance.update({
				"doctype": "Advance",
				"posting_date": self.posting_date,
				"party_type": "Supplier",
				"party": a.supplier,
				"branch": self.branch,
				"advance_account": advance_account,
				"advance_amount_requested": a.amount,
				"advance_amount": a.amount,
				"reference_doctype": self.doctype,
				"reference_name": self.name,
				"credit_account": credit_account,
				"advance_type": "Hire Fuel Advance"
			})

			advance.insert()
			self.db_set("advance", advance.name)
		frappe.msgprint(_('{} posted to hire charge advance').format(frappe.get_desk_link(advance.doctype, advance.name)))

	def before_cancel(self):
		if self.receive_in_barrel == 1:
			self.cancel_je()

	def cancel_je(self):
		if self.journal_entry:
			je = frappe.get_doc("Journal Entry", self.journal_entry)
			if (
				frappe.db.get_value("Journal Entry", self.journal_entry, "docstatus")
				== 1
			):
				je.flags.ignore_permissions = 1
				je.cancel()
			elif (
				frappe.db.get_value("Journal Entry", self.journal_entry, "docstatus")
				== 0
			):
				for a in je.accounts:
					child_doc = frappe.get_doc("Journal Entry Account", a.name)
					child_doc.db_set("reference_type", None)
					child_doc.db_set("reference_name", None)
				frappe.db.commit()
				frappe.db.sql(
					"""
					delete from `tabJournal Entry` where name = '{}'
				""".format(
						self.journal_entry
					)
				)
				frappe.db.sql(
					"""
					delete from `tabJournal Entry Account` where parent = '{}'
				""".format(
						self.journal_entry
					)
				)

	def check_balance(self):
		received_data = frappe.db.sql(f"""
			select sum(qty) as qty from `tabPOL Receive` where docstatus = 1
			and equipment = '{self.tanker}' and pol_type = '{self.pol_type}'
			and direct_consumption = 0
		""", as_dict=1)
		issued_data = frappe.db.sql(f"""
			select sum(b.qty) as qty from `tabPOL Issue` a, `tabPOL Issue Items` b where b.parent = a.name and a.docstatus = 1
			and a.tanker = '{self.tanker}' and a.pol_type = '{self.pol_type}' and a.name != '{self.name}'
		""", as_dict=1)
		balance_qty = flt(received_data[0].qty) - flt(issued_data[0].qty)
		qty = 0
		for a in self.items:
			qty += a.qty
		if flt(qty) > flt(balance_qty):
			frappe.throw(f"""
							Not Enough Balance for POL Item <strong>{self.item_name}</strong> in Tanker <strong>{self.tanker}</strong>. Balance is less by <strong>{flt(qty)-flt(balance_qty)}</strong>.
						 """)
	
	def validate_posting_date_time(self):
		if not self.receive_in_barrel:
			return
		else:
			data_list = frappe.db.sql("""
					select *, timestamp(posting_date, posting_time) as "timestamp"
					from `tabStock Ledger Entry`
					where item_code = '{}'
					and warehouse = '{}'
					and is_cancelled = 0
					order by timestamp(posting_date, posting_time) desc, creation desc
					limit 1
				""".format(self.pol_type, self.warehouse), as_dict=1)
			
			if not data_list:
				return
			else:
				previous_sle = data_list[0]

			if getdate(self.posting_date) < previous_sle.get("posting_date"):
				frappe.throw(
					_(
						"Cannot perform transaction for item {3} in warehouse {0} at the posting time of the entry ({1} {2})"
					).format(
						frappe.bold(self.warehouse),
						formatdate(self.posting_date),
						format_time(self.posting_time),
						frappe.bold(self.pol_type),
					)
					+ "<br><br>"
					+ _("Transactions can only be performed from the posting time of the entry ({0} {1})").format(
						frappe.bold(previous_sle.get("posting_date")),
						frappe.bold(previous_sle.get("posting_time"))
					),
					title=_("Posting Date & Time"),
				)
			elif getdate(self.posting_date) == getdate(previous_sle.get("posting_date")):
				if format_time(self.posting_time) < format_time(previous_sle.get("posting_time")):
					frappe.throw(
						_(
							"Row Cannot perform transaction for item {3} in warehouse {0} at the posting time of the entry ({1} {2})"
						).format(
							frappe.bold(self.warehouse),
							formatdate(self.posting_date),
							format_time(self.posting_time),
							frappe.bold(self.pol_type),
						)
						+ "<br><br>"
						+ _("Transactions can only be performed from the posting time of the entry ({0} {1})").format(
							frappe.bold(previous_sle.get("posting_date")),
							frappe.bold(previous_sle.get("posting_time"))
						),
						title=_("Posting Date & Time"),
					)
		

	def on_cancel(self):
		if self.receive_in_barrel == 1:
			self.update_stock_ledger()
			self.repost_future_sle_and_gle()
		self.delete_pol_entry()

	def check_tanker_hsd_balance(self):
		if not self.tanker:
			return
		received_till = get_pol_till(
			"Stock", self.tanker, self.posting_date, self.pol_type, self.posting_time
		)
		issue_till = get_pol_till(
			"Issue", self.tanker, self.posting_date, self.pol_type
		)
		balance = flt(received_till) - flt(issue_till)
		if flt(self.total_quantity) > flt(balance):
			frappe.throw(
				"Not enough balance in tanker to issue. The balance is " + str(balance)
			)

	def post_journal_entry(self):
		total_amount = 0
		if self.hired_equipment:
			for a in self.hired_required_items:
				total_amount += flt(a.amount, 2)
		else:
			for a in self.items:
				total_amount += flt(a.amount, 2)
		if not total_amount:
			frappe.throw(_("Amount should be greater than zero"))
		# if self.settle_imprest_advance == 1:
		# 	credit_account = frappe.get_value("Company", self.company, "imprest_advance_account")
		# debit_account = frappe.db.get_value("Equipment Category", self.equipment_category, "r_m_expense_account")
		credit_account = None
		if self.receive_in_barrel == 1 and not self.tanker:
			credit_account = frappe.db.get_value("Warehouse", self.warehouse, "account")
			if not credit_account:
				credit_account = frappe.get_value(
					"Company", self.company, "default_bank_account"
				)
		elif self.tanker:
			credit_account = frappe.db.get_value("Equipment Category", frappe.db.get_value("Equipment", self.tanker, "equipment_category"),"pol_receive_account")
			if not credit_account:
				frappe.throw("No Account found. Please set POL Receive Account in Equipment Category <strong>{}</strong>".format(frappe.db.get_value("Equipment", self.tanker, "equipment_category")))
		# Posting Journal Entry
		je = frappe.new_doc("Journal Entry")
		je.flags.ignore_permissions = 1
		accounts = []
		if self.hired_equipment:
			for a in self.hired_required_items:
				debit_account = frappe.db.get_single_value("Maintenance Settings", "hired_fuel_expense_account")
				if not debit_account:
					frappe.throw('Plese set Hired Fuel Expense Account in Maintenance Settings.')
				accounts.append(
					{
						"account": debit_account,
						"debit_in_account_currency": flt(a.qty * a.rate, 2),
						"debit": flt(a.qty * a.rate, 2),
						"cost_center": self.cost_center,
						"party_type": "Supplier",
						"party": a.supplier,
						"business_activity": get_default_ba,
					}
				)
		else:
			for a in self.items:
				debit_account = frappe.db.get_value(
					"Equipment Category", a.equipment_category, "pol_advance_account"
				)
				if not debit_account:
					debit_account = frappe.db.get_value(
						"Company", self.company, "pol_expense_account"
					)
				accounts.append(
					{
						"account": debit_account,
						"debit_in_account_currency": flt(a.qty * a.rate, 2),
						"debit": flt(a.qty * a.rate, 2),
						"cost_center": self.cost_center,
						"business_activity": get_default_ba,
					}
				)
		accounts.append(
			{
				"account": credit_account,
				"credit_in_account_currency": flt(total_amount, 2),
				"credit": flt(total_amount, 2),
				"cost_center": self.cost_center,
				"reference_type": "POL Issue",
				"reference_name": self.name,
				"business_activity": get_default_ba,
			}
		)
		# credit

		je.update(
			{
				"doctype": "Journal Entry",
				"voucher_type": "Journal Entry",
				"naming_series": "Journal Voucher",
				"title": "POL Issue - " + self.name,
				"user_remark": "Note: " + "POL Issue - " + self.name,
				"posting_date": self.posting_date,
				"company": self.company,
				"total_amount_in_words": money_in_words(total_amount),
				"branch": self.branch,
				"accounts": accounts,
				"total_debit": flt(total_amount, 2),
				"total_credit": flt(total_amount, 2),
			}
		)
		je.insert()
		# Set a reference to the claim journal entry
		self.db_set("journal_entry", je.name)
		frappe.msgprint(
			_("{} posted to accounts").format(
				frappe.get_desk_link("Journal Entry", je.name)
			)
		)

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
			a.equipment_category = frappe.db.get_value(
				"Equipment", a.equipment, "equipment_category"
			)
			# budget_account = frappe.db.get_value("Equipment Category", a.equipment_category, "budget_account")
			# if not budget_account:
			# 	budget_account = frappe.db.get_value("Item Default", {'parent':self.pol_type}, "expense_account")
			# if not budget_account:
			# 	frappe.throw("Set Budget Account in Equipment Category")
			# a.expense_account = budget_account

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
		# frappe.throw(str(sl_entries))
		self.make_sl_entries(sl_entries)

	def get_sle_for_source_warehouse(self, sl_entries):
		# stock_balances = {}
		# if cstr(self.warehouse):
		# 	if self.pol_type and self.receive_in_barrel and self.warehouse:
		# 		stock_balances = self.get_balance(self.pol_type, self.warehouse)
		# 	for a in self.items:
		# 		quantity = a.qty
		# 		for bal in stock_balances:
		# 			if stock_balances[bal]["balance"] > 0:
		# 				if flt(quantity) <= flt(stock_balances[bal]['balance']):
		# 					sle = self.get_sl_entries(
		# 						{"item_code":self.pol_type, "name":self.name},
		# 						{
		# 							"warehouse": cstr(self.warehouse),
		# 							"actual_qty": -1*flt(quantity),
		# 							# "incoming_rate": flt(bal),
		# 							"valuation_rate":flt(bal),
		# 						},
		# 					)
		# 					a.amount += flt(bal)*flt(quantity)
		# 					frappe.db.sql("""
		# 						update `tabPOL Issue Items` set amount = '{}' where name = '{}'
		# 					""".format(a.amount, a.name))
		# 					sl_entries.append(sle)
		# 					quantity = 0
		# 				else:
		# 					sle = self.get_sl_entries(
		# 						{"item_code":self.pol_type, "name":self.name},
		# 						{
		# 							"warehouse": cstr(self.warehouse),
		# 							"actual_qty": -1*flt(stock_balances[bal]['balance']),
		# 							# "incoming_rate": flt(),
		# 							"valuation_rate":flt(bal),
		# 						},
		# 					)
		# 					a.amount += flt(bal)*flt(quantity)
		# 					frappe.db.sql("""
		# 						update `tabPOL Issue Items` set amount = '{}' where name = '{}'
		# 					""".format(a.amount, a.name))
		# 					quantity -= flt(stock_balances[bal]['balance'])
		# 					sl_entries.append(sle)
		# stock_balances = {}
		if self.hired_equipment:
			for a in self.hired_required_items:
				if cstr(self.warehouse):
					# if self.stock_entry_type == "Material Transfer" and flt(d.difference_qty) < 0:
					# 	sle = self.get_sl_entries(
					# 		d, {"warehouse": cstr(d.s_warehouse),
					# 			"actual_qty": -(flt(d.transfer_qty) - flt(d.difference_qty)),
					# 			"incoming_rate": 0
					# 			})
					# else:
					sle = self.get_sl_entries(
						{"item_code": self.pol_type, "name": self.name},
						{
							"warehouse": cstr(self.warehouse),
							"actual_qty": -1 * flt(a.qty),
							"incoming_rate": 0,
							"valuation_rate": a.rate,
						},
					)

				sl_entries.append(sle)
		else:
			for a in self.items:
				if cstr(self.warehouse):
					# if self.stock_entry_type == "Material Transfer" and flt(d.difference_qty) < 0:
					# 	sle = self.get_sl_entries(
					# 		d, {"warehouse": cstr(d.s_warehouse),
					# 			"actual_qty": -(flt(d.transfer_qty) - flt(d.difference_qty)),
					# 			"incoming_rate": 0
					# 			})
					# else:
					sle = self.get_sl_entries(
						{"item_code": a.item_code, "name": self.name},
						{
							"warehouse": cstr(self.warehouse),
							"actual_qty": -1 * flt(a.qty),
							"incoming_rate": 0,
							"valuation_rate": a.rate,
						},
					)

					sl_entries.append(sle)

	@frappe.whitelist()
	def get_balance(pol_type, warehouse):
		stock_balances = {}
		sle_in = frappe.db.sql(
			"""
			select valuation_rate, actual_qty from `tabStock Ledger Entry` where
			item_code = '{}' and warehouse = '{}' and actual_qty > 0 and is_cancelled = 0 order by posting_date, posting_time asc
		""".format(
				pol_type, warehouse
			),
			as_dict=1,
		)
		sle_out = frappe.db.sql(
			"""
			select sum(actual_qty) from `tabStock Ledger Entry` where item_code = '{}' and warehouse = '{}' and actual_qty < 0
			and is_cancelled = 0
		""".format(
				pol_type, warehouse
			),
			as_dict=1,
		)
		stock_balances = {}
		for s1 in sle_in:
			if str(s1.valuation_rate) not in stock_balances:
				stock_balances.update(
					{str(s1.valuation_rate): {"balance": flt(s1.actual_qty)}}
				)
			else:
				stock_balances[str(s1.valuation_rate)]["balance"] += s1.actual_qty
		for b in sle_out:
			remaining = 0
			for c in stock_balances:
				if remaining == 0:
					if flt(stock_balances[c]["balance"]) > flt(b.actual_qty):
						stock_balances[c]["balance"] -= flt(b.actual_qty)
					elif flt(stock_balances[c]["balance"]) > 0 and flt(
						stock_balances[c]["balance"]
					) < flt(b.actual_qty):
						remaining = -1 * (
							flt(stock_balances[c]["balance"]) - flt(b.actual_qty)
						)
						stock_balances[c]["balance"] = 0
				else:
					if flt(stock_balances[c]["balance"]) > flt(remaining):
						stock_balances[c]["balance"] -= flt(remaining)
						remaining = 0
					elif flt(stock_balances[c]["balance"]) > 0 and flt(
						stock_balances[c]["balance"]
					) < flt(remaining):
						remaining = -1(
							flt(stock_balances[c]["balance"]) - flt(remaining)
						)
						stock_balances[c]["balance"] = 0
		return stock_balances

	@frappe.whitelist()
	def get_rate(self):
		args = frappe._dict(
			{
				"item_code": self.pol_type,
				"warehouse": self.warehouse,
				"posting_date": self.posting_date,
				"posting_time": self.posting_time,
				"voucher_type": self.doctype,
				"voucher_no": self.name,
			}
		)
		if self.receive_in_barrel == 1:
			rate = get_incoming_rate(args, True)
		else:
			rate = self.get_pol_receive_rate()
		return rate

	def get_pol_receive_rate(self):
		received_data = frappe.db.sql(f"""
			select sum(qty) as qty, sum(qty*rate) as amount from `tabPOL Receive` where docstatus = 1
			and equipment = '{self.tanker}' and pol_type = '{self.pol_type}'
			and direct_consumption = 0
		""", as_dict=1)
		issued_data = frappe.db.sql(f"""
			select sum(b.qty) as qty, sum(b.qty*b.rate) as amount from `tabPOL Issue` a, `tabPOL Issue Items` b where b.parent = a.name and a.docstatus = 1
			and a.tanker = '{self.tanker}' and a.pol_type = '{self.pol_type}' and a.name != '{self.name}'
		""", as_dict=1)
		balance_qty = flt(received_data[0].qty) - flt(issued_data[0].qty)
		balance_amount = flt(received_data[0].amount) - flt(issued_data[0].amount)
		if flt(balance_qty) > 0:
			return flt(balance_amount)/flt(balance_qty)

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

# Added by Dawa Tshering on 25/10/2023
def get_permission_query_conditions(user):
	if not user:
		user = frappe.session.user
	user_roles = frappe.get_roles(user)

	if user == "Administrator":
		return
	if "Fleet Manager" in user_roles:
		return

	return """(
		`tabPol Issue`.owner = '{user}'
	)""".format(user=user)
