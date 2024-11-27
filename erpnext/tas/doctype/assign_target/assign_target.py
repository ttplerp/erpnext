# -*- coding: utf-8 -*-
# Copyright (c) 2023, TTPL and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt, cint
from frappe.model.document import Document

class AssignTarget(Document):
	def validate(self):
		self.check_mandatory()
		self.check_duplicate_target_assignment()
		self.check_if_the_target_is_already_pulled()

	def check_mandatory(self):
		if not self.tas_target_setup:
			frappe.throw(_("Reference to <b>TAS Target Setup</b> is not found. \
				Please assign target from the respective <b>TAS Target Setup</b>"))
		elif not self.target_reference:
			frappe.throw(_("Reference to target is not found. Please assign the \
				target from the respective <b>TAS Target Setup</b>"))

	def check_duplicate_target_assignment(self):
		for d in frappe.db.get_all("Assign Target", {"target_reference": self.target_reference, \
				"name": ("!=", self.name), "docstatus": ("<",2)}):
			frappe.throw(_("Target is already assigned via {}").format(frappe.get_desk_link(\
				"Assign Target", d.name)))

	def check_if_the_target_is_already_pulled(self):
		for d in frappe.db.get_all("Financial Target Item", {"parent_target": self.target_reference, "docstatus": 1}):
			frappe.throw(_("This target is already pulled"))
		pass

@frappe.whitelist()
def get_dependent_units(doctype, txt, searchfield, start, page_len, filters):
	cond = ""
	if cint(filters.get("show_dependents")):
		cond = """ where exists(select 1
			from `tabPerformance Level` pl
			where pl.parent_level = "{}"
			and fu.performance_level = pl.name)""".format(filters.get("performance_level"))

	return frappe.db.sql("""select fu.name, fu.performance_level, fu.parent_unit
		from `tabFunctional Unit` fu
		{cond}
		""".format(cond=cond))
