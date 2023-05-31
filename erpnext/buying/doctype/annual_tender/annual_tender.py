# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class AnnualTender(Document):
	def before_save(self):
		self.price_list = ""

	def on_submit(self):
		doc = frappe.new_doc("Price List")
		doc.flags.ignore_permissions = 1
		doc.price_list_name = "Annual Tender " + str(self.fiscal_year) + "(" + str(self.supplier) + ")"
		start, end = frappe.db.get_value("Fiscal Year", self.fiscal_year, ["year_start_date", "year_end_date"])
		doc.price_valid_from = start
		doc.price_valid_to = end
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
			ip.save()
	
	def on_cancel(self):
		frappe.db.sql("delete from `tabPrice List` where name = \'" + str(self.price_list) + "\'")
		frappe.db.sql("delete from `tabItem Price` where price_list = \'" + str(self.price_list) + "\'")

