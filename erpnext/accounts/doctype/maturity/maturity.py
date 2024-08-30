# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt, cint, money_in_words, date_diff, nowdate
from erpnext.accounts.general_ledger import make_gl_entries
from frappe.utils.data import get_first_day, get_last_day, add_years, date_diff, now, today, getdate
from frappe.model.mapper import get_mapped_doc
from datetime import datetime
from erpnext.custom_utils import get_date_diff
import calendar

class Maturity(Document):
	def validate(self):
		self.validate_existing()
		self.get_days()
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
		if datetime.strptime(str(self.posting_date),"%Y-%m-%d") < datetime.strptime(str(frappe.db.get_value("Treasury", self.treasury_id, "issue_date")), "%Y-%m-%d"):
			frappe.throw("Posting Date for maturity cannot be earlier than {}".format(frappe.db.get_value("Treasury", self.treasury_id, "issue_date")))
		exists = frappe.db.sql("""
                         select name from `tabMaturity` where
                         treasury_id = '{}' and name != '{}' and docstatus = 1
                         """.format(self.treasury_id, self.name),as_dict=1)
		if exists:
			exists = ", ".join(a.name for a in exists)
			frappe.throw("Maturity document for Treasury {0} already exists. Existing Document ID: {1}".format(self.treasury_id, exists, self.fiscal_year, self.month))

	def post_journal_entry(self):
		party_type = frappe.db.get_value("Treasury", self.treasury_id, "party_type")
		party = frappe.db.get_value("Treasury", self.treasury_id, "party")
		if not self.total_interest_amount:
			frappe.throw("Total Interest Amount should be greater than zero")

		credit_account_query = """
			SELECT tmi.credit_account
			FROM `tabTreasury Mapping Item` tmi
			JOIN `tabTreasury Mapping` tm ON tmi.parent = tm.name
			WHERE tmi.financial_schedule = 'Maturity'
			AND tm.party_type = %s
			AND tm.party = %s
			LIMIT 1
		"""
		debit_account_query = """
			SELECT tmi.debit_account
			FROM `tabTreasury Mapping Item` tmi
			JOIN `tabTreasury Mapping` tm ON tmi.parent = tm.name
			WHERE tmi.financial_schedule = 'Maturity'
			AND tm.party_type = %s
			AND tm.party = %s
			LIMIT 1
		"""

		intrest_account_query = """
			SELECT tmi.interest_account
			FROM `tabTreasury Mapping Item` tmi
			JOIN `tabTreasury Mapping` tm ON tmi.parent = tm.name
			WHERE tmi.financial_schedule = 'Maturity'
			AND tm.party_type = %s
			AND tm.party = %s
			LIMIT 1
		"""

		tds_account_query = """
			SELECT tmi.tds_account
			FROM `tabTreasury Mapping Item` tmi
			JOIN `tabTreasury Mapping` tm ON tmi.parent = tm.name
			WHERE tmi.financial_schedule = 'Maturity'
			AND tm.party_type = %s
			AND tm.party = %s
			LIMIT 1
		"""

		credit_account = frappe.db.sql(credit_account_query, (party_type, party))
		debit_account = frappe.db.sql(debit_account_query, (party_type, party))
		interest_account = frappe.db.sql(intrest_account_query, (party_type, party))
		tds_account = frappe.db.sql(tds_account_query, (party_type, party))

		if not credit_account:
			frappe.throw("Setup Credit Account in Treasury Mapping")
		if not debit_account:
			frappe.throw("Setup Debit Account in Treasury Mapping")
		if not interest_account:
			frappe.throw("Setup Interest Account in Treasury Mapping")
		if not tds_account:
			frappe.throw("Setup TDS Account in Treasury Mapping")

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
			"title": f"Treasury Maturity - {self.name}",
			"user_remark": f"Note: Treasury Maturity - {self.name}",
			"posting_date": self.posting_date,
			"company": self.company,
			"total_amount_in_words": money_in_words(self.maturity_amount),
			"branch": self.branch
		})
		
		je.append("accounts", {
			"account": credit_account[0][0],
			"credit_in_account_currency": flt(frappe.db.get_value("Treasury", self.treasury_id, "principal_amount"),2),
			"cost_center": self.cost_center,
			"reference_type": "Maturity",
			"reference_name": self.name,
		})
		je.append("accounts", {
			"account": interest_account[0][0],
			"credit_in_account_currency": flt(self.total_interest_amount,2),
			"cost_center": self.cost_center,
			"reference_type": "Maturity",
			"reference_name": self.name,
		})
		je.append("accounts", {
			"account": debit_account[0][0],
			"debit_in_account_currency": flt(self.maturity_amount-self.tds_amount,2),
			"cost_center": self.cost_center,
			"reference_type": "Maturity",
			"reference_name": self.name,
		})
		je.append("accounts", {
			"account": tds_account[0][0],
			"debit_in_account_currency": flt(self.tds_amount,2),
			"cost_center": self.cost_center,
			"reference_type": "Maturity",
			"reference_name": self.name
		})
		frappe.throw("Credit:\nPrinciple Amount: {} Total Interest: {}\nDebit:\n Maturity Amount - TDS Amount: {} TDS Amount: {}".format(str(flt(frappe.db.get_value("Treasury", self.treasury_id, "principal_amount"),2)), str(flt(self.total_interest_amount,2)), str(flt(self.maturity_amount-self.tds_amount,2)), str(flt(self.tds_amount,2))))

		je.insert()

		# Set a reference to the claim journal entry
		self.db_set("journal_entry", je.name)
		frappe.msgprint("Journal Entry created. {}".format(frappe.get_desk_link("Journal Entry", je.name)))

	def calculate_interest_amount(self):
		self.total_interest_amount = self.maturity_amount = 0
		if not self.treasury_id:
			frappe.throw('Please select Treasury ID to calculate interest')
		# d2 = datetime.strptime(str(self.posting_date).split("-")[0]+"-12-31","%Y-%m-%d").date()
		# d3 = datetime.strptime(str(frappe.db.get_value("Treasury", self.treasury_id, "issue_date")).split("-")[0]+"-01-01","%Y-%m-%d").date()
		# days = ((d2-d3).days)+1
		# self.days = days
		# treasury = frappe.get_doc("Treasury", self.treasury_id)
		# days = treasury.day
		# days_paid = frappe.db.sql("""
        #                     select sum(days) as days from `tabInterest Accrual` where treasury_id = '{}'
        #                     and name != '{}' and docstatus = 1
        #                     """.format(self.treasury_id, self.name),as_dict=1)
		# if days_paid:
		# 	days_paid = flt(days_paid[0].days)
		# else:
		# 	days_paid = 0
		# days -= days_paid
		# month = flt(str(self.posting_date).split("-")[1])
		# # days_in_month = flt(calendar.monthrange(int(2024), month)[1])
		# days_in_month = no_of_days_in_month = get_date_diff(get_first_day(getdate(self.posting_date)), get_last_day(getdate(self.posting_date)))
		# if days > days_in_month:
		# 	days = days_in_month
		# self.days = days
		# d2 = datetime.strptime(str(self.posting_date).split("-")[0]+"-12-31","%Y-%m-%d").date()
		# d3 = datetime.strptime(str(self.posting_date).split("-")[0]+"-01-01","%Y-%m-%d").date()
		# days_in_year = (d2-d3).days
		# self.interest_amount = (flt(self.interest_rate)*0.01) *(flt(days)/flt(days_in_year))
		total_interest = frappe.db.sql("""
										select sum(interest_amount) as total_interest from `tabInterest Accrual` where docstatus = 1 and treasury_id = '{}'
										""".format(self.name),as_dict=1)
		if total_interest:
			total_interest = flt(total_interest[0].total_interest,2)
		else:
			total_interest = 0
		if frappe.db.get_value("Treasury", self.treasury_id, "is_existing") == 1:
			total_interest += flt(frappe.db.get_value("Treasury", self.treasury_id, "opening_accrued_interest"),2)
		self.total_interest_amount = total_interest
		self.total_interest_amount += self.interest_amount
		self.maturity_amount = flt(flt(frappe.db.get_value("Treasury", self.treasury_id, "principal_amount"),2) + self.total_interest_amount,2)
	@frappe.whitelist()
	def get_days(self):
		if not self.treasury_id:
			frappe.throw('Please select Treasury ID to calculate interest')
		d2 = datetime.strptime(str(self.posting_date).split("-")[0]+"-12-31","%Y-%m-%d").date()
		d3 = datetime.strptime(str(frappe.db.get_value("Treasury", self.treasury_id, "issue_date")).split("-")[0]+"-01-01","%Y-%m-%d").date()
		days = ((d2-d3).days)+1
		self.days = days
	@frappe.whitelist()
	def get_month(self, posting_date):
		month = flt(str(self.posting_date).split("-")[1])
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
