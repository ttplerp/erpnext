# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from frappe.utils import flt, getdate, get_url, today

class RevenueTarget(Document):
	def validate(self):
		self.validate_mandatory()
		self.calculate_targets()
		self.validate_accounts()
		self.set_initial_revenue_target()
	
	def validate_accounts(self):
		account_list = []
		for d in self.get("revenue_target_account"):
			if d.account:
				account_details = frappe.db.get_value(
					"Account", d.account, ["is_group", "company", "report_type"], as_dict=1
				)

				if account_details.is_group:
					frappe.msgprint(_("Revenue Target cannot be assigned against Group Account {0}").format(d.account), raise_exception=True)
				elif account_details.company != self.company:
					frappe.msgprint(_("Account {0} does not belongs to company {1}").format(d.account, self.company), raise_exception=True)
				if d.account in account_list:
					frappe.msgprint(_("Account {0} has been entered multiple times").format(d.account), raise_exception=True)
				else:
					account_list.append(d.account)

	def validate_mandatory(self):
		for item in self.revenue_target_account:
			if flt(item.target_amount) < 0.0:
				frappe.throw(_("Row#{0}: Target Amount cannot be a negative value.").format(item.idx), title="Invalid Value")

			if frappe.db.get_value("Account", item.account, "root_type") != "Income":
				frappe.throw(_("Row#{0}: `{1}` is not an Income GL.").format(item.idx, item.account), title="Invalid GL")

			if not item.account_number:
				item.account_number = frappe.db.get_value("Account", item.account, "account_number")
	
	def calculate_targets(self):
		tot_target_amount     = 0.0

		for d in self.revenue_target_account:
			# d.net_target_amount = flt(d.target_amount)
			tot_target_amount += flt(d.target_amount)

		self.tot_target_amount     = tot_target_amount
		# self.tot_net_target_amount = flt(tot_target_amount)
	
	@frappe.whitelist()
	def get_accounts(self):
		query = "select name as account, account_number from `tabAccount` where account_type in (\'Income Account\') and is_group = 0 and company = \'" + str(self.company) + "\' and (freeze_account is null or freeze_account != 'Yes') and disabled=0"
		entries = frappe.db.sql(query, as_dict=True)
		self.set('revenue_target_account', [])

		for d in entries:
			row = self.append('revenue_target_account', {})
			row.update(d)
	
	@frappe.whitelist()
	def set_initial_revenue_target(self):
		total_target = 0
		for d in self.revenue_target_account:
			initial_target = flt(d.january) + flt(d.february) + flt(d.march) + flt(d.april)+ flt(d.may) +flt(d.june) +flt(d.july) +flt(d.august) + flt(d.september) +flt(d.october) +flt(d.november) +flt(d.december)
			total_target += flt(initial_target)
			d.db_set("target_amount", initial_target)
			self.db_set("tot_target_amount", total_target)

