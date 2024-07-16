# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt, nowdate, add_days, getdate, fmt_money, add_to_date, DATE_FORMAT, date_diff, get_last_day

class DesuupDeploymentEntry(Document):
	def validate(self):
		self.validate_reported_date()

	def validate_reported_date(self):
		for item in self.get("items"):
			if item.reported_date:
				if getdate(item.reported_date) < getdate(self.start_date) or getdate(item.reported_date) > getdate(self.end_date):
					frappe.throw("Reported date for Row#{} must be between {} and {}".format(
						frappe.bold(item.idx),
						frappe.bold(self.start_date),
						frappe.bold(self.end_date),
					))
