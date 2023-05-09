# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt
import frappe
from frappe import _, msgprint, scrub
from frappe.model.document import Document
from frappe.utils import cint, cstr, flt, fmt_money, formatdate, get_link_to_form, nowdate
from erpnext.budget.doctype.budget.budget import validate_expense_against_budget
from erpnext.custom_workflow import validate_workflow_states, notify_workflow_states

class BudgetReappropiation(Document):
	def validate(self):
		self.validate_budget()
		self.budget_check()
		# validate_workflow_states(self)
	def on_submit(self):
		self.budget_appropriate(cancel=False)

	def on_cancel(self):
		self.budget_appropriate(cancel=True)
	
	#Added by Thukten on 13th Sept, 2023
	def validate_budget(self):
		budget_against_field = frappe.scrub(self.budget_against)
		from_budget_against = self.from_cost_center if self.budget_against == "Cost Center" else self.from_project
		to_budget_against = self.to_cost_center if self.budget_against == "Cost Center" else self.to_project
		total_amount = 0
		if not self.items:
			frappe.throw(_("Please provide Budget Head or Account to Appropriate budget"))

		for d in self.items:
			total_amount += flt(d.amount)
			if d.from_account:
				from_budget_exist = frappe.db.sql(
						"""
						select
							b.name, ba.account from `tabBudget` b, `tabBudget Account` ba
						where
							ba.parent = b.name and b.docstatus = 1 and b.company = %s and %s=%s and
							b.fiscal_year=%s and ba.account =%s """
						% ("%s", budget_against_field, "%s", "%s", "%s"),
						(self.company, from_budget_against, self.fiscal_year, d.from_account),
						as_dict=1,
					)
				if not from_budget_exist:
					frappe.throw(
						_(
							"Budget record doesnot exists against {0} '{1}' and account '{2}' for fiscal year {3}"
						).format(self.budget_against, from_budget_against, d.from_account, self.fiscal_year),
					)
			if d.to_account:
				to_budget_exist = frappe.db.sql(
						"""
						select
							b.name, ba.account from `tabBudget` b, `tabBudget Account` ba
						where
							ba.parent = b.name and b.docstatus = 1 and b.company = %s and %s=%s and
							b.fiscal_year=%s and ba.account =%s """
						% ("%s", budget_against_field, "%s", "%s", "%s"),
						(self.company, to_budget_against, self.fiscal_year, d.to_account),
						as_dict=1,
					)
				if not to_budget_exist:
					frappe.throw(
						_(
							"Budget record doesnot exists against {0} '{1}' and account '{2}' for fiscal year {3}"
						).format(self.budget_against, to_budget_against, d.to_account, self.fiscal_year),
					)
		self.total_reappropiation_amount = total_amount
	# Check the budget amount in the from cost center and account
	def budget_check(self):
		args = frappe._dict()
		args.budget_against = self.budget_against
		args.cost_center = self.from_cost_center if self.budget_against == "Cost Center" else None
		args.project = self.from_project if self.budget_against == "Project" else None
		args.posting_date = self.appropriation_on
		args.fiscal_year = self.fiscal_year
		args.company = self.company
		for a in self.get('items'):
			args.account = a.from_account
			args.amount = a.amount
		validate_expense_against_budget(args)

	# Added by Thukten on 13th September, 2022
	def budget_appropriate(self, cancel=False):
		if frappe.db.get_value("Fiscal Year", self.fiscal_year, "closed"):
			frappe.throw("Fiscal Year " + fiscal_year + " has already been closed")
		else:
			budget_against_field = frappe.scrub(self.budget_against)
			from_budget_against = self.from_cost_center if self.budget_against == "Cost Center" else self.from_project
			to_budget_against = self.to_cost_center if self.budget_against == "Cost Center" else self.to_project
			for d in self.items:
				from_month = d.from_month
				to_month = d.to_month
				if d.amount <= 0:
					frappe.throw("Budget appropiation Amount should be greater than 0 for record " + str(a.idx))
				from_account = frappe.db.sql(
						"""
						select
							ba.name, ba.account from `tabBudget` b, `tabBudget Account` ba
						where
							ba.parent = b.name and b.docstatus < 2 and b.company = %s and %s=%s and
							b.fiscal_year=%s and ba.account =%s """
						% ("%s", budget_against_field, "%s", "%s", "%s"),
						(self.company, from_budget_against, self.fiscal_year, d.from_account),
						as_dict=1,
					)
				monthly_budget_check = frappe.db.get_single_value("Budget Settings","monthly_budget_check")
				if from_account:
					from_budget_account = frappe.get_doc("Budget Account", from_account[0].name)
					total = flt(from_budget_account.budget_amount) - flt(d.amount)
					budget_sent = flt(from_budget_account.budget_sent) + flt(d.amount)
					# frappe.throw(str(from_budget_account.budget_amount))
					if cancel:
						total = flt(from_budget_account.budget_amount) + flt(d.amount)
						budget_sent = flt(from_budget_account.budget_sent) - flt(d.amount)
					# added By Rinzin
					from_budget_account.db_set("budget_sent", flt(budget_sent,2))
					if monthly_budget_check:
						if from_month:
							if from_month =="January":
								if cancel:
									sent = flt(from_budget_account.bs_jan) - flt(d.amount)
									from_budget_account.db_set("bs_jan", flt(sent,2))
									from_budget_account.db_set("budget_amount", flt(total,2))
								else:
									sent = flt(from_budget_account.bs_jan) + flt(d.amount)
									from_budget_account.db_set("bs_jan", flt(sent,2))
									from_budget_account.db_set("budget_amount", flt(total,2))
							elif from_month =="Februery":
								if cancel:
									sent = flt(from_budget_account.bs_feb) - flt(d.amount)
									from_budget_account.db_set("bs_feb", flt(sent,2))
									from_budget_account.db_set("budget_amount", flt(total,2))
								else:
									sent = flt(from_budget_account.bs_feb) + flt(d.amount)
									from_budget_account.db_set("bs_feb", flt(sent,2))
									from_budget_account.db_set("budget_amount", flt(total,2))
							elif from_month =="March":
								if cancel:
									sent = flt(from_budget_account.bs_march) - flt(d.amount)
									from_budget_account.db_set("bs_march", flt(sent,2))
									from_budget_account.db_set("budget_amount", flt(total,2))
								else:
									sent = flt(from_budget_account.bs_march) + flt(d.amount)
									from_budget_account.db_set("bs_march", flt(sent,2))
									from_budget_account.db_set("budget_amount", flt(total,2))
							elif from_month =="April":
								if cancel:
									sent = flt(from_budget_account.bs_april) - flt(d.amount)
									from_budget_account.db_set("bs_april", flt(sent,2))
									from_budget_account.db_set("budget_amount", flt(total,2))
								else:
									sent = flt(from_budget_account.bs_april) + flt(d.amount)
									from_budget_account.db_set("bs_april", flt(sent,2))
									from_budget_account.db_set("budget_amount", flt(total,2))
							elif from_month =="May":
								if cancel:
									sent = flt(from_budget_account.bs_may) - flt(d.amount)
									from_budget_account.db_set("bs_may", flt(sent,2))
									from_budget_account.db_set("budget_amount", flt(total,2))
								else:
									sent = flt(from_budget_account.bs_may) + flt(d.amount)
									from_budget_account.db_set("bs_may", flt(sent,2))
									from_budget_account.db_set("budget_amount", flt(total,2))
							elif from_month =="June":
								if cancel:
									sent = flt(from_budget_account.bs_june) - flt(d.amount)
									from_budget_account.db_set("bs_june", flt(sent,2))
									from_budget_account.db_set("budget_amount", flt(total,2))
								else:
									sent = flt(from_budget_account.bs_june) + flt(d.amount)
									from_budget_account.db_set("bs_june", flt(sent,2))
									from_budget_account.db_set("budget_amount", flt(total,2))
							elif from_month =="July":
								if cancel:
									sent = flt(from_budget_account.bs_july) - flt(d.amount)
									from_budget_account.db_set("bs_july", flt(sent,2))
									from_budget_account.db_set("budget_amount", flt(total,2))
								else:
									sent = flt(from_budget_account.bs_july) + flt(d.amount)
									from_budget_account.db_set("bs_july", flt(sent,2))
									from_budget_account.db_set("budget_amount", flt(total,2))
							elif from_month =="August":
								if cancel:
									sent = flt(from_budget_account.bs_aug) - flt(d.amount)
									from_budget_account.db_set("bs_aug", flt(sent,2))
									from_budget_account.db_set("budget_amount", flt(total,2))
								else:
									sent = flt(from_budget_account.bs_aug) + flt(d.amount)
									from_budget_account.db_set("bs_aug", flt(sent,2))
									from_budget_account.db_set("budget_amount", flt(total,2))
							elif from_month =="September":
								if cancel:
									sent = flt(from_budget_account.bs_sep) - flt(d.amount)
									from_budget_account.db_set("bs_sep", flt(sent,2))
									from_budget_account.db_set("budget_amount", flt(total,2))
								else:
									sent = flt(from_budget_account.bs_sep) + flt(d.amount)
									from_budget_account.db_set("bs_sep", flt(sent,2))
									from_budget_account.db_set("budget_amount", flt(total,2))
							elif from_month =="October":
								if cancel:
									sent = flt(from_budget_account.bs_oct) - flt(d.amount)
									from_budget_account.db_set("bs_oct", flt(sent,2))
									from_budget_account.db_set("budget_amount", flt(total,2))
								else:
									sent = flt(from_budget_account.bs_oct) + flt(d.amount)
									from_budget_account.db_set("bs_oct", flt(sent,2))
									from_budget_account.db_set("budget_amount", flt(total,2))
							elif from_month =="November":
								if cancel:
									sent = flt(from_budget_account.bs_nov) - flt(d.amount)
									from_budget_account.db_set("bs_nov", flt(sent,2))
									from_budget_account.db_set("budget_amount", flt(total,2))
								else:
									sent = flt(from_budget_account.bs_nov) + flt(d.amount)
									from_budget_account.db_set("bs_nov", flt(sent,2))
									from_budget_account.db_set("budget_amount", flt(total,2))
							else:
								if cancel:
									sent = flt(from_budget_account.bs_dec) - flt(d.amount)
									from_budget_account.db_set("bs_dec", flt(sent,2))
									from_budget_account.db_set("budget_amount", flt(total,2))
								else:
									sent = flt(from_budget_account.bs_dec) + flt(d.amount)
									from_budget_account.db_set("bs_dec", flt(sent,2))
									from_budget_account.db_set("budget_amount", flt(total,2))
						else:
							frappe.throw("Please Enter From Month")
					else:
						from_budget_account.db_set("budget_amount", flt(total,2))
				
				to_account = frappe.db.sql(
						"""
						select
							ba.name, ba.account from `tabBudget` b, `tabBudget Account` ba
						where
							ba.parent = b.name and b.docstatus < 2 and b.company = %s and %s=%s and
							b.fiscal_year=%s and ba.account =%s """
						% ("%s", budget_against_field, "%s", "%s", "%s"),
						(self.company, to_budget_against, self.fiscal_year, d.to_account),
						as_dict=1,
					)
				#Add in the To Account and Cost Center or project
				if to_account:
					to_budget_account = frappe.get_doc("Budget Account", to_account[0].name)
					total = flt(to_budget_account.budget_amount) + flt(d.amount)
					budget_received = flt(from_budget_account.budget_received) + flt(d.amount)
					if cancel:
						total = flt(to_budget_account.budget_amount) - flt(d.amount)
						budget_received = flt(from_budget_account.budget_received) - flt(d.amount)
					to_budget_account.db_set("budget_received", flt(budget_received,2))
					if monthly_budget_check:
						if to_month:
							if to_month =="January":
								if cancel:
									received = flt(to_budget_account.br_jan) - flt(d.amount)
									to_budget_account.db_set("br_jan", received)
									to_budget_account.db_set("budget_amount", total)
								else:
									received = flt(to_budget_account.br_jan) + flt(d.amount)
									to_budget_account.db_set("br_jan", received)
									to_budget_account.db_set("budget_amount", total)
							elif to_month =="Februery":
								if cancel:
									received = flt(to_budget_account.br_feb) - flt(d.amount)
									to_budget_account.db_set("br_feb", received)
									to_budget_account.db_set("budget_amount", total)
								else:
									received = flt(to_budget_account.br_feb) + flt(d.amount)
									to_budget_account.db_set("br_feb", received)
									to_budget_account.db_set("budget_amount", total)
							elif to_month =="March":
								if cancel:
									received = flt(to_budget_account.br_march) - flt(d.amount)
									to_budget_account.db_set("br_march", received)
									to_budget_account.db_set("budget_amount", total)
								else:
									received = flt(to_budget_account.br_march) + flt(d.amount)
									to_budget_account.db_set("br_march", received)
									to_budget_account.db_set("budget_amount", total)
							elif to_month =="April":
								if cancel:
									received = flt(to_budget_account.br_april) - flt(d.amount)
									to_budget_account.db_set("br_april", received)
									to_budget_account.db_set("budget_amount", total)
								else:
									received = flt(to_budget_account.br_april) + flt(d.amount)
									to_budget_account.db_set("br_april", received)
									to_budget_account.db_set("budget_amount", total)
							elif to_month =="May":
								if cancel:
									received = flt(to_budget_account.br_may) - flt(d.amount)
									to_budget_account.db_set("br_may", received)
									to_budget_account.db_set("budget_amount", total)
								else:
									received = flt(to_budget_account.br_may) + flt(d.amount)
									to_budget_account.db_set("br_may", received)
									to_budget_account.db_set("budget_amount", total)
							elif to_month =="June":
								if cancel:
									received = flt(to_budget_account.br_june) - flt(d.amount)
									to_budget_account.db_set("br_june", received)
									to_budget_account.db_set("budget_amount", total)
								else:
									received = flt(to_budget_account.br_june) + flt(d.amount)
									to_budget_account.db_set("br_june", received)
									to_budget_account.db_set("budget_amount", total)
							elif to_month =="July":
								if cancel:
									received = flt(to_budget_account.br_july) - flt(d.amount)
									to_budget_account.db_set("br_july", received)
									to_budget_account.db_set("budget_amount", total)
								else:
									received = flt(to_budget_account.br_july) + flt(d.amount)
									to_budget_account.db_set("br_july", received)
									to_budget_account.db_set("budget_amount", total)
							elif to_month =="August":
								if cancel:
									received = flt(to_budget_account.br_aug) - flt(d.amount)
									to_budget_account.db_set("br_aug", received)
									to_budget_account.db_set("budget_amount", total)
								else:
									received = flt(to_budget_account.br_aug) + flt(d.amount)
									to_budget_account.db_set("br_aug", received)
									to_budget_account.db_set("budget_amount", total)
							elif to_month =="September":
								if cancel:
									received = flt(to_budget_account.br_sep) - flt(d.amount)
									to_budget_account.db_set("br_sep", received)
									to_budget_account.db_set("budget_amount", total)
								else:
									received = flt(to_budget_account.br_sep) + flt(d.amount)
									to_budget_account.db_set("br_sep", received)
									to_budget_account.db_set("budget_amount", total)
							elif to_month =="October":
								if cancel:
									received = flt(to_budget_account.br_oct) - flt(d.amount)
									to_budget_account.db_set("br_oct", received)
									to_budget_account.db_set("budget_amount", total)
								else:
									received = flt(to_budget_account.br_oct) + flt(d.amount)
									to_budget_account.db_set("br_oct", received)
									to_budget_account.db_set("budget_amount", total)
							elif to_month =="November":
								if cancel:
									received = flt(to_budget_account.br_nov) - flt(d.amount)
									to_budget_account.db_set("br_nov", received)
									to_budget_account.db_set("budget_amount", total)
								else:
									received = flt(to_budget_account.br_nov) + flt(d.amount)
									to_budget_account.db_set("br_nov", received)
									to_budget_account.db_set("budget_amount", total)
							else:
								if cancel:
									received = flt(to_budget_account.br_dec) - flt(d.amount)
									to_budget_account.db_set("br_dec", received)
									to_budget_account.db_set("budget_amount", total)
								else:
									received = flt(to_budget_account.br_dec) + flt(d.amount)
									to_budget_account.db_set("br_dec", received)
									to_budget_account.db_set("budget_amount", total)
						else:
							frappe.throw("Please Enter To Month")
					else:
						to_budget_account.db_set("budget_amount", total)


				app_details = frappe.new_doc("Reappropriation Details")
				app_details.flags.ignore_permissions = 1
				app_details.budget_against = self.budget_against
				app_details.from_cost_center = self.from_cost_center if self.budget_against == "Cost Center" else ""
				app_details.to_cost_center = self.to_cost_center if self.budget_against == "Cost Center" else ""
				app_details.from_account = d.from_account
				app_details.to_account = d.to_account
				app_details.from_project = self.from_project if self.budget_against == "Project" else ""
				app_details.to_project = self.to_project if self.budget_against == "Project" else ""
				app_details.amount =flt(d.amount,2)
				app_details.posting_date = nowdate()
				app_details.reference = self.name
				app_details.from_month = from_month if from_month else ""
				app_details.to_month = to_month if to_month else ""
				app_details.company = self.company
				app_details.submit()

			#Delete the reappropriation details for record
			# frappe.throw("HHHH")
			if cancel:
				frappe.db.sql("delete from `tabReappropriation Details` where reference=%s", self.name)

def get_permission_query_conditions(user):
	if not user: user = frappe.session.user
	user_roles = frappe.get_roles(user)

	if user == "Administrator":
		return
	if "Budget Manager" in user_roles or "GM" in user_roles or "CEO" in user_roles:
		return

	return """(
		`tabBudget Reappropiation`.owner = '{user}'
		or
		(`tabBudget Reappropiation`.approver = '{user}' and `tabBudget Reappropiation`.workflow_state not in  ('Draft','Approved','Rejected','Cancelled'))
	)""".format(user=user)
