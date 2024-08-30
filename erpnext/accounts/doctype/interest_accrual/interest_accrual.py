# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import date_diff, flt, cint, money_in_words
from frappe.utils.data import get_first_day, get_last_day, add_years, date_diff, now, today, getdate
from datetime import datetime
from erpnext.custom_utils import get_date_diff
import calendar

class InterestAccrual(Document):
	def validate(self):
		self.validate_existing()
		self.calculate_interest_amount()

	def on_submit(self):
		self.post_journal_entry()

	def before_cancel(self):
		if self.journal_entry:
			doc = frappe.get_doc("Journal Entry", self.journal_entry)
			self.journal_entry = None
			if doc.docstatus == 1:
				doc.cancel()
		for a in frappe.db.sql("""
					select name from `tabGL Entry` where against_voucher = '{}'
					""".format(self.name),as_dict=1):
			frappe.db.sql("update `tabGL Entry` set against_voucher = NULL where name = '{}'".format(a.name))
				

	def validate_existing(self):
		if not self.posting_date:
			frappe.throw("Please Enter Posting Date.")
		if self.get_month(frappe.db.get_value("Treasury", self.treasury_id, "maturity_date")) == self.month and str(frappe.db.get_value("Treasury", self.treasury_id, "maturity_date")).split("-")[0] == str(self.posting_date).split("-")[0]:
			frappe.throw("Cannot create Interest for Treasury {} on maturity month".format(self.name))
		exists = frappe.db.sql("""
                         select name from `tabInterest Accrual` where
                         treasury_id = '{}' and year(posting_date) = '{}' and month = '{}'
                         and name != '{}' and docstatus < 2
                         """.format(self.treasury_id, str(self.posting_date).split("-")[0], self.month, self.name),as_dict=1)
		if exists:
			exists = ", ".join(a.name for a in exists)
			frappe.throw("Interest Accrual document for Treasury {0} for the year {2} and month {3} already exists. Existing Document ID: {1}".format(self.treasury_id, exists, self.fiscal_year, self.month))

	def post_journal_entry(self):
		party_type = frappe.db.get_value("Treasury", self.treasury_id, "party_type")
		party = frappe.db.get_value("Treasury", self.treasury_id, "party")
		if not self.interest_amount:
			frappe.throw("Total Interest Amount should be greater than zero")

		credit_account_query = """
			SELECT tmi.credit_account
			FROM `tabTreasury Mapping Item` tmi
			JOIN `tabTreasury Mapping` tm ON tmi.parent = tm.name
			WHERE tmi.financial_schedule = 'Monthly Interest Accruals'
			AND tm.party_type = %s
			AND tm.party = %s
			LIMIT 1
		"""
		debit_account_query = """
			SELECT tmi.debit_account
			FROM `tabTreasury Mapping Item` tmi
			JOIN `tabTreasury Mapping` tm ON tmi.parent = tm.name
			WHERE tmi.financial_schedule = 'Monthly Interest Accruals'
			AND tm.party_type = %s
			AND tm.party = %s
			LIMIT 1
		"""
		credit_account = frappe.db.sql(credit_account_query, (party_type, party))
		debit_account = frappe.db.sql(debit_account_query, (party_type, party))

		if not credit_account:
			frappe.throw("Setup Credit Account in Treasury Mapping")
		if not debit_account:
			frappe.throw("Setup Debit Account in Treasury Mapping")

		voucher_type = "Journal Entry"
		voucher_series = "Journal Voucher"
		party_type = party_type
		party = party

		# remarks.append(("Note: {0}").format())
		# remarks_str = " ".join(remarks)

		# Posting Journal Entry
		je = frappe.new_doc("Journal Entry")
		je.update({
			"voucher_type": voucher_type,
			"naming_series": voucher_series,
			"title": f"Treasury Interest Accrual - {self.name}",
			"user_remark": f"Note: Treasury Interest Accrual - {self.name}",
			"posting_date": self.posting_date,
			"company": self.company,
			"total_amount_in_words": money_in_words(self.interest_amount),
			"branch": self.branch,
			"business_activity": "Common"
		})
		
		je.append("accounts", {
			"account": credit_account[0][0],
			"credit_in_account_currency": self.interest_amount,
			"cost_center": self.cost_center,
			"reference_type": "Interest Accrual",
			"reference_name": self.name,
			"business_activity": "Common"
		})
		
		je.append("accounts", {
			"account": debit_account[0][0],
			"debit_in_account_currency": self.interest_amount,
			"cost_center": self.cost_center,
			"reference_type": "Interest Accrual",
			"reference_name": self.name,
			"party_type": party_type,
			"party": party,
			"business_activity": "Common"
		})

		je.insert()

		# Set a reference to the claim journal entry
		self.db_set("journal_entry", je.name)
		frappe.msgprint("Journal Entry created. {}".format(frappe.get_desk_link("Journal Entry", je.name)))

	def calculate_interest_amount(self):
		if not self.treasury_id:
			frappe.throw('Please select Treasury ID to calculate interest')
		treasury = frappe.get_doc("Treasury", self.treasury_id)
		days = treasury.day
		days_paid = frappe.db.sql("""
                            select sum(days) as days from `tabInterest Accrual` where treasury_id = '{}'
                            and name != '{}' and docstatus = 1
                            """.format(self.treasury_id, self.name),as_dict=1)
		if days_paid:
			days_paid = flt(days_paid[0].days)
		else:
			days_paid = 0
		days -= days_paid
		month = flt(str(self.posting_date).split("-")[1])
		# days_in_month = flt(calendar.monthrange(int(2024), month)[1])
		days_in_month = no_of_days_in_month = get_date_diff(get_first_day(getdate(self.posting_date)), get_last_day(getdate(self.posting_date)))
		if days > days_in_month:
			days = days_in_month
		self.days = days
		d2 = datetime.strptime(str(self.posting_date).split("-")[0]+"-12-31","%Y-%m-%d").date()
		d3 = datetime.strptime(str(self.posting_date).split("-")[0]+"-01-01","%Y-%m-%d").date()
		days_in_year = ((d2-d3).days)+1
		self.interest_amount = flt(flt(treasury.principal_amount) * (flt(self.interest_rate)*0.01) *(flt(days)/flt(days_in_year)),2)

	@frappe.whitelist()
	def get_month(self, posting_date):
		month = flt(str(posting_date).split("-")[1])
		if month == 1:
			return "Jan"
		elif month == 2:
			return "Feb"
		elif month == 3:
			return "Mar"
		elif month == 4:
			return "Apr"
		elif month == 5:
			return "May"
		elif month == 6:
			return "Jun"
		elif month == 7:
			return "Jul"
		elif month == 8:
			return "Aug"
		elif month == 9:
			return "Sep"
		elif month == 10:
			return "Oct"
		elif month == 11:
			return "Nov"
		elif month == 12:
			return "Dec"
