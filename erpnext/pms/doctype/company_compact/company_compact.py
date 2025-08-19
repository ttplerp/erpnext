# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document

class CompanyCompact(Document):
	def validate(self):
		self.validate_duplicate()

	def validate_duplicate(self):
		if self.type == "Company":
			existing_compact = frappe.get_all(
				"Company Compact",
				filters={"company": self.company, "compact": self.compact, "fiscal_year": self.fiscal_year, "name": ["!=", self.name]},
				limit=1,
				fields=["name"],
			)
			if existing_compact:
				frappe.throw(
					_("A compact with the same company and compact already exists: {0} for fiscal year {1}").format(existing_compact[0].name, self.fiscal_year)
				)
		else:
			existing_compact = frappe.get_all(
				"Company Compact",
				filters={"department": self.department, "compact": self.compact, "fiscal_year": self.fiscal_year, "name": ["!=", self.name]},
				limit=1,
				fields=["name"],
			)
			if existing_compact:
				frappe.throw(
					_("A compact with the same department and compact already exists: {0} for fiscal_year").format(existing_compact[0].name, self.fiscal_year)
				)
