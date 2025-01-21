# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt
import json
import frappe
import frappe.utils
from frappe import _
from frappe.model.document import Document
from erpnext.controllers.stock_controller import StockController
from erpnext.accounts.general_ledger import (make_gl_entries, merge_similar_entries)
from erpnext.stock.utils import get_bin, get_incoming_rate
from erpnext.stock.get_item_details import (
	get_barcode_data,
	get_bin_details,
	get_conversion_factor,
	get_default_cost_center,
)
from frappe.utils import (
	cint,
	comma_or,
	cstr,
	flt,
	format_time,
	formatdate,
	get_link_to_form,
	getdate,
	nowdate,
)
import erpnext
from erpnext.setup.doctype.item_group.item_group import get_item_group_defaults
from erpnext.setup.doctype.brand.brand import get_brand_defaults
from erpnext.stock.stock_ledger import NegativeStockError, get_previous_sle, get_valuation_rate

from erpnext.controllers.stock_controller import StockController


class EquipmentMaterialIssue(StockController):
	def validate(self):
		self.validate_posting_time()
		self.validate_item()
		self.set_transfer_qty()
		self.validate_warehouse()
		self.set_debit_account()
		self.validate_uom_is_integer("uom", "qty")
		self.validate_uom_is_integer("stock_uom", "transfer_qty")

		self.calculate_rate_and_amount()

	def on_submit(self):
		self.update_stock_ledger()
		self.make_gl_entries()

	def on_cancel(self):
		self.update_stock_ledger(cancel=True)
		self.make_gl_entries(cancel=True)	

	def validate_item(self):
		stock_items = self.get_stock_items()
		for item in self.get("items"):
			# frappe.throw(str(item.uom))
			if flt(item.qty) and flt(item.qty) < 0:
				frappe.throw(
					_("Row {0}: The item {1}, quantity must be positive number").format(
						item.idx, frappe.bold(item.item_code)
					)
				)

			if item.item_code not in stock_items:
				frappe.throw(_("{0} is not a stock Item").format(item.item_code))

			item_details = self.get_item_details(
				frappe._dict(
					{
						"item_code": item.item_code,
						"company": self.company,
						"project": self.project,
						"uom": item.uom,
						"warehouse": self.warehouse,
					}
				),
				for_update=True,
			)
			# frappe.throw(str(item_details))

			# reset_fields = ("stock_uom", "item_name")
			# for field in reset_fields:
			# 	item.set(field, item_details.get(field))

			# update_fields = (
			# 	"uom",
			# 	"description",
			# 	# "expense_account",
			# 	"cost_center",
			# 	"conversion_factor",
			# )

			# for field in update_fields:
			# 	if not item.get(field):
			# 		item.set(field, item_details.get(field))
			# 	if field == "conversion_factor" and item.uom == item_details.get("stock_uom"):
			# 		item.set(field, item_details.get(field))

			if not item.transfer_qty and item.qty:
				item.transfer_qty = flt(
					flt(item.qty) * flt(item.conversion_factor), self.precision("transfer_qty", item)
				)	
	
	def set_transfer_qty(self):
		for item in self.get("items"):
			if not flt(item.qty):
				frappe.throw(_("Row {0}: Qty is mandatory").format(item.idx), title=_("Zero quantity"))
			if not flt(item.conversion_factor):
				frappe.throw(_("Row {0}: UOM Conversion Factor is mandatory").format(item.idx))
			item.transfer_qty = flt(
				flt(item.qty) * flt(item.conversion_factor), self.precision("transfer_qty", item)
			)
			if not flt(item.transfer_qty):
				frappe.throw(
					_("Row {0}: Qty in Stock UOM can not be zero.").format(item.idx), title=_("Zero quantity")
				)

	def validate_warehouse(self):
		if not self.warehouse:
			frappe.throw(_("Source warehouse is mandatory"))

	def calculate_rate_and_amount(self):
		self.update_valuation_rate()
		self.set_total_amount()

	def update_valuation_rate(self):
		for d in self.get("items"):
			if d.transfer_qty:
				d.amount = flt(flt(d.basic_amount), d.precision("amount"))
				# Do not round off valuation rate to avoid precision loss
				d.valuation_rate = flt(d.basic_rate)

	def set_total_amount(self):
		self.total_amount = None
		self.total_amount = sum([flt(item.amount) for item in self.get("items")])

	def set_debit_account(self):
		debit_account = frappe.db.get_value("Advance Type", self.advance_type, "account")
		if not debit_account:
			frappe.throw("Please set account in {}".format("Advance Type", self.warehouse))
		self.debit_account = debit_account

	def update_stock_ledger(self, cancel=False):
		sl_entries = []
		self.get_sle_for_source_warehouse(sl_entries)
		
		if cancel:
			sl_entries.reverse()
		self.make_sl_entries(sl_entries)

	def make_gl_entries(self, cancel=False):
		credit_account = frappe.db.get_value("Warehouse", self.warehouse, "account")
		if not credit_account:
			frappe.throw("Please set account in {}".format("Warehouse", self.warehouse))
		gl_entries = []
		gl_entries.append(
			self.get_gl_dict({
				"account": self.debit_account,
				"debit": flt(self.total_amount),
				"debit_in_account_currency": flt(self.total_amount),
				"party_type": "Supplier",
				"party": self.supplier,
				"cost_center": self.cost_center,
				"voucher_type":self.doctype,
				"voucher_no":self.name
			})
		)
		gl_entries.append(
			self.get_gl_dict({
				"account": credit_account,
				"credit": flt(self.total_amount),
				"credit_in_account_currency": flt(self.total_amount),
				"cost_center": self.cost_center,
				"voucher_type":self.doctype,
				"voucher_no":self.name
			})
		)
		make_gl_entries(gl_entries, update_outstanding="No", cancel=cancel)

	def get_sle_for_source_warehouse(self, sl_entries):
		if cstr(self.warehouse):
			for d in self.items:
				sle = self.get_sl_entries(
					d,
					{
						"warehouse": cstr(self.warehouse),
						"actual_qty": -flt(d.transfer_qty),
						"incoming_rate": 0,
					},
				)

				sl_entries.append(sle)

	@frappe.whitelist()
	def get_item_details(self, args=None, for_update=False):
		item = frappe.db.sql(
			"""select i.name, i.stock_uom, i.description, i.image, i.item_name, i.item_group,
				i.has_batch_no, i.sample_quantity, i.has_serial_no, i.allow_alternative_item,
				id.expense_account, id.buying_cost_center
			from `tabItem` i LEFT JOIN `tabItem Default` id ON i.name=id.parent and id.company=%s
			where i.name=%s
				and i.disabled=0
				and (i.end_of_life is null or i.end_of_life<'1900-01-01' or i.end_of_life > %s)""",
			(self.company, args.get("item_code"), nowdate()),
			as_dict=1,
		)

		if not item:
			frappe.throw(
				_("Item {0} is not active or end of life has been reached").format(args.get("item_code"))
			)

		item = item[0]
		# item_group_defaults = get_item_group_defaults(item.name, self.company)
		# brand_defaults = get_brand_defaults(item.name, self.company)

		ret = frappe._dict(
			{
				"uom": item.stock_uom,
				"stock_uom": item.stock_uom,
				"description": item.description,
				"item_name": item.item_name,
				# "cost_center": get_default_cost_center(
				# 	args, item, item_group_defaults, brand_defaults, self.company
				# ),
				"qty": args.get("qty"),
				"transfer_qty": args.get("qty"),
				"conversion_factor": 1,
				# "actual_qty": 0,
				# "basic_rate": 0,
				# "has_serial_no": item.has_serial_no,
				# "has_batch_no": item.has_batch_no,
				# "sample_quantity": item.sample_quantity,
				# "expense_account": item.expense_account or item_group_defaults.get("expense_account"),
			}
		)

		# update uom
		if args.get("uom") and for_update:
			ret.update(get_uom_details(args.get("item_code"), args.get("uom"), args.get("qty")))

		# if self.purpose == "Material Issue":
		# 	ret["expense_account"] = item.get("expense_account") or item_group_defaults.get("expense_account")

		args["posting_date"] = self.posting_date
		args["posting_time"] = self.posting_time

		stock_and_rate = get_warehouse_details(args) if args.get("warehouse") else {}
		ret.update(stock_and_rate)

		return ret

@frappe.whitelist()
def get_uom_details(item_code, uom, qty):
	"""Returns dict `{"conversion_factor": [value], "transfer_qty": qty * [value]}`
	:param args: dict with `item_code`, `uom` and `qty`"""
	conversion_factor = get_conversion_factor(item_code, uom).get("conversion_factor")

	if not conversion_factor:
		frappe.msgprint(_("UOM conversion factor required for UOM: {0} in Item: {1}").format(uom, item_code))
		ret = {"uom": ""}
	else:
		ret = {
			"conversion_factor": flt(conversion_factor),
			"transfer_qty": flt(qty) * flt(conversion_factor),
		}
	return ret

@frappe.whitelist()
def get_warehouse_details(args):
	if isinstance(args, str):
		args = json.loads(args)

	args = frappe._dict(args)

	ret = {}
	if args.warehouse and args.item_code:
		args.update(
			{
				"posting_date": args.posting_date,
				"posting_time": args.posting_time,
			}
		)
		ret = {
			"actual_qty": get_previous_sle(args).get("qty_after_transaction") or 0,
			"basic_rate": get_incoming_rate(args),
		}
	return ret
