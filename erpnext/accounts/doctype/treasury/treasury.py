# Copyright (c) 2024,s Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt, cint, money_in_words, date_diff, nowdate
from frappe.utils.data import get_first_day, get_last_day, add_years, date_diff, now, today, getdate
from erpnext.accounts.general_ledger import make_gl_entries
from frappe.model.mapper import get_mapped_doc
from datetime import datetime
from erpnext.custom_utils import get_date_diff
import calendar
# from erpnext.controllers.accounts_controller import AccountsController

class Treasury(Document):
	def validate(self):
		self.check_principal_amount()
		self.calculate_number_of_days()

	def on_submit(self):
		if self.is_existing == 0:
			self.post_journal_entry()
	
	def before_cancel(self):
		if self.journal_entry:
			je_status = frappe.get_value("Journal Entry", {"name": self.journal_entry}, "docstatus")
			if cint(je_status) == 1:
				frappe.throw("Journal Entry {} for this transaction needs to be cancelled first".format(frappe.get_desk_link("Journal Entry", self.journal_entry)))
			else:
				frappe.db.sql("delete from `tabJournal Entry` where name = '{}'".format(self.journal_entry))
				self.db_set("journal_entry", None)
	
	def on_cancel(self):
		self.ignore_linked_doctypes = ("GL Entry", "Payment Ledger Entry")
	
	def calculate_number_of_days(self):
		if self.issue_date and self.maturity_date:
			no_of_days = date_diff(self.maturity_date, self.issue_date)
			self.db_set("day", flt(no_of_days))
	
	def check_principal_amount(self):
		if flt(self.principal_amount) <= 0:
			frappe.throw('Principal Amount should be greater than 0')
	
	def post_journal_entry(self):
		if not self.principal_amount:
			frappe.throw("Total Principal Amount should be greater than zero")

		credit_account_query = """
			SELECT tmi.credit_account
			FROM `tabTreasury Mapping Item` tmi
			JOIN `tabTreasury Mapping` tm ON tmi.parent = tm.name
			WHERE tmi.financial_schedule = 'Opening'
			AND tm.party_type = %s
			AND tm.party = %s
			LIMIT 1
		"""
		debit_account_query = """
			SELECT tmi.debit_account
			FROM `tabTreasury Mapping Item` tmi
			JOIN `tabTreasury Mapping` tm ON tmi.parent = tm.name
			WHERE tmi.financial_schedule = 'Opening'
			AND tm.party_type = %s
			AND tm.party = %s
			LIMIT 1
		"""
		credit_account = frappe.db.sql(credit_account_query, (self.party_type, self.party))
		debit_account = frappe.db.sql(debit_account_query, (self.party_type, self.party))

		if not credit_account:
			frappe.throw("Setup Credit Account in Treasury Mapping")
		if not debit_account:
			frappe.throw("Setup Debit Account in Treasury Mapping")

		voucher_type = "Journal Entry"
		voucher_series = "Journal Voucher"
		party_type = self.party_type
		party = self.party

		remarks = []
		if self.remarks:
			remarks.append(("Note: {0}").format(self.remarks))
		remarks_str = " ".join(remarks)

		# Posting Journal Entry
		je = frappe.new_doc("Journal Entry")
		je.update({
			"voucher_type": voucher_type,
			"naming_series": voucher_series,
			"title": f"Treasury Opening - {self.name}",
			"user_remark": remarks_str if remarks_str else f"Note: Opening Treasury - {self.name}",
			"posting_date": self.posting_date,
			"company": self.company,
			"total_amount_in_words": money_in_words(self.principal_amount),
			"branch": self.branch
		})
		
		je.append("accounts", {
			"account": credit_account[0][0],
			"credit_in_account_currency": self.principal_amount,
			"cost_center": self.cost_center,
			"reference_type": "Treasury",
			"reference_name": self.name,
		})
		
		je.append("accounts", {
			"account": debit_account[0][0],
			"debit_in_account_currency": self.principal_amount,
			"cost_center": self.cost_center,
			"reference_type": "Treasury",
			"reference_name": self.name,
			"party_type": party_type,
			"party": party,
		})

		je.insert()

		# Set a reference to the claim journal entry
		self.db_set("journal_entry", je.name)
		frappe.msgprint("Journal Entry created. {}".format(frappe.get_desk_link("Journal Entry", je.name)))

	@frappe.whitelist()
	def check_date_for_interest(self):
		show = 0
		if self.issue_date:
			if nowdate() > self.issue_date:
				show = 1
		return show

	@frappe.whitelist()
	def check_date_for_maturity(self):
		show = 0
		if self.issue_date:
			if nowdate() >= self.issue_date:
				show = 1
		return show

@frappe.whitelist()
def make_interest_accrual(source_name, target_doc=None):
	def set_missing_values(source, target):
		if source.currency != "BTN":
			if frappe.db.exists("Currency Exchange", {'date':nowdate(), 'from_currency':source.currency, 'to_currency':'BTN'}):
				exchange_rate = frappe.db.get_value("Currency Exchange", {'date':nowdate(), 'from_currency':source.currency, 'to_currency':'BTN'}, "exchange_rate")
			else:
				frappe.throw("{} Exchange rate from {} to BTN is not set ".format(nowdate(), source.currency))
			target.conversion_rate = exchange_rate
		target.posting_date = nowdate()
		target.journal_entry = None
	def update_item(obj, target, source_parent):
		target.rate = obj.rate
		target.price_list_rate = obj.price_list_rate
		target.qty = flt(obj.qty) - flt(obj.received_qty)
		target.stock_qty = (flt(obj.qty) - flt(obj.received_qty)) * flt(obj.conversion_factor)
		target.amount = (flt(obj.qty) - flt(obj.received_qty)) * flt(obj.rate)
		target.base_amount = (flt(obj.qty) - flt(obj.received_qty)) * \
			flt(obj.rate) * flt(source_parent.conversion_rate)
		exchange_rate = 0
		if source_parent.currency != "BTN":
			if frappe.db.exists("Currency Exchange", {'date':nowdate(), 'from_currency':source_parent.currency, 'to_currency':'BTN'}):
				exchange_rate = frappe.db.get_value("Currency Exchange", {'date':nowdate(), 'from_currency':source_parent.currency, 'to_currency':'BTN'}, "exchange_rate")
			else:
				frappe.throw("{} Exchange rate from {} to BTN is not set ".format(nowdate(), source_parent.currency))
		if source_parent.currency != "BTN" and source_parent.advance_paid > 0:
			advance_percent = (flt(source_parent.advance_paid)/flt(source_parent.base_grand_total,2))*100
			target.base_price_list_rate = flt(flt(flt(flt(obj.price_list_rate,2) * flt(advance_percent/100,2),2)*source_parent.conversion_rate,2)+flt(flt(flt(obj.price_list_rate,2)-flt(flt(obj.price_list_rate,2) * flt(advance_percent/100,2),2),2)*exchange_rate,2),2)
			target.base_rate = flt(flt(flt(flt(obj.rate,2) * flt(advance_percent/100,2),2)*source_parent.conversion_rate,2)+flt(flt(flt(obj.rate,2)-flt(flt(obj.rate,2) * flt(advance_percent/100,2),2),2)*exchange_rate,2),2)
			# frappe.throw(str(target.base_price_list_rate))
			target.actual_rate = flt(flt(flt(flt(obj.rate,2) * flt(advance_percent/100,2),2)*source_parent.conversion_rate,2)+flt(flt(flt(obj.rate,2)-flt(flt(obj.rate,2) * flt(advance_percent/100,2),2),2)*exchange_rate,2),2)

	doc = get_mapped_doc("Treasury", source_name,	{
		"Treasury": {
			"doctype": "Interest Accrual",
			# "field_map": {
			# 	"per_billed": "per_billed",
			# 	"supplier_warehouse": "supplier_warehouse",
			# 	"naming_series":"naming_series"
			# },
			"validation": {
				"docstatus": ["=", 1],
			}
		},
		# "Purchase Order Item": {
		# 	"doctype": "Purchase Receipt Item",
		# 	"field_map": {
		# 		"name": "purchase_order_item",
		# 		"parent": "purchase_order",
		# 		"bom": "bom",
		# 		"material_request": "material_request",
		# 		"material_request_item": "material_request_item",
		# 		"reference_type": "reference_type",
		# 		"reference_name": "reference_name",
		# 		"price_list_rate": "price_list_rate",
		# 		"rate": "rate",
		# 		"task": "task",
		# 		"site": "site",
		# 	},
		# 	"postprocess": update_item,
		# 	"condition": lambda doc: abs(doc.received_qty) < abs(doc.qty) and doc.delivered_by_supplier != 1
		# },
		# "Purchase Taxes and Charges": {
		# 	"doctype": "Purchase Taxes and Charges",
		# 	"add_if_empty": True
		# }
	}, target_doc, set_missing_values, ignore_permissions=True)

	return doc

@frappe.whitelist()
def make_treasury_maturity(source_name, target_doc=None):
	def set_missing_values(source, target):
		target.journal_entry = None
		target.posting_date = nowdate()
		total_interest = frappe.db.sql("""
                                 select sum(interest_amount) as total_interest from `tabInterest Accrual` where docstatus = 1 and treasury_id = '{}'
                                 """.format(source.name),as_dict=1)
		if total_interest:
			total_interest = flt(total_interest[0].total_interest,2)
		else:
			total_interest = 0
		days = source.day
		days_paid = frappe.db.sql("""
                            select sum(days) as days from `tabInterest Accrual` where treasury_id = '{}'
                            and docstatus = 1
                            """.format(source.name),as_dict=1)
		if days_paid:
			days_paid = flt(days_paid[0].days)
		else:
			days_paid = 0
		days -= days_paid
		month = flt(str(source.maturity_date).split("-")[1])
		# days_in_month = flt(calendar.monthrange(int(2024), month)[1])
		days_in_month = no_of_days_in_month = get_date_diff(get_first_day(getdate(source.maturity_date)), get_last_day(getdate(source.maturity_date)))
		if days > days_in_month:
			days = days_in_month
		d2 = datetime.strptime(str(source.maturity_date).split("-")[0]+"-12-31","%Y-%m-%d").date()
		d3 = datetime.strptime(str(source.maturity_date).split("-")[0]+"-01-01","%Y-%m-%d").date()
		days_in_year = (d2-d3).days
		interest_amount = flt(flt(source.principal_amount) * (flt(source.interest_rate)*0.01) *(flt(days)/flt(days_in_year)),2)
		total_interest = flt(total_interest+interest_amount,2)
		target.interest_amount = flt(interest_amount,2)
		# target.total_interest_amount = total_interest
		target.maturity_amount = flt(source.principal_amount+total_interest,2)
		target.tds_amount = flt(total_interest*0.05,2)
	def update_item(obj, target, source_parent):
		pass

	doc = get_mapped_doc("Treasury", source_name,	{
		"Treasury": {
			"doctype": "Maturity",
			# "field_map": {
			# 	"per_billed": "per_billed",
			# 	"supplier_warehouse": "supplier_warehouse",
			# 	"naming_series":"naming_series"
			# },
			"validation": {
				"docstatus": ["=", 1],
			}
		},
		# "Purchase Order Item": {
		# 	"doctype": "Purchase Receipt Item",
		# 	"field_map": {
		# 		"name": "purchase_order_item",
		# 		"parent": "purchase_order",
		# 		"bom": "bom",
		# 		"material_request": "material_request",
		# 		"material_request_item": "material_request_item",
		# 		"reference_type": "reference_type",
		# 		"reference_name": "reference_name",
		# 		"price_list_rate": "price_list_rate",
		# 		"rate": "rate",
		# 		"task": "task",
		# 		"site": "site",
		# 	},
		# 	"postprocess": update_item,
		# 	"condition": lambda doc: abs(doc.received_qty) < abs(doc.qty) and doc.delivered_by_supplier != 1
		# },
		# "Purchase Taxes and Charges": {
		# 	"doctype": "Purchase Taxes and Charges",
		# 	"add_if_empty": True
		# }
	}, target_doc, set_missing_values, ignore_permissions=True)

	return doc