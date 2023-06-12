# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class Service(Document):
	def validate(self):
		self.item_code = self.name
		if self.bsr_service_item:
			bsr_code_exist = 0
			for a in frappe.db.sql("select count(*) as bsr_count from `tabService` where bsr_service_item = '1' and bsr_item_code = '{0}' and name != '{1}' and fiscal_year={2}".format(self.bsr_item_code, self.name, self.fiscal_year), as_dict=True):
				if a.bsr_count > 0:
					bsr_code_exist = 1
			if bsr_code_exist:
				frappe.throw("BSR Item Code {0} already recorded".format(self.bsr_item_code))

		self.validate_region_rate()

	def validate_region_rate(self):
		if not self.same_rate:
			for a in frappe.db.sql("select region from `tabBSR Region`",as_dict=True):
				flag = 0
				for r in self.bsr_detail_item:
					if a.region == r.region:
						flag = 1
				if not flag:
					frappe.throw("BSR Rate missing for {0} Region".format(a.region) )

