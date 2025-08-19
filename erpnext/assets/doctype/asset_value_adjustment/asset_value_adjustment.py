# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import (
	add_days,
	add_months,
	cint,
	date_diff,
	flt,
	get_datetime,
	get_last_day,
	get_first_day,
	getdate,
	month_diff,
	nowdate,
	today,
	get_year_ending,
	get_year_start,
	formatdate,
)

from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import (
	get_checks_for_pl_and_bs_accounts,
)
from erpnext.assets.doctype.asset.asset import get_depreciation_amount
from erpnext.assets.doctype.asset.depreciation import get_depreciation_accounts


class AssetValueAdjustment(Document):
	def validate(self):
		self.validate_date()
		self.set_current_asset_value()
		self.set_new_asset_value()

	def on_submit(self):
		self.make_depreciation_entry()
		self.reschedule_depreciations(self.new_asset_value, cancel=0)
	
	def on_cancel(self):
		doc = frappe.get_doc("Journal Entry", self.journal_entry)
		doc.cancel()
		self.reschedule_depreciations(self.current_asset_value, cancel=1)
		self.remove_adjustment_value()
	
	def remove_adjustment_value(self):
		doc = frappe.get_doc("Asset", self.asset)
		# doc.db_set("additional_value", doc.additional_value - self.difference_amount)
		frappe.db.set_value(doc.doctype, doc.name, "additional_value", flt(doc.additional_value - self.difference_amount))

	def validate_date(self):
		asset_purchase_date = frappe.db.get_value("Asset", self.asset, "purchase_date")
		without_purchase = frappe.db.get_value("Asset", self.asset, "asset_creation_without_pd")
		if getdate(self.date) < getdate(asset_purchase_date) and without_purchase == 0:
			frappe.throw(
				_("Asset Value Adjustment cannot be posted before Asset's purchase date <b>{0}</b>.").format(
					formatdate(asset_purchase_date)
				),
				title=_("Incorrect Date"),
			)

	def set_new_asset_value(self):
		self.new_asset_value = flt(self.current_asset_value + self.difference_amount)

	def set_current_asset_value(self):
		actual_current_asset_value = get_current_asset_value(self.asset, self.finance_book)
		if self.current_asset_value != actual_current_asset_value:
			self.current_asset_value = flt(actual_current_asset_value,2)
			frappe.msgprint(
					_("Current Asset value reset with a new Asset Value <b>{}</b>").format(
						actual_current_asset_value
					),
					title=_("Incorrect Asset Value"),
				)

	def make_depreciation_entry(self):
		je = frappe.new_doc("Journal Entry")
		je.voucher_type = "Journal Entry"
		je.posting_date = self.date
		je.company = self.company
		je.remark = "Asset Adjustment Entry against {0} worth {1}".format(self.asset, self.difference_amount)
		je.finance_book = self.finance_book
		je.branch = self.branch

		credit_entry = {
			"account": self.credit_account,
			"credit_in_account_currency": self.difference_amount,
			"cost_center": self.cost_center,
			"reference_type": "Asset",
			"reference_name": self.asset,
		}

		debit_entry = {
			"account": self.fixed_asset_account,
			"debit_in_account_currency": self.difference_amount,
			"cost_center": self.cost_center,
			"reference_type": "Asset",
			"reference_name": self.asset,
		}

		accounting_dimensions = get_checks_for_pl_and_bs_accounts()

		for dimension in accounting_dimensions:
			if dimension.get("mandatory_for_bs"):
				credit_entry.update(
					{
						dimension["fieldname"]: self.get(dimension["fieldname"])
						or dimension.get("default_dimension")
					}
				)

			if dimension.get("mandatory_for_pl"):
				debit_entry.update(
					{
						dimension["fieldname"]: self.get(dimension["fieldname"])
						or dimension.get("default_dimension")
					}
				)

		je.append("accounts", credit_entry)
		je.append("accounts", debit_entry)

		je.flags.ignore_permissions = True
		je.submit()

		self.db_set("journal_entry", je.name)
		doc = frappe.get_doc("Asset", self.asset)
		# doc.db_set("additional_value", self.difference_amount)
		frappe.db.set_value(doc.doctype, doc.name, "additional_value", flt(self.difference_amount))

	def reschedule_depreciations(self, asset_value, cancel=None):
		depreciation_start_date = get_last_day(add_days(self.date, -20))
		asset = frappe.get_doc("Asset", self.asset)
		country = frappe.get_value("Company", self.company, "country")
		
		new_gross_value = asset.gross_purchase_amount + self.difference_amount
		if cancel:
			new_gross_value = asset.gross_purchase_amount - self.difference_amount

		for d in asset.finance_books:
			d.value_after_depreciation = asset_value

			if d.depreciation_method in ("Straight Line", "Manual"):
				end_date = max(s.schedule_date for s in asset.schedules if cint(s.finance_book_id) == d.idx and s.depreciation_amount > 0)
				total_days = date_diff(end_date, depreciation_start_date)
				rate_per_day = 0
				if total_days:
					rate_per_day = flt(d.value_after_depreciation) / flt(total_days)
				from_date = depreciation_start_date
			else:
				no_of_depreciations = len(
					[
						s.name for s in asset.schedules if (cint(s.finance_book_id) == d.idx and not s.journal_entry)
					]
				)

			value_after_depreciation = d.value_after_depreciation
			
			# Calculate income_accumulated_depreciation
			income_accumulated_depreciation = 0
			remaining_booked_schedules = [s for s in asset.schedules if cint(s.finance_book_id) == d.idx and not s.journal_entry and s.income_depreciation_amount > 0]
			booked_schedules = [s for s in asset.schedules if cint(s.finance_book_id) == d.idx and s.journal_entry]
			if booked_schedules:
				income_accumulated_depreciation = max(s.income_accumulated_depreciation for s in booked_schedules)
			remaining_dep_amount = flt(asset.gross_purchase_amount - income_accumulated_depreciation) + self.difference_amount
			if cancel:
				remaining_dep_amount = asset.gross_purchase_amount - self.difference_amount
			
			for data in asset.schedules:
				if getdate(data.schedule_date) <= getdate(depreciation_start_date) and not data.journal_entry:
						frappe.throw("Monthly depreciation on <b>{}</b> for <b>{}</b> is <b>Pending</b>. Run the depreciation before Asset Value Adjustment".format(getdate(data.schedule_date),self.asset))
				if cint(data.finance_book_id) == d.idx:
					# Calculate days
					days = 0
					if d.depreciation_method in ("Straight Line", "Manual"):
						days = date_diff(data.schedule_date, from_date) 
						depreciation_amount = days * rate_per_day
						from_date = data.schedule_date
					else:
						depreciation_amount = get_depreciation_amount(asset, value_after_depreciation, d)

					if depreciation_amount and data.depreciation_amount:
						value_after_depreciation -= flt(depreciation_amount)
						data.depreciation_amount = depreciation_amount

					# Only calculate income depreciation if the schedule hasn't been booked yet
					if not data.journal_entry:
						income_depreciation_amount = self._get_income_tax_depreciation_amount(d, data.schedule_date, days, income_accumulated_depreciation, new_gross_value, remaining_dep_amount, remaining_booked_schedules)
						income_accumulated_depreciation += flt(income_depreciation_amount)
						data.income_depreciation_amount = income_depreciation_amount
						data.income_accumulated_depreciation = income_accumulated_depreciation if income_depreciation_amount else 0.0

			d.db_update()

		asset.set_accumulated_depreciation(ignore_booked_entry=True)
		for asset_data in asset.schedules:
			if not asset_data.journal_entry:
				asset_data.db_update()

	def _get_income_tax_depreciation_amount(self,finance_book, schedule_date,no_of_days,income_accumulated_depreciation, new_gross_value, remaining_dep_amount, remaining_booked_schedules):
		#new work
		# convert_to_year = len(remaining_booked_schedules) / 12
		dep_per_year = (flt(remaining_dep_amount) - flt(finance_book.expected_value_after_useful_life)) / (len(remaining_booked_schedules)/12)
		
		# Use the adjusted asset value instead of the original gross_purchase_amount
		# frappe.throw(f"{new_gross_value}")
		# dep_per_year = (flt(gross_amount) - flt(finance_book.expected_value_after_useful_life)) * (flt(finance_book.income_depreciation_percent)/100)
		days_in_year = date_diff(get_year_ending(getdate(schedule_date)),get_year_start(getdate(schedule_date))) + 1
		income_depreciation_amount = (flt(dep_per_year) / cint(days_in_year)) * cint(no_of_days)
		
		if (flt(new_gross_value) - flt(finance_book.expected_value_after_useful_life)) >= (flt(income_accumulated_depreciation)+income_depreciation_amount):
			return income_depreciation_amount
		elif (flt(new_gross_value) - flt(finance_book.expected_value_after_useful_life)) - (flt(income_accumulated_depreciation)) > 1:
			income_depreciation_amount = flt(income_depreciation_amount - ((income_accumulated_depreciation+income_depreciation_amount) - (flt(new_gross_value) - flt(finance_book.expected_value_after_useful_life))),2)
			# frappe.throw(str(income_depreciation_amount))
			return income_depreciation_amount
		else:
			return 0.0

@frappe.whitelist()
def get_current_asset_value(asset, finance_book=None):
	cond = {"parent": asset, "parenttype": "Asset"}
	if finance_book:
		cond.update({"finance_book": finance_book})

	return frappe.db.get_value("Asset Finance Book", cond, "value_after_depreciation")
