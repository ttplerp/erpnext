# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import add_to_date, get_last_day, flt, getdate, cint
from frappe import _

class HousingApplication(Document):
	def validate(self):
		self.generate_rank()

	def on_submit(self):
		pass

	def generate_rank(self):
		if not self.applicant_rank:
			highest_rank = frappe.db.sql("""select max(applicant_rank) as ranking 
									from `tabHousing Application` 
									where employment_type="{employment_type}"
								""".format(employment_type=self.employment_type))[0][0]
			self.applicant_rank = cint(highest_rank) + 1