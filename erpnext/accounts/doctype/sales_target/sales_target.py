# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import (
	add_days,
	add_months,
	get_first_day,
	get_last_day,
	get_year_ending,
	get_year_start,
	getdate,
	nowdate,
	flt,
	rounded,
)
from erpnext.accounts.accounts_custom_functions import get_child_cost_centers,get_period_date

class SalesTarget(Document):
	def validate(self):
		self.calculate_total_qty()
		self.validate_duplicate()

	def validate_duplicate(self):
		if frappe.db.exists(self.doctype,{"name":("!=",self.name),"fiscal_year":self.fiscal_year,"item_sub_group":self.item_sub_group,"docstatus":("!=",2)}):
			frappe.throw("Target already exists against {}".format(frappe.bold(self.item_sub_group)))
	def calculate_total_qty(self):
		total_qty = 0
		for t in self.targets:
			total_qty += flt(t.target_qty)
		self.total_target_qty = total_qty
	@frappe.whitelist()
	def get_months(self):
		months = frappe.db.sql("SELECT month, month_no,'MT' as uom, 0 as target_qty FROM `tabMonth` order by month_no",as_dict=True)
		for d in months:
			date = getdate(self.fiscal_year+'-'+d.month_no+'-01')
			d.update({
				"from_date":get_first_day(date),
				"to_date":get_last_day(date)
			})
		return months

	@frappe.whitelist()
	def get_item(self):
		if not self.item_sub_group:
			frappe.throw("Item sub group is required")
		return frappe.db.sql("SELECT name as item_code, item_name, item_group, item_sub_group FROM `tabItem` WHERE item_sub_group = '{}'".format(self.item_sub_group), as_dict=True)