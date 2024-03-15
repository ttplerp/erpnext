# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _, qb
from frappe.utils import (
    cint,
    comma_or,
    cstr,
    flt,
    format_time,
    formatdate,
    getdate,
    nowdate,
    nowtime
)
from erpnext.custom_utils import check_future_date
from erpnext.accounts.doctype.business_activity.business_activity import get_default_ba
from frappe.utils import money_in_words, cstr, flt, formatdate, cint, now_datetime
from erpnext.controllers.stock_controller import StockController
from erpnext.accounts.general_ledger import (
	make_gl_entries,
	merge_similar_entries,
)
from erpnext.custom_workflow import validate_workflow_states, notify_workflow_states

from erpnext.accounts.party import get_party_account


class POLReceive(StockController):
	def validate(self):
		check_future_date(self.posting_date)
		# self.calculate_km_diff()
		self.validate_data()
		validate_workflow_states(self)
		# if self.workflow_state != "Approved":
		#     notify_workflow_states(self)
		# self.balance_check()
		self.validate_posting_date_time()

	def on_submit(self):
		if self.direct_consumption == 0 and self.receive_in_barrel == 1:
			self.update_stock_ledger()
			self.repost_future_sle_and_gle()
		self.update_pol_expense()
		self.make_pol_entry()
		self.post_journal_entry()
		self.post_advance()
		self.make_pol_receive_invoice()
		# notify_workflow_states(self)

	def post_advance(self):
		if self.fuel_policy != "Without Fuel" or not self.direct_consumption or (self.direct_consumption and not self.hired_equipment):
			return 
		
		if self.settle_imprest_advance:
			credit_account = frappe.db.get_value("Company", self.company, "imprest_advance_account")
		else:
			credit_account = frappe.db.get_value("Company", self.company, "default_bank_account")
		
		advance_doc = frappe.new_doc("Advance")
		advance_doc.flags.ignore_permissions = 1
		advance_account = frappe.db.get_single_value("Maintenance Settings", "fuel_advance_account")
		if not advance_account:
			frappe.throw("Please set Fuel Advance Account in Maintenance Settings")
		advance_doc.update({
			"doctype": "Advance",
			"posting_date": self.posting_date,
			"party_type": "Supplier",
			"party": self.supplier,
			"branch": self.branch,
			"advance_account": advance_account,
			"advance_amount_requested": self.total_amount,
			"advance_amount": self.total_amount,
			"reference_doctype": self.doctype,
			"reference_name": self.name,
			"credit_account": credit_account,
			"advanced_paid_from_imprest_money": 1 if self.settle_imprest_advance else 0,
			"imprest_party": self.party if self.settle_imprest_advance else "",
			"advance_type": "Hired Fuel Advance"
		})

		advance_doc.insert()
		self.db_set("advance", advance_doc.name)
		frappe.msgprint(_('{} posted to Advance').format(frappe.get_desk_link(advance_doc.doctype, advance_doc.name)))

	def before_cancel(self):
		if self.direct_consumption == 0 and self.receive_in_barrel == 1:
			self.update_stock_ledger()
			self.cancel_je()
		self.delete_pol_entry()

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

	def on_cancel(self):
		self.ignore_linked_doctypes = ("GL Entry", "Stock Ledger Entry", "Payment Ledger Entry", "Repost Item Valuation")
		self.update_pol_expense()
		self.delete_pol_entry()
		# notify_workflow_states(self)
		if self.direct_consumption == 0 and self.receive_in_barrel == 1:
			self.update_stock_ledger()
			self.repost_future_sle_and_gle()

	def update_stock_ledger(self):
		sl_entries = []
		# finished_item_row = self.get_finished_item_row()

		# make sl entries for source warehouse first
		# self.get_sle_for_source_warehouse(sl_entries, finished_item_row)

		# SLE for target warehouse
		self.get_sle_for_target_warehouse(sl_entries)

		# reverse sl entries if cancel
		if self.docstatus == 2:
			sl_entries.reverse()

		self.make_sl_entries(sl_entries)

	def get_sle_for_target_warehouse(self, sl_entries):
		if cstr(self.warehouse):
			sle = self.get_sl_entries(
				{"item_code": self.pol_type, "name": self.name},
				{
					"warehouse": cstr(self.warehouse),
					"actual_qty": flt(self.qty),
					"incoming_rate": flt(self.rate),
					"valuation_rate": flt(self.rate),
				},
			)

			sl_entries.append(sle)

	# def balance_check(self):
	# 	total_balance = 0
	# 	for row in self.items:
	# 		total_balance = flt(total_balance) + flt(row.balance_amount)
	# 	if total_balance < self.total_amount :
	# 		frappe.throw("<b>Payable Amount({})</b> cannot be greater than <b>Total Advance Balance({})</b>".format(self.total_amount,total_balance))
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

	def post_journal_entry(self):
		if self.hired_equipment:
			if self.fuel_policy == "Without Fuel" or not self.settle_imprest_advance:
				return
		else:
			if not self.settle_imprest_advance:
				return
		
		if not self.total_amount:
			frappe.throw(_("Amount should be greater than zero"))

		credit_account = debit_account = pol_receive_account = pol_advance_account = None

		# getting credit account 
		if self.settle_imprest_advance == 1:
			credit_account = frappe.get_value("Company", self.company, "imprest_advance_account")
		else:
			credit_account = frappe.get_value("Company", self.company, "default_bank_account")
	
		if self.equipment:
			(pol_receive_account, pol_advance_account) = frappe.db.get_value("Equipment Category", self.equipment_category,
				[
					"pol_receive_account",
					"pol_advance_account",
				],
			)

		if self.hired_equipment:
			if self.fuel_policy == "With Fuel":
				if self.hired_equipment_type == "Vehicle":
					debit_account = frappe.db.get_single_value("Maintenance Settings", "vehicle_expense_account")
				else:
					debit_account = frappe.db.get_single_value("Maintenance Settings", "machine_expense_account")
			if not debit_account:
				frappe.throw("Set <strong>{}</strong> account in Maintenance Settings.".format("Vehicle Expense Advance" if self.hired_equipment_type == "Vehicle" else "Machine Expense Account"))
		else:
			if self.direct_consumption:
				debit_account = pol_advance_account
			else:
				if not debit_account and self.receive_in_barrel == 1:
					debit_account = frappe.db.get_value("Warehouse", self.warehouse, "account")
				else:
					debit_account = pol_receive_account

		# Posting Journal Entry
		je = frappe.new_doc("Journal Entry")
		je.flags.ignore_permissions = 1
		accounts = []
		accounts.append(
			{
				"account": debit_account,
				"debit_in_account_currency": flt(self.total_amount, 2),
				"debit": flt(self.total_amount, 2),
				"cost_center": self.cost_center,
				"party_type": "Supplier",
				"party": self.paid_to,
				"business_activity": get_default_ba,
			}
		)
		if self.settle_imprest_advance == 0 or not self.settle_imprest_advance:
			accounts.append(
				{
					"account": credit_account,
					"credit_in_account_currency": flt(self.total_amount, 2),
					"credit": flt(self.total_amount, 2),
					"cost_center": self.cost_center,
					"reference_type": "POL Receive",
					"reference_name": self.name,
					"business_activity": get_default_ba,
				}
			)
		else:
			accounts.append(
				{
					"account": credit_account,
					"credit_in_account_currency": flt(self.total_amount, 2),
					"credit": flt(self.total_amount, 2),
					"cost_center": self.cost_center,
					"reference_type": "POL Receive",
					"reference_name": self.name,
					"party_type": "Employee",
					"party": self.party,
					"business_activity": get_default_ba,
				}
			)

		je.update(
			{
				"doctype": "Journal Entry",
				"voucher_type": "Journal Entry" if self.settle_imprest_advance else "Bank Entry",
				"naming_series": "Bank Payment Voucher" if self.settle_imprest_advance == 0 else "Journal Voucher",
				"title": "POL Receive - " + self.equipment if (self.receive_in_barrel == 0 and not self.hired_equipment) else "Adjustment Entry",
				"user_remark": "Note: " + "POL Receive - " + self.equipment if (self.receive_in_barrel == 0 and not self.hired_equipment) else "",
				"posting_date": self.posting_date,
				"company": self.company,
				"mode_of_payment" "Online Payment" if self.settle_imprest_advance else ""
				"total_amount_in_words": money_in_words(self.total_amount),
				"branch": self.branch,
				"accounts": accounts,
				"total_debit": flt(self.total_amount, 2),
				"total_credit": flt(self.total_amount, 2),
				"settle_project_imprest": self.settle_imprest_advance,
			}
		)
		# frappe.throw('{}'.format(accounts))
		je.insert()
		# Set a reference to the claim journal entry
		self.db_set("journal_entry", je.name)
		self.db_set(
			"journal_entry_status",
			"Forwarded to accounts for processing payment on {0}".format(
				now_datetime().strftime("%Y-%m-%d %H:%M:%S")
			),
		)
		frappe.msgprint(
			_("{} posted to accounts").format(
				frappe.get_desk_link("Journal Entry", je.name)
			)
		)

	def update_pol_expense(self):
		if self.docstatus == 2:
			for item in self.items:
				doc = frappe.get_doc("POL Expense", {"name": item.pol_expense})
				doc.adjusted_amount = flt(doc.adjusted_amount) - flt(
					item.allocated_amount
				)
				doc.balance_amount = flt(doc.amount) - flt(doc.adjusted_amount)
				doc.save(ignore_permissions=True)
			return
		for item in self.items:
			doc = frappe.get_doc("POL Expense", {"name": item.pol_expense})
			doc.balance_amount = flt(item.balance_amount) - flt(item.allocated_amount)
			doc.adjusted_amount = flt(doc.adjusted_amount) + flt(item.allocated_amount)
			doc.save(ignore_permissions=True)

	@frappe.whitelist()
	def get_previous_km_reading(self):
		previous_km_reading = frappe.db.sql(
			"""
						select cur_km_reading from `tabPOL Receive` where docstatus = 1 
						and equipment = '{}' and uom = '{}'
						order by posting_date desc, posting_time desc
						limit 1
						""".format(
				self.equipment, self.uom
			)
		)
		previous_km_reading_pol_issue = frappe.db.sql(
			"""
				select cur_km_reading
				from `tabPOL Issue` p inner join `tabPOL Issue Items` pi on p.name = pi.parent	
				where p.docstatus = 1 and pi.equipment = '{}'
				and pi.uom = '{}' 
				order by p.posting_date desc, p.posting_time desc
				limit 1
			""".format(
				self.equipment, self.uom
			)
		)
		if not previous_km_reading and previous_km_reading_pol_issue:
			previous_km_reading = previous_km_reading_pol_issue
		elif previous_km_reading and previous_km_reading_pol_issue:
			if flt(previous_km_reading[0][0]) < previous_km_reading_pol_issue[0][0]:
				previous_km_reading = previous_km_reading_pol_issue

		pv_km = 0
		if not previous_km_reading:
			pv_km = frappe.db.get_value(
				"Equipment", self.equipment, "initial_km_reading"
			)
		else:
			pv_km = previous_km_reading[0][0]
		self.previous_km = pv_km
		return pv_km

	def on_trash(self):
		self.ignore_linked_doctypes = ("GL Entry", "Stock Ledger Entry", "Payment Ledger Entry", "Repost Item Valuation")
		
	def calculate_km_diff(self):
		if cint(self.hired_equipment) == 1:
			return
		if cint(self.direct_consumption) == 0:
			return
		if not self.uom:
			self.uom = frappe.db.get_value("Equipment", self.equipment, "reading_uom")
		if not self.uom:
			self.uom = frappe.db.get_value(
				"Equipment Type", self.equipment_type, "reading_uom"
			)
		
		pv_km = self.get_previous_km_reading()
		# Commentted by Dawa Tshering on 20/11/2023
		# if flt(pv_km) >= flt(self.cur_km_reading):
		#     frappe.throw(
		#         "Current KM/Hr Reading cannot be less than Previous KM/Hr Reading({}) for Equipment Number <b>{}</b>".format(
		#             pv_km, self.equipment
		#         )
		#     )
		# self.km_difference = flt(self.cur_km_reading) - flt(pv_km)
		# if self.uom == "Hour":
		#     self.mileage = self.qty / flt(self.km_difference)
		# else:
		#     self.mileage = flt(self.km_difference) / self.qty

		# Commentted by Dawa Tshering on 20/11/2023
		if flt(pv_km) >= flt(self.cur_km_reading):
			frappe.throw(
				"Current KM/Hr Reading cannot be less than Previous KM/Hr Reading({}) for Equipment Number <b>{}</b>".format(
					pv_km, self.equipment
				)
			)
		self.km_difference = flt(self.cur_km_reading) - flt(pv_km)
		if self.uom == "Hour":
			self.mileage = self.qty / flt(self.km_difference)
		else:
			self.mileage = flt(self.km_difference) / self.qty

	def validate_data(self):
		# if not self.fuelbook_branch:
		# 	frappe.throw("Fuelbook Branch are mandatory")

		if flt(self.qty) <= 0 or flt(self.rate) <= 0:
			frappe.throw("Quantity and Rate should be greater than 0")
		if not self.hired_equipment:
			if not self.equipment_category and self.receive_in_barrel == 0:
				frappe.throw("Vehicle Category Missing")

	@frappe.whitelist()
	def populate_child_table(self):
		# self.calculate_km_diff()
		pol_exp = qb.DocType("POL Expense")
		je = qb.DocType("Journal Entry")
		data = []
		if not self.equipment:
			frappe.throw("Either equipment is missing")
		data = (
			qb.from_(pol_exp)
			.select(pol_exp.name, pol_exp.amount, pol_exp.balance_amount)
			.where(
				(pol_exp.docstatus == 1)
				& (pol_exp.balance_amount > 0)
				& (pol_exp.fuel_book == self.fuelbook)
			)
			.orderby(pol_exp.entry_date, order=qb.desc)
		).run(as_dict=True)
		if not data:
			frappe.throw(
				"NO POL Expense Found against Equipment {}".format(self.equipment)
			)
		self.set("items", [])
		allocated_amount = self.total_amount
		total_amount_adjusted = 0
		for d in data:
			if cint(d.is_opening) == 0:
				row = self.append("items", {})
				row.pol_expense = d.name
				row.amount = d.amount
				row.balance_amount = d.balance_amount
				if row.balance_amount >= allocated_amount:
					row.allocated_amount = allocated_amount
					total_amount_adjusted += flt(row.allocated_amount)
					allocated_amount = 0
				elif row.balance_amount < allocated_amount:
					row.allocated_amount = row.balance_amount
					total_amount_adjusted += flt(row.allocated_amount)
					allocated_amount = flt(allocated_amount) - flt(row.balance_amount)
				row.balance = flt(row.balance_amount) - flt(row.allocated_amount)
			else:
				row = self.append("items", {})
				row.pol_expense = d.name
				row.amount = d.amount
				row.balance_amount = d.balance_amount
				if row.balance_amount >= allocated_amount:
					row.allocated_amount = allocated_amount
					total_amount_adjusted += flt(row.allocated_amount)
					allocated_amount = 0
				elif row.balance_amount < allocated_amount:
					row.allocated_amount = row.balance_amount
					total_amount_adjusted += flt(row.allocated_amount)
					allocated_amount = flt(allocated_amount) - flt(row.balance_amount)
				row.balance = flt(row.balance_amount) - flt(row.allocated_amount)

	def make_pol_entry(self):
		if cint(self.hired_equipment) == 1:
			return
		container = frappe.db.get_value("Equipment Type", self.equipment_type, "is_container")
		if (
			not self.direct_consumption
			and not container
			and self.receive_in_barrel == 0
		):
			frappe.throw(
				"Equipment {} is not a container".format(frappe.bold(self.equipment))
			)

		if self.direct_consumption:
			con1 = frappe.new_doc("POL Entry")
			con1.flags.ignore_permissions = 1
			con1.equipment = self.equipment
			con1.pol_type = self.pol_type
			con1.branch = self.branch
			con1.posting_date = self.posting_date
			con1.posting_time = self.posting_time
			con1.qty = self.qty
			con1.reference_type = self.doctype
			con1.reference = self.name
			con1.type = "Receive"
			con1.is_opening = 0
			con1.cost_center = self.cost_center
			con1.current_km = self.cur_km_reading
			con1.mileage = self.mileage
			con1.uom = self.uom
			con1.submit()
		elif container:
			con = frappe.new_doc("POL Entry")
			con.flags.ignore_permissions = 1
			con.equipment = self.equipment
			con.pol_type = self.pol_type
			con.branch = self.branch
			con.posting_date = self.posting_date
			con.posting_time = self.posting_time
			con.qty = self.qty
			con.reference_type = self.doctype
			con.reference = self.name
			con.is_opening = 0
			con.uom = self.uom
			con.cost_center = self.cost_center
			con.type = "Stock"
			con.submit()

			# if container:
			# 	con2 = frappe.new_doc("POL Entry")
			# 	con2.flags.ignore_permissions = 1
			# 	con2.equipment = self.equipment
			# 	con2.pol_type = self.pol_type
			# 	con2.branch = self.branch
			# 	con2.date = self.posting_date
			# 	con2.posting_time = self.posting_time
			# 	con2.qty = self.qty
			# 	con2.reference_type = self.doctype
			# 	con2.reference_name = self.name
			# 	con2.type = "Issue"
			# 	con2.is_opening = 0
			# 	con2.cost_center = self.cost_center
			# 	con2.submit()

	def delete_pol_entry(self):
		frappe.db.sql("delete from `tabPOL Entry` where reference = %s", self.name)

	@frappe.whitelist()
	def make_pol_receive_invoice(self, submit=True):
		if self.settle_imprest_advance:
			return

		if self.hired_equipment:
			if self.fuel_policy == "Without Fuel":
				return
			
			if self.hired_equipment_type == "Machine":
				debit_account = frappe.db.get_single_value("Maintenance Settings", "machine_expense_account")
			elif self.hired_equipment_type == "Vehicle":
				debit_account = frappe.db.get_single_value("Maintenance Settings", "vehicle_expense_account")
		if self.equipment:
			if self.direct_consumption:
				debit_account = frappe.db.get_value("Equipment Category", self.equipment_category, "pol_advance_account")
			else:
				debit_account = frappe.db.get_value("Equipment Category", self.equipment_category, "pol_receive_account")
		if self.receive_in_barrel == 1:
			debit_account = frappe.db.get_value("Warehouse", self.warehouse, "account")

		credit_account = frappe.db.get_value("Company", self.company, "default_payable_account")

		pol_rev_invoice = frappe.new_doc("POL Receive Invoice")
		pol_rev_invoice.flags.ignore_permissions=1
		pol_rev_invoice.update({
			"doctype": "POL Receive Invoice",
			"posting_date": self.posting_date,
			"company": self.company,
			"branch": self.branch,
			"amount": self.total_amount,
			"party_type": "Supplier",
			"party": self.paid_to,
			"credit_account": credit_account,
			"debit_account": debit_account,
			"reference_doctype":self.doctype,
			"reference_name":self.name,
		})

		if submit:
			frappe.get_doc(pol_rev_invoice).submit()
		# else:
		# 	delete_pol_rev_invoice(pol_rev_invoice)


	# def delete_pol_rev_invoice(pol_rev_invoice):
	# 	"""Delete ledger entry on cancel of leave application/allocation/encashment"""
	# 		if pol_rev_invoice.transaction_type == "Leave Allocation":
	# 			validate_leave_allocation_against_leave_application(ledger)

	# 	expired_entry = get_previous_expiry_ledger_entry(ledger)
	# 	frappe.db.sql(
	# 		"""DELETE
	# 		FROM `tabLeave Ledger Entry`
	# 		WHERE
	# 			`transaction_name`=%s
	# 			OR `name`=%s""",
	# 		(ledger.transaction_name, expired_entry),
	# 	)

	# 	pol_rev_invoice.insert()
		frappe.msgprint(_('POL Receive Invoice {0} created').format(frappe.get_desk_link("POL Receive Invoice", pol_rev_invoice.name)))


# query permission
def get_permission_query_conditions(user):
	if not user:
		user = frappe.session.user
	user_roles = frappe.get_roles(user)

	if user == "Administrator" or "System Manager" in user_roles:
		return

	return """(
		`tabPOL Receive`.owner = '{user}'
		or
		exists(select 1
			from `tabEmployee` as e
			where e.branch = `tabPOL Receive`.branch
			and e.user_id = '{user}')
		or
		exists(select 1
			from `tabEmployee` e, `tabAssign Branch` ab, `tabBranch Item` bi
			where e.user_id = '{user}'
			and ab.employee = e.name
			and bi.parent = ab.name
			and bi.branch = `tabPOL Receive`.branch)
	)""".format(
		user=user
	)
