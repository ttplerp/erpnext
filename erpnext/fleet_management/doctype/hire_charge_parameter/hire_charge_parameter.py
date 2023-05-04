# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import getdate
from frappe.utils.data import nowdate, add_years, add_days, date_diff

class HireChargeParameter(Document):
	def before_save(self):
		for i, item in enumerate(sorted(self.items, key=lambda item: item.from_date), start=1):
			item.idx = i

	def validate(self):
		self.set_dates() 
		self.set_parameter_values()

	def set_dates(self):
		to_date = self.items[len(self.items) - 1].to_date
		for a in reversed(self.items):
			a.to_date = to_date
			to_date = add_days(a.from_date, -1)

	def set_parameter_values(self):
		p = frappe.db.sql("select name from `tabHire Charge Parameter` where equipment_type = %s and equipment_model = %s and name != %s", (str(self.equipment_type), str(self.equipment_model), str(self.name)), as_dict=True)
		if p:
			frappe.throw("Hire Charges for the equipment type and model already exists. Update " + str(p[0].name))
		if self.items:
			self.db_set("without_fuel", self.items[len(self.items) - 1].rate_wofuel)	
			self.db_set("with_fuel", self.items[len(self.items) - 1].rate_fuel)	
			self.db_set("idle", self.items[len(self.items) - 1].idle_rate)	
			self.db_set("cft_rate_bf", self.items[len(self.items) - 1].cft_rate_bf)	
			self.db_set("cft_rate_co", self.items[len(self.items) - 1].cft_rate_co)	
			self.db_set("lph", self.items[len(self.items) - 1].yard_hours)	
			self.db_set("kph", self.items[len(self.items) - 1].yard_distance)	
			self.db_set("benchmark", self.items[len(self.items) - 1].perf_bench)	
			self.db_set("interval", self.items[len(self.items) - 1].main_int)
		
		if len(self.items) > 1:
			for a in range(len(self.items)-1):
				self.items[a].to_date = frappe.utils.data.add_days(getdate(self.items[a + 1].from_date), -1)


