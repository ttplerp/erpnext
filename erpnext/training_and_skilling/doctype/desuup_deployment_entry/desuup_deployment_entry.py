# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt, add_days, getdate, fmt_money, add_to_date, DATE_FORMAT, date_diff, get_last_day
from datetime import date

class DesuupDeploymentEntry(Document):
	def validate(self):
		self.validate_reported_date()
		self.validate_duplicate_entry()
		self.validate_desuup()
	
	def on_submit(self):
		self.validate_completion_date()

	def validate_completion_date(self):
		if getdate(self.end_date) > getdate(date.today()):
			frappe.throw("Can be completed only after {}".format(frappe.bold(self.end_date)))

	def validate_duplicate_entry(self):
		data = []
		for d in self.items:
			if d.desuup not in data:
				data.append(d.desuup)
			else:
				frappe.throw("Duplicate Desuup Entry at #Row. {}".format(d.idx))

	def validate_desuup(self):
		desuup = frappe.db.sql("""
				SELECT
					t2.desuup, t1.name, t1.end_date
				FROM `tabDesuup Deployment Entry` t1 inner join `tabDesuup Deployment Entry Item` t2 
				ON t1.name=t2.parent 
				WHERE t1.status in ('On Going', 'Created')
			""", as_dict=True)
				
		for td in self.items:
			for t in desuup:
				if self.name != t.name: 
					if(t.desuup == td.desuup):
						frappe.throw(_("At Row {0} Desuup  <b>{1}</b> is under going OJT <b>{2}</b> till {3}.").format(td.idx, t.desuup, t.name, t.end_date))

	def validate_reported_date(self):
		if getdate(self.start_date) > getdate(self.end_date):
			frappe.throw("Start date must not be greater than End date")

		for item in self.get("items"):
			if item.reported_date:
				reported_date = getdate(item.reported_date)
				if reported_date < getdate(self.start_date) or reported_date > getdate(self.end_date):
					frappe.throw(
						"Reported date for Row#{} must be between {} and {}".format(
							frappe.bold(item.idx),
							frappe.bold(self.start_date),
							frappe.bold(self.end_date),
						)
					)

			if item.exit_date:
				exit_date = getdate(item.exit_date)
				if exit_date > getdate(self.end_date):
					frappe.throw(
						"Exit date for Row#{} must be less than or equal to {}".format(
							frappe.bold(item.idx),
							frappe.bold(self.end_date),
						)
					)

