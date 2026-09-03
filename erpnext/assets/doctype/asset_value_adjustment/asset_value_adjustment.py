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
from erpnext.accounts.accounts_custom_functions import get_number_of_days
from erpnext.accounts.accounts_custom_functions import update_jv

class AssetValueAdjustment(Document):
	def validate(self):
		self.validate_date()
		self.set_current_asset_value()
		self.set_new_asset_value()

	def on_submit(self):
		# self.make_depreciation_entry()
  
		# self.reschedule_depreciations(self.new_asset_value)
		self.change_value(self.new_asset_value)
		self.update_asset()

	def on_cancel(self):
		self.ignore_linked_doctypes = ("GL Entry", "Stock Ledger Entry", "Payment Ledger Entry")
		# doc = frappe.get_doc("Journal Entry", self.journal_entry)
		# doc.cancel()
		# self.reschedule_depreciations(self.current_asset_value)
		self.change_value(self.current_asset_value)
		# self.remove_adjustment_value()
		self.update_asset(cancel=True)
	
	def remove_adjustment_value(self):
		doc = frappe.get_doc("Asset", self.asset)
		doc.db_set("additional_value", flt(doc.additional_value - self.difference_amount))
		doc.db_set("gross_purchase_amount", flt(doc.gross_purchase_amount - self.difference_amount))
	
	def update_asset(self, cancel=False):
		if self.re_valued:
			if cancel:
				frappe.db.set_value("Asset",self.asset,"revalued_asset_value", 0)
				frappe.db.set_value("Asset",self.asset, "re_valued", 0)
			else:
				frappe.db.set_value("Asset",self.asset,"revalued_asset_value", self.new_asset_value)
				frappe.db.set_value("Asset",self.asset,"re_valued", 1)
	
	def validate_date(self):
		asset_purchase_date = frappe.db.get_value("Asset", self.asset, "purchase_date")
		if getdate(self.date) < getdate(asset_purchase_date):
			frappe.throw(
				_("Asset Value Adjustment cannot be posted before Asset's purchase date <b>{0}</b>.").format(
					formatdate(asset_purchase_date)
				),
				title=_("Incorrect Date"),
			)

	def set_new_asset_value(self):
		self.new_asset_value = flt(self.current_asset_value + self.difference_amount)
		# self.new_asset_value = flt(self.difference_amount)

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
		doc.db_set("additional_value", self.difference_amount)

	def reschedule_depreciations(self, asset_value):
		depreciation_start_date = get_last_day(add_days(self.date, -20))
		asset = frappe.get_doc("Asset", self.asset)
		country = frappe.get_value("Company", self.company, "country")

		for d in asset.finance_books:
			d.value_after_depreciation = asset_value

			if d.depreciation_method in ("Straight Line", "Manual"):
				end_date = max(s.schedule_date for s in asset.schedules if cint(s.finance_book_id) == d.idx)
				total_days = date_diff(end_date, depreciation_start_date)
				rate_per_day = flt(d.value_after_depreciation) / flt(total_days)
				from_date = depreciation_start_date
			else:
				no_of_depreciations = len(
					[
						s.name for s in asset.schedules if (cint(s.finance_book_id) == d.idx and not s.journal_entry)
					]
				)

			value_after_depreciation = d.value_after_depreciation
			for data in asset.schedules:
				if getdate(data.schedule_date) <= getdate(depreciation_start_date) and not data.journal_entry:
						frappe.throw("Monthly depreciation on <b>{}</b> for <b>{}</b> is <b>Pending</b>. Run the depreciation before Asset Value Adjustment".format(getdate(data.schedule_date),self.asset))
				if cint(data.finance_book_id) == d.idx:
					if d.depreciation_method in ("Straight Line", "Manual"):
						days = date_diff(data.schedule_date, from_date) 
						depreciation_amount = days * rate_per_day
						from_date = data.schedule_date
					else:
						depreciation_amount = get_depreciation_amount(asset, value_after_depreciation, d)

					if depreciation_amount:
						value_after_depreciation -= flt(depreciation_amount)
						data.depreciation_amount = depreciation_amount
			d.db_update()

		asset.set_accumulated_depreciation(ignore_booked_entry=True)
		for asset_data in asset.schedules:
			if not asset_data.journal_entry:
				asset_data.db_update()
		
		# if asset.status == 'Fully Depreciated':
		# 	asset.prepare_depreciation_data(revaluation_date=self.date)

	def change_value(self, values):	
		asset= self.asset
		value = flt(self.difference_amount)
		start_date = self.date
		credit_account = self.credit_account
		asset_account = self.fixed_asset_account
		
		if(asset and value and getdate(start_date) <= getdate(nowdate())):   
			asset_obj = frappe.get_doc("Asset", asset)

			if asset_obj and asset_obj.docstatus == 1:
				value = -1*flt(value) if self.docstatus == 2 else flt(value)
				#Make GL Entries for additional values and update gross_amount (rate)
				asset_obj.db_set("additional_value", flt(asset_obj.additional_value) + flt(value))
				asset_obj.db_set("gross_purchase_amount", flt(flt(asset_obj.gross_purchase_amount) + flt(value)))
				if self.docstatus == 1:
					self.make_gl_entry(asset_account, credit_account, value, asset_obj, start_date)
				#Get dep. schedules which had not yet happened
				schedules = frappe.db.get_all("Depreciation Schedule", order_by="schedule_date", filters = {"parent": asset_obj.name, "schedule_date": [">=", start_date]},fields={"name", "schedule_date", "journal_entry", "depreciation_entry", "depreciation_amount", "accumulated_depreciation_amount", "income_depreciation_amount","income_accumulated_depreciation"})
				##Get total number of dep days for the asset
				total_days = get_number_of_days(add_days(getdate(start_date), -1), schedules[-1]['schedule_date'])
				##Assign the last dep schedule date for num of days calc
				asset_depreciation_percent = asset_obj.get('finance_books')[0].income_depreciation_percent
				last_sch_date = add_days(getdate(start_date), -1)
				for i in schedules:
					#Add additional values to the depreciation schedules
					#Calc num of days for each dep schedule
					num_days = get_number_of_days(last_sch_date, i.schedule_date)
					#Calc num of days till current schedule
					num_till_days = get_number_of_days(start_date, i.schedule_date)
					##Updated dep amount
					dep_amount = flt(i.depreciation_amount) + (flt(value) * num_days / total_days)
					##Updated accu dep amount
					accu_dep = flt(i.accumulated_depreciation_amount) + (flt(value) * num_till_days / total_days)
					#Income amount
					income = flt(i.income_depreciation_amount) + (flt(value)/(100 * 365.25)) * flt(asset_depreciation_percent) * num_days
					#Accumulated Income amount
					accu_income = flt(i.income_accumulated_depreciation) + (flt(value)/(100 * 365.25)) * flt(asset_depreciation_percent) * num_till_days
					self.update_value(i.name, dep_amount, accu_dep, income, accu_income)
					if i.journal_entry:
						update_jv(i.journal_entry, dep_amount)
					if i.depreciation_entry:
						update_de(i.depreciation_entry, dep_amount, asset)

					##Update last dep schedule date
					last_sch_date = i.schedule_date

				#Add the reappropriation details for record
				# app_details = frappe.new_doc("Asset Modification Entries")
				# app_details.flags.ignore_permissions=1
				# app_details.asset = asset
				# app_details.value = value
				# app_details.credit_account = credit_account
				# app_details.asset_account = asset_account
				# app_details.addition_date = start_date
				# app_details.posted_on = nowdate()
				# app_details.submit()
				return "DONE"
			elif asset_obj.docstatus == 2:
				return "Cannot add value to CANCELLED assets"
			else:
				return "Invalid asset code"
		elif not asset:
			frappe.throw("Invalid asset code")

		elif not value:
			frappe.throw("Invalid asset value")
		elif start_date > nowdate():
			frappe.throw("Effective Date cannot be greater than Today")
		else:
			frappe.throw("Sorry, something happened. Please try again")

	##
	# Make GL Entry for the additional cost
	##
	def make_gl_entry(self, asset_account, credit_account, value, asset, start_date):
		je = frappe.new_doc("Journal Entry")
		je.flags.ignore_permissions = 1
		je.update({
			"voucher_type": "Journal Entry",
			"company": asset.company,
			"remark": "Value (" + str(value) +" ) added to " + asset.name + " (" + asset.asset_name + ") ",
			"user_remark": "Value (" + str(value) +" ) added to " + asset.name + " (" + asset.asset_name + ") ",
			"posting_date": start_date,
			"branch": asset.branch,
			"naming_series":'Journal Entry'
			})

		#credit account update
		party = party_type = None
		account_type = frappe.db.get_value("Account", credit_account, "account_type") or ""
		if account_type in ["Receivable", "Payable"]:
			party = self.party
			party_type = self.party_type
		je.append("accounts", {
			"account": credit_account,
			"party":party,
			"party_type":party_type,
			"credit_in_account_currency": flt(value),
			"reference_type": self.doctype,
			"reference_name": self.name,
			"cost_center": asset.cost_center,
			# "business_activity": asset.business_activity,
			})

		#debit account update
		je.append("accounts", {
			"account": asset_account,
			"debit_in_account_currency": flt(value),
			"reference_type": self.doctype,
			"reference_name": self.name,
			"cost_center": asset.cost_center,
			# "business_activity": asset.business_activity,
			})
		je.flags.ignore_permissions=1
		je.submit()
		self.db_set("journal_entry", je.name)
	
	##
	# Update the depreciation values for schedules
	##
	def update_value(self, sch_name, dep_amount, accu_dep, income, accu_income):
		sch = frappe.get_doc("Depreciation Schedule", sch_name)
		sch.db_set("depreciation_amount",dep_amount)
		sch.db_set("accumulated_depreciation_amount", accu_dep)
		sch.db_set("income_depreciation_amount", income)
		sch.db_set("income_accumulated_depreciation", accu_income)
	
	@frappe.whitelist()
	def update_def_account(self):
		if self.re_valued:
			account= "Revaluation Income/(Loss) - SMCL"
		else:
			account = " "
		return account

@frappe.whitelist()
def get_current_asset_value(asset, finance_book=None):
	cond = {"parent": asset, "parenttype": "Asset"}
	if finance_book:
		cond.update({"finance_book": finance_book})

	return frappe.db.get_value("Asset Finance Book", cond, "value_after_depreciation")

@frappe.whitelist()
def update_def_account(re_valued):
	if re_valued == 1:
		account= "Revaluation Income/(Loss) - SMCL"
	else:
		account = ""
	frappe.throw(str(account))
	return account
