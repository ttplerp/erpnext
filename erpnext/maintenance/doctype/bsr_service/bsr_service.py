# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.naming import make_autoname

class BSRService(Document):
	def autoname(self):
		bsr_code = "BSR-" + str(self.fiscal_year) + '-.###'
		self.name = make_autoname(bsr_code)

	def validate(self):
		if not self.valid_from:
			start, end = frappe.db.get_value("Fiscal Year", self.fiscal_year, ["year_start_date", "year_end_date"])
			self.valid_from = start
			# self.valid_upto = end

	def before_save(self):
		self.price_list = ""

	def on_submit(self):
		doc = frappe.new_doc("Price List")
		doc.flags.ignore_permissions = 1
		doc.price_list_name = "BSR " + str(self.fiscal_year) +" "+ str(self.region)
		doc.currency = self.currency
		doc.buying = 1
		doc.enabled = 1
		doc.save()
		self.db_set("price_list", doc.name)

		for a in self.items:
			ip = frappe.new_doc("Item Price")
			ip.flags.ignore_permissions = 1
			ip.price_list = doc.name
			ip.item_code = a.item
			ip.price_list_rate = a.rate
			# start, end = frappe.db.get_value("Fiscal Year", self.fiscal_year, ["year_start_date", "year_end_date"])
			ip.valid_from = self.valid_from
			ip.valid_upto = self.valid_upto
			ip.save()
	
	def on_cancel(self):
		frappe.db.sql("delete from `tabPrice List` where name = \'" + str(self.price_list) + "\'")
		frappe.db.sql("delete from `tabItem Price` where price_list = \'" + str(self.price_list) + "\'")
