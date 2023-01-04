# Copyright (c) 2017, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt


import frappe
from email_reply_parser import EmailReplyParser
from frappe import _
from frappe.desk.reportview import get_match_cond
from frappe.model.document import Document
from frappe.utils import add_days, flt, get_datetime, get_time, get_url, nowtime, today, getdate, get_last_day

from erpnext import get_default_company
from erpnext.controllers.employee_boarding_controller import update_employee_boarding_status
from erpnext.controllers.queries import get_filters_cond
from erpnext.setup.doctype.holiday_list.holiday_list import is_holiday

import frappe, json
from frappe.model.mapper import get_mapped_doc
import datetime
from frappe.model.naming import make_autoname
from erpnext.custom_utils import get_branch_cc
from erpnext.accounts.general_ledger import make_gl_entries, merge_similar_entries
from erpnext.controllers.accounts_controller import AccountsController
class Project(AccountsController):
	def autoname(self):
		self.name = make_autoname("PRJ.-.YY.-.###")

	# def get_feed(self):
	# 	return "{0}: {1}".format(_(self.status), frappe.safe_decode(self.project_name))

	def validate(self):
		self.validate_dates()
		self.validate_branch_cc()
		self.cancelled_status()

	# def on_cancel(self):
	#     if self.status == 'Capitalized':
	#         frappe.throw("This Project is Capitalized, cannot performed Cancel")
	#     if self.settlement == 1:
	#         self.monthly_settlement()

	def validate_dates(self):
		if self.start_date and self.end_date:
			if getdate(self.end_date) < getdate(self.start_date):
				frappe.throw(_("End Date can not be less than Start Date"))
	
	def validate_branch_cc(self):
		if self.cost_center != get_branch_cc(self.branch):
			frappe.throw("Project\'s branch and cost center doesn't belong to each other")
			
	def cancelled_status(self):
		if self.status == 'Cancelled':
			self.docstatus = {
					"Created": 0,
					"Cancelled": 2
			}[str(self.status) or "Created"]

			self.monthly_settlement()

	def update_purchase_costing(self):
	   total_purchase_cost = frappe.db.sql("""select sum(base_net_amount) from `tabPurchase Invoice Item` where project = %s and docstatus=1""", self.name)
	
	def capitalize_project_process(self, item_code, item_name, account):
		# frappe.throw(str(self.cost_center))
		if self.status == 'Capitalized':
			frappe.throw(_("This Project Already Capitalized"))
		
		self.capitalized_date = utils.today()
		next_depreciation_date = get_last_day(self.capitalized_date)
		asset_sub_cat = frappe.db.get_value("Item", item_code, "asset_sub_category")
		total_number_of_depreciations = frappe.db.get_value("Asset Sub Category", asset_sub_cat, "total_number_of_depreciations")
		depreciation_percent = frappe.db.get_value("Asset Sub Category", asset_sub_cat, "depreciation_percent")
		# 1 Post GL Entry
		# self.post_gl_entry(account) # no need by Deki
		cwip_accounts = [d[0] for d in frappe.db.sql("""select name from tabAccount where account_type = 'Capital Work in Progress' and is_group=0""")]
		# 2 Make Draft Asset
		asset = frappe.get_doc({
			"doctype": "Asset",
			"asset_name": item_name,
			"item_code": item_code,
			"purchase_date": frappe.utils.nowdate(),
			"asset_account": account,
			"credit_account": cwip_accounts[0],
			"cost_center": self.cost_center,
			"asset_rate": self.total_overall_project_cost,
			"gross_purchase_amount": self.total_overall_project_cost,
			"branch": self.branch,
			"next_depreciation_date": next_depreciation_date,
			"reference": self.name,
			"reference_type": 'Project',
			"posting_date": self.capitalized_date,
			"total_number_of_depreciations": total_number_of_depreciations,
			"asset_depreciation_percent": depreciation_percent,
		})
		asset.insert()
		# 3 Update posting date and capitalize check value
		doc = frappe.get_doc("Project", self.name)
		doc.capitalized_date = self.capitalized_date
		doc.status = 'Capitalized'
		doc.docstatus = 1
		doc.save(ignore_permissions = True)

		return 'done'
					
	def post_gl_entry(self, account):
		gl_entries = []
		cwip_accounts = [d[0] for d in frappe.db.sql("""select name from tabAccount where account_type = 'Capital Work in Progress' and is_group=0""")]
		gl_entries.append(
			self.get_gl_dict({
				"account": cwip_accounts[0],
				"against": account,
				"credit": self.total_overall_project_cost,
				"credit_in_account_currency": self.total_overall_project_cost,
				"voucher_no": self.name,
				"project": self.name,
				"voucher_type": self.doctype,
				"cost_center": self.cost_center,
				"business_activity": self.business_activity
				})
			)
		gl_entries.append(
			self.get_gl_dict({
				"account": account,
				"against": cwip_accounts[0],
				"debit": self.total_overall_project_cost,
				"debit_in_account_currency": self.total_overall_project_cost,
				"voucher_no": self.name,
				"project": self.name,
				"voucher_type": self.doctype,
				"cost_center": self.cost_center,
				"business_activity": self.business_activity
				})
			)

		make_gl_entries(gl_entries, cancel=(self.docstatus == 2), update_outstanding="No", merge_entries=False)

	def monthly_settlement(self):
		if not self.total_overall_project_cost:
			return

		self.posting_date = utils.today()
		clearing_account = [d[0] for d in frappe.db.sql("""select name from tabAccount where account_type = 'Temporary Account' and is_group=0 and name like '%Clearing%' """)]
		# account = frappe.db.get_value("Company", self.company, "default_inventory_account")
		# pr_amount = 0
		# for i in frappe.db.sql("""select sum(amount) as sum_amount from `tabPurchase Receipt Item` where project = '{}' and docstatus = 1 """.format(self.name), as_dict=True):
		#     pr_amount += i.sum_amount

		gl_entries = []
		cwip_accounts = [d[0] for d in frappe.db.sql("""select name from tabAccount where account_type = 'Capital Work in Progress' and is_group=0""")]
		gl_entries.append(
			self.get_gl_dict({
				"account": clearing_account[0],
				"against": cwip_accounts[0],
				"credit": self.total_overall_project_cost,
				"credit_in_account_currency": self.total_overall_project_cost,
				"voucher_no": self.name,
				"project": self.name,
				"voucher_type": self.doctype,
				"cost_center": self.cost_center,
				"business_activity": self.business_activity,
				"posting_date": self.posting_date
				})
			)
		gl_entries.append(
			self.get_gl_dict({
				"account": cwip_accounts[0],
				"against": clearing_account[0],
				"debit": self.total_overall_project_cost,
				"debit_in_account_currency": self.total_overall_project_cost,
				"voucher_no": self.name,
				"project": self.name,
				"voucher_type": self.doctype,
				"cost_center": self.cost_center,
				"business_activity": self.business_activity,
				"posting_date": self.posting_date
				})
			)

		make_gl_entries(gl_entries, cancel=(self.docstatus == 2), update_outstanding="No", merge_entries=False)

		doc = frappe.get_doc("Project", self.name)
		if self.status == 'Cancelled':
			doc.settlement = '0'
		else:
			doc.settlement = '1'
			doc.posting_date = self.posting_date
		doc.save(ignore_permissions = True)

		if self.docstatus != 2:
			frappe.msgprint("Settlement Done", title='Notice')
			# frappe.reload_doctype("Project")
		self.reload()
		return 1

# @frappe.whitelist()
# def get_project_cost(project_definition):
# 	project_names = frappe.db.sql("select site_name as name from `tabOngoing Project Item` where parent='{}'".format(project_definition),as_dict=1)
# 	for item in project_names:
# 		total_cost = frappe.db.sql("select total_cost from `tabProject` where name='{}'".format(item.name),as_dict=1)
# 		frappe.db.sql("update `tabOngoing Project Item` set total_cost={} where parent='{}' and site_name='{}'".format(total_cost[0].total_cost, project_definition, item.name))

# added by Jai,
# @frappe.whitelist()
	
# added by Jai,
@frappe.whitelist()
def get_item_expense_account(item_code):
	return frappe.db.sql(""" Select id.expense_account expense_account, i.item_name item_name 
				From `tabItem` i 
				Inner Join `tabItem Default` id on i.name = id.parent 
				where i.name = '{}'""".format(item_code), as_dict=True)

# Following code added by SHIV on 2021/05/13
def get_permission_query_conditions(user):
	if not user: user = frappe.session.user
	user_roles = frappe.get_roles(user)

	if user == "Administrator" or "System Manager" in user_roles: 
		return

	return """(
		exists(select 1
			from `tabEmployee` as e
			where e.branch = `tabProject`.branch
			and e.user_id = '{user}')
		or
		exists(select 1
			from `tabEmployee` e, `tabAssign Branch` ab, `tabBranch Item` bi
			where e.user_id = '{user}'
			and ab.employee = e.name
			and bi.parent = ab.name
			and bi.branch = `tabProject`.branch)
	)""".format(user=user)

@frappe.whitelist()
def get_cost_center(doctype, txt, searchfield, start, page_len, filters):
	cond = ''
	
	return frappe.db.sql(""" select name 
			from `tabCost Center` 
			where name not in (select cost_center from `tabProject` where status = 'Capitalized') and company = %s and is_group = %s """,(filters.get("company"),filters.get("is_group")))
