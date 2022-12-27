# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt, cint

class ProductionSettings(Document):
	def validate(self):
		self.check_percent_total()
		self.check_duplicate()

	def check_percent_total(self):
		total_percent = 0
		for a in self.item:
			total_percent += a.ratio
			
		if cint(total_percent) > 100:
			frappe.throw("Total percent is {}. It should not be more than 100".format(total_percent))

	def check_duplicate(self):
		condition = ""
		if self.warehouse:
			condition += " and warehouse = '" + str(self.warehouse) + "'"

		if self.item_type:
			condition += " and item_type = '" + str(self.item_type) + "'"

		if self.based_on == "Product":
			self.raw_material = ""
			condition += " and product = '" + str(self.product) + "'"
		else:
			self.product = ""
			condition += " and raw_material = '" + str(self.product) + "'"

		if self.item_type:
			condition += " and item_type = '" + str(self.item_type) + "'"
		
		if self.branch:
			condition += " and branch = '" + str(self.branch) + "'"
		for a in frappe.db.sql("""
				select name from `tabProduction Settings`
				where based_on = '{0}'
				and (
					from_date between '{1}' and '{2}'
					or ifnull(to_date, now()) between '{1}' and '{2}'
					or '{1}' between from_date and ifnull(to_date,now())
					or '{2}' between from_date and ifnull(to_date,now())
					)
				{3}
			""".format(self.based_on, self.from_date, self.to_date, condition), as_dict=True):
			if a.name:
				frappe.throw("Production Setting already exists for {} within {} and {} date in {}".format(self.raw_material, self.from_date, self.to_date, a.name))
