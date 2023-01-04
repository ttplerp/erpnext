# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt, cint, getdate, get_datetime, get_url, nowdate, now_datetime, money_in_words, formatdate
from erpnext.accounts.general_ledger import make_gl_entries
from frappe import _
from erpnext.controllers.accounts_controller import AccountsController
from erpnext.custom_utils import check_future_date
import json
from erpnext.accounts.doctype.accounts_settings.accounts_settings import get_bank_account as get_bank_account_accounts
# from erpnext.accounts.doctype.hr_accounts_settings.hr_accounts_settings import get_bank_account as get_bank_account_hr
from frappe.model.naming import make_autoname

class DirectPayment(AccountsController):
	# Added by Jai, 2 June, 2022
	def autoname(self):
		year = formatdate(self.posting_date, "YY")
		month = formatdate(self.posting_date, "MM")
		self.name = make_autoname(str("DPAY") + '.{}.{}.###'.format(year, month))
  
	def validate(self):
		check_future_date(self.posting_date)
		self.validate_data()
		self.clearance_date = None
		self.validate_tds_account()
		# self.validate_party()
		self.salary_advance()
		self.validate_project()
		
	def salary_advance(self):
		if self.party_type == "":
			self.party_type = "Employee"

	def on_submit(self):
		self.post_gl_entry()
		self.consume_budget()
		self.update_project_transaction_details() #added by Jai
		
	def validate_party(self):
		for a in self.item:
			account_type = frappe.db.get_value("Account", a.account, "account_type") or ""
			if account_type in ["Receivable", "Payable", "Expense Account"]:
				if not a.party:
					frappe.msgprint("Party is Mandatory for account head {} with account type {}".format(a.account, account_type))
		
			# TDS not applicable for party type employee
			if a.party_type == "Employee" and a.tds_amount > 0:
				frappe.throw("TDS is not applicable for party type employee")

	def validate_project(self):
		for i in self.item:
			if i.project and not self.docstatus == 2:
				project_capitalize = frappe.db.get_value("Project", i.project, "status")
				if project_capitalize == 'Capitalized':
					frappe.throw(_("This {} Project is already Capitalized".format(i.project)))
			elif i.project and self.docstatus == 2:
				project_capitalize = frappe.db.get_value("Project", i.project, "status")
				if project_capitalize == 'Capitalized':
					frappe.throw(_("This {} is Linked to the Project {}".format(self.name, i.project)))
					
	def before_cancel(self):
		pass

	def on_cancel(self):
		if self.clearance_date:
			frappe.throw("Already done bank reconciliation.")
		self.post_gl_entry()
		self.cancel_budget_entry()
		self.update_project_transaction_details() #added by Jai

	def validate_data(self):
		tds_amt = gross_amt = net_amt = taxable_amt = 0.00
		for a in self.item:
			if self.payment_type == "Receive":
				inter_company = frappe.db.get_value(
					"Customer", self.party, "inter_company")
				if inter_company == 0:
					frappe.throw(
						_("Selected Customer {0} is not inter company ".format(self.party)))

			if self.payment_type == "Payment" and a.party_type == "Customer":
				frappe.throw(
					_("Party Type should be Supplier in Child table when Payment Type is Payment"))
			elif self.payment_type == "Receive" and a.party_type == "Supplier":
				frappe.throw(
					_("Party Type should be Customer in Child Table when Payment Type is Receive"))
			if a.tds_applicable:
				if not self.tds_percent:
					frappe.throw("Select TDS Percent for tds deduction")
				if self.tds_percent and cint(self.tds_percent) > 0:
					a.tds_amount = flt(a.taxable_amount) * \
						flt(self.tds_percent) / 100
			else:
				a.tds_amount = 0.00

			a.net_amount = flt(a.amount) - flt(a.tds_amount)
			tds_amt += flt(a.tds_amount)
			gross_amt += flt(a.amount)
			net_amt += flt(a.net_amount)
			taxable_amt += flt(a.taxable_amount)

		self.tds_amount = tds_amt
		self.gross_amount = gross_amt
		self.amount = gross_amt
		self.net_amount = net_amt
		self.taxable_amount = taxable_amt

	##
	# Update the Committedd Budget for checking budget availability
	##
	def consume_budget(self):
		if self.payment_type == "Payment":
			for a in self.item:
				bud_obj = frappe.get_doc({
					"doctype": "Committed Budget",
					"account": a.account,
					"cost_center": a.cost_center,
					"po_no": self.name,
					"po_date": self.posting_date,
					"amount": a.amount,
					"poi_name": self.name,
					"date": frappe.utils.nowdate()
				})
				bud_obj.flags.ignore_permissions = 1
				bud_obj.submit()

				consume = frappe.get_doc({
					"doctype": "Consumed Budget",
					"account": a.account,
					"cost_center": a.cost_center,
					"po_no": self.name,
					"po_date": self.posting_date,
					"amount": a.amount,
					"pii_name": self.name,
					"com_ref": bud_obj.name,
					"date": frappe.utils.nowdate()})
				consume.flags.ignore_permissions = 1
				consume.submit()
	##
	# Cancel budget check entry
	##
	def cancel_budget_entry(self):
		frappe.db.sql(
			"delete from `tabCommitted Budget` where po_no = %s", self.name)
		frappe.db.sql(
			"delete from `tabConsumed Budget` where po_no = %s", self.name)
		
	def add_bank_gl_entries(self, gl_entries):
		party = party_type = None

		''' CBS Integration Begins'''
		partylist_json = {}
		if frappe.db.exists('Company', {'cbs_enabled': 1}) and not (self.cheque_no or self.cheque_date):
			for a in self.item:
				if a.party_type and a.party:
					partylist_json.setdefault(a.party_type, []).append({"party_type": a.party_type, "party": a.party, "amount": flt(a.net_amount)})
		''' CBS Integration Ends'''
		
		if self.payment_type == "Receive":
			account_type = frappe.db.get_value("Account", self.debit_account, "account_type") or ""
			if account_type in ["Receivable", "Payable"]:
				party = self.party
				party_type = self.party_type
			gl_entries.append(
				self.get_gl_dict({
					"account": self.debit_account,
					"debit": self.net_amount,
					"debit_in_account_currency": self.net_amount,
					"voucher_no": self.name,
					"voucher_type": self.doctype,
					"cost_center": self.cost_center,
					"party_type": party_type,
					"party": party,
					"company": self.company,
					"remarks": self.remarks,
					"business_activity": self.business_activity,
					"use_check_lot": self.use_check_lot,
					"select_cheque_lot": self.select_cheque_lot,
					"cheque_no": self.cheque_no,
					"cheque_date": self.cheque_date,
					"pay_to_recd_from": self.pay_to_recd_from
					})
				)
		else:
			account_type = frappe.db.get_value("Account", self.credit_account, "account_type") or ""
			if account_type in ["Receivable", "Payable"]:
				party = self.party
				party_type = self.party_type
			gl_entries.append(
				self.get_gl_dict({
					"account": self.credit_account,
					"credit": self.net_amount,
					"credit_in_account_currency": self.net_amount,
					"voucher_no": self.name,
					"voucher_type": self.doctype,
					"cost_center": self.cost_center,
					"party_type": party_type,
					"party": party,
					"company": self.company,
					"remarks": self.remarks,
					"business_activity": self.business_activity,
					"partylist_json": json.dumps(partylist_json),
					"use_check_lot": self.use_check_lot,
					"select_cheque_lot": self.select_cheque_lot,
					"cheque_no": self.cheque_no,
					"cheque_date": self.cheque_date,
					"pay_to_recd_from": self.pay_to_recd_from
					})
				)
	
	def add_party_gl_entries(self, gl_entries):
		for a in self.item:
			party = party_type = None
			account_type = frappe.db.get_value("Account", a.account, "account_type") or ""
			if account_type in ["Receivable", "Payable"]:
				party = a.party
				party_type = a.party_type
			if self.payment_type == "Receive":
				gl_entries.append(
					self.get_gl_dict({
						"account": a.account,
						"credit": a.amount,
						"credit_in_account_currency": a.amount,
						"voucher_no": self.name,
						"voucher_type": self.doctype,
						"cost_center": a.cost_center,
						'party': party,
						'party_type': party_type,						
						"company": self.company,
						"remarks": self.remarks,
						"business_activity": self.business_activity,
						"use_check_lot": self.use_check_lot,
						"select_cheque_lot": self.select_cheque_lot,
						"cheque_no": self.cheque_no,
						"cheque_date": self.cheque_date,
						"pay_to_recd_from": self.pay_to_recd_from
						})
					)
			else:
				gl_entries.append(
					self.get_gl_dict({
						"account": a.account,
						"debit": a.amount,
						"debit_in_account_currency": a.amount,
						"voucher_no": self.name,
						"voucher_type": self.doctype,
						"cost_center": a.cost_center,
						'party': party,
						'party_type': party_type,						
						"company": self.company,
						"remarks": self.remarks,
						"business_activity": self.business_activity,
						"use_check_lot": self.use_check_lot,
						"select_cheque_lot": self.select_cheque_lot,
						"cheque_no": self.cheque_no,
						"cheque_date": self.cheque_date,
						"pay_to_recd_from": self.pay_to_recd_from
						})
					)             
	def add_tds_gl_entries(self, gl_entries):
		if flt(self.tds_amount) > 0:
			if self.payment_type == "Received":
				gl_entries.append(
					self.get_gl_dict({
						"account": self.tds_account,
						"debit": self.tds_amount,
						"debit_in_account_currency": self.tds_amount,
						"voucher_no": self.name,
						"voucher_type": self.doctype,
						"cost_center": self.cost_center,
						"company": self.company,
						"remarks": self.remarks,
						"business_activity": self.business_activity,
						"use_check_lot": self.use_check_lot,
						"select_cheque_lot": self.select_cheque_lot,
						"cheque_no": self.cheque_no,
						"cheque_date": self.cheque_date,
						"pay_to_recd_from": self.pay_to_recd_from
						})
					)
			else:
				gl_entries.append(
					self.get_gl_dict({
						"account": self.tds_account,
						"credit": self.tds_amount,
						"credit_in_account_currency": self.tds_amount,
						"voucher_no": self.name,
						"voucher_type": self.doctype,
						"cost_center": self.cost_center,
						"company": self.company,
						"remarks": self.remarks,
						"business_activity": self.business_activity,
						"use_check_lot": self.use_check_lot,
						"select_cheque_lot": self.select_cheque_lot,
						"cheque_no": self.cheque_no,
						"cheque_date": self.cheque_date,
						"pay_to_recd_from": self.pay_to_recd_from
						})
					)
				
	def post_gl_entry(self):
		gl_entries = []
		self.add_party_gl_entries(gl_entries)
		self.add_bank_gl_entries(gl_entries)
		self.add_tds_gl_entries(gl_entries)
		make_gl_entries(gl_entries, cancel=(self.docstatus == 2),
						update_outstanding="No", merge_entries=False)
		# if direct payment linked with amc work order following code will execute
		amc_wo = frappe.db.sql("""
							select name from `tabAMC Work Order` where payment_status = "Pending Payment" and direct_payment = '{0}'   
		""".format(self.name), as_dict = True)
		if amc_wo:
			wo = frappe.get_doc("AMC Work Order", amc_wo[0].name)
			wo.payment_status = "Paid"
			wo.save()
	
	def validate_tds_account(self):
		if not self.tds_account and self.tds_percent:
			self.tds_account = get_tds_account(self.tds_percent, payment_type ="Payment")
			
	def update_project_transaction_details(self):
		for i in self.item:
			if i.project and not self.docstatus == 2:
				project_capitalize = frappe.db.get_value("Project", i.project, "status")
				if project_capitalize == 'Capitalized':
					frappe.throw(_("This {} is already Capitalized".format(i.project)))

				total_overall_project_cost = frappe.db.get_value("Project", i.project, "total_overall_project_cost")
				doc = frappe.get_doc("Project", i.project)
				doc.append("transaction_details", {
					"posting_date": self.posting_date,
					"invoice_no": self.name,
					"amount": i.amount
				})
				total_overall_project_cost += i.amount
				doc.total_overall_project_cost = total_overall_project_cost
				doc.save(ignore_permissions = True)
			elif i.project and self.docstatus == 2:
				project_capitalize = frappe.db.get_value("Project", i.project, "status")
				if project_capitalize == 'Capitalized':
					frappe.throw(_("This {} is Linked to the Project {}".format(self.name, i.project)))

				total_overall_project_cost = frappe.db.get_value("Project", i.project, "total_overall_project_cost")
				doc = frappe.get_doc("Project", i.project)
				total_overall_project_cost -= i.amount
				doc.total_overall_project_cost = total_overall_project_cost
				doc.save(ignore_permissions = True)

				frappe.db.sql(""" delete from `tabTransaction Details` where invoice_no = %s """, self.name)

@frappe.whitelist()
def get_tds_account(percent, payment_type):
	if payment_type == "Payment":
		if percent:
			if cint(percent) == 2:
				field = "tds_2_account"
			elif cint(percent) == 3:
				field = "tds_3_account"
			elif cint(percent) == 5:
				field = "tds_5_account"
			elif cint(percent) == 10:
				field = "tds_10_account"
			else:
				frappe.throw(
					"Set TDS Accounts in Accounts Settings and try again")
			return frappe.db.get_single_value("Accounts Settings", field)

	elif payment_type == "Receive":
		if percent:
			field = "tds_deducted"
			return frappe.db.get_single_value("Accounts Settings", field)

# Following code added by SHIV on 2021/05/13
def get_permission_query_conditions(user):
	if not user: user = frappe.session.user
	user_roles = frappe.get_roles(user)

	if user == "Administrator" or "System Manager" in user_roles: 
		return

	return """(
		exists(select 1
			from `tabEmployee` as e
			where e.branch = `tabDirect Payment`.branch
			and e.user_id = '{user}')
		or
		exists(select 1
			from `tabEmployee` e, `tabAssign Branch` ab, `tabBranch Item` bi
			where e.user_id = '{user}'
			and ab.employee = e.name
			and bi.parent = ab.name
			and bi.branch = `tabDirect Payment`.branch)
	)""".format(user=user)

@frappe.whitelist()
def get_salary_advance(doctype, txt, searchfield, start, page_len, filters):
	data = frappe.db.sql("select c.party, (select b.employee_name from `tabEmployee` b where b.name = c.party) from `tabJournal Entry` a, `tabJournal Entry Account` c where a.name=c.parent and c.party_type = '{}' and c.account = '{}' and a.docstatus = 1".format(filters.get("party_type"), filters.get("account")))
	return data




# def get_salary_advance(doctype, txt, searchfield, start, page_len,filters):
#     data = frappe.db.sql("select e.employee,e.employee_name from `tabSalary Advance` sa, `tabEmployee` e where sa.employee = e.name and sa.docstatus=1")
#     return data

@frappe.whitelist()
def get_credit_account(doctype=None, txt=None, searchfield=None, start=None, page_len=None, filters=None):
	cond = ""
	# commented by Jai, 6 Jun, 2022
	# if filters.get("payment_type") == "Payment":
	# 	expense_bank_account = []
	# 	expense_bank_account_accounts = get_bank_account_accounts(filters.get('branch'))
	# 	expense_bank_account_hr = get_bank_account_hr(filters.get('branch'))
	# 	if filters.get('party_types'):
	# 		for party_type in filters.get('party_types'):
	# 			if party_type == 'Employee':
	# 				expense_bank_account.append(expense_bank_account_hr)
	# 			elif party_type:
	# 				expense_bank_account.append(expense_bank_account_accounts)

	# 	if not expense_bank_account:
	# 		expense_bank_account.append(expense_bank_account_accounts)
	# 		expense_bank_account.append(expense_bank_account_hr)

	# 	if len(set(expense_bank_account)) == 1:
	# 		cond = "and name  = '%s'" % expense_bank_account[0]
	# 	else:
	# 		cond = "and name in {}".format(tuple(["%s"]*len(set(expense_bank_account)))) % tuple(set(expense_bank_account))
	# else:
	# 	if filters.get("payment_type") == "Receive":
	# 		cond = "and account_type in ('Receivable')"
	# 	else:
	# 		cond = "and account_type in ('Bank', 'Cash', 'Payable', 'Receivable')"
	if filters.get("payment_type") == "Receive":
		cond = "and account_type in ('Receivable')"
	else:
		cond = "and account_type in ('Bank', 'Cash', 'Payable', 'Receivable')"

	return frappe.db.sql("""select name from `tabAccount`
				where `{key}` LIKE %(txt)s {cond}
				order by name limit %(start)s, %(page_len)s"""
				.format(key=searchfield, cond=cond), {
					'txt': '%' + txt + '%',
					'start': start, 'page_len': page_len
				})
