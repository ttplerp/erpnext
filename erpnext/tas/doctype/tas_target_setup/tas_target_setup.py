# -*- coding: utf-8 -*-
# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt, getdate, get_url, today, cint, nowdate
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from erpnext.custom_workflow import validate_workflow_states

class TASTargetSetup(Document):
	def validate(self):
		self.check_root_target()
		self.check_parent_unit_target()
		self.check_duplicate_entries()
		self.validate_targets()
		
	def on_update(self):
		self.update_total_weight()
		self.update_progress()

	def on_submit(self):
		self.validate_total_weight()

	def on_cancel(self):
		pass

	def check_root_target(self):
		''' make sure that the target setup for root level exists '''
		root_level = frappe.db.get("Performance Level", {"is_root_level": 1})
		if not root_level:
			frappe.throw(_("Root <b>Performance Level</b> is not found. Please set a root level under <b>Performance Level</b>"))

		if self.performance_level != root_level.name and not frappe.db.exists("TAS Target Setup", \
				{"tas_calendar": self.tas_calendar, "docstatus": 1, "performance_level": root_level.name}):
			frappe.throw(_("""<b>Target Setup</b> at <b>{}</b> is not prepared for the fiscal year yet""")\
				.format(root_level.name))

	def check_duplicate_entries(self):
		''' check for duplicate target setup '''
		filters = {"tas_calendar": self.tas_calendar, "name": ("!=",self.name), "docstatus": ("<",2), \
			"performance_level": self.performance_level}
		if not cint(self.is_root_level):
			filters.update({"functional_unit": self.functional_unit})

		for t in frappe.db.get_all("TAS Target Setup", filters):
			frappe.throw(_("There is another {} exists for the fiscal year").format(frappe.get_desk_link("TAS Target Setup", t.name)))

	def check_parent_unit_target(self):
		''' check if target setup for parent unit exists'''
		if self.parent_unit and not frappe.db.exists("TAS Target Setup", {"tas_calendar": self.tas_calendar, \
			"docstatus": 1, "functional_unit": self.parent_unit}):
			frappe.throw(_("""<b>Target Setup</b> is not prepared for parent unit <b>{}</b> yet.
				You can set the targets only after the parent unit submits it's targets""").format(self.parent_unit))

	def validate_weightage(self, row):
		if flt(row.weightage) <= 0:
				frappe.throw(_("Row# {}: <b>Weightage</b> should be greater than 0 under <b>{}</b>")\
					.format(row.idx, row.doctype), title="Error")

	def validate_targets(self):
		# financial trgets
		for row in self.financial_target_item:
			self.validate_weightage(row)

		# non financial trgets
		for row in self.non_financial_target_item:
			self.validate_weightage(row)

		# common trgets
		for row in self.common_target_item:
			self.validate_weightage(row)

	def update_total_weight(self):
		self.total_financial_weight = sum([flt(row.weightage) for row in self.financial_target_item])
		self.total_non_financial_weight = sum([flt(row.weightage) for row in self.non_financial_target_item])
		self.total_common_weight = sum([flt(row.weightage) for row in self.common_target_item])

		self.total_weight = self.total_financial_weight + self.total_non_financial_weight + self.total_common_weight

	def update_progress(self):
		pass
		# self.db_set('financial_progress')
		# prev_docstatus =  self.get_db_value('docstatus')
		# if prev_docstatus == 1:
		# 	pass
		# else:
		# 	pass

	def validate_total_weight(self):
		if flt(self.total_weight) != 100:
			frappe.throw(_("<b>Total Weightage({})</b> of all your targets should be equal to <b>100</b>").format(self.total_weight))

	def set_rejected_reason(self, reason):
		doc = frappe.get_doc("TAS Target Setup", self.name)
		doc.remarks = reason
		doc.save(ignore_permissions = True)

		return True

@frappe.whitelist()
def create_review(source_name, target_doc=None):
	# if frappe.db.exists('TAS Review', {'target': source_name,
	# 	'docstatus':('!=',2)}):
	# 	frappe.throw(
	# 		title='Error',
	# 		msg="You have already created Review for this Target")

	doclist = get_mapped_doc("TAS Target Setup", source_name, {
		"TAS Target Setup": {
			"doctype": "TAS Review",
			"field_map":{
					"tas_target_setup":"name"
				},
			},
		"Financial Target Item":{
				"doctype":"Review Financial Item"
			},
		"Non Financial Target Item":{
				"doctype":"Review Non Financial Item"
			},
		"Common Target Item":{
				"doctype":"Review Common Item"
			},
	}, target_doc)

	return doclist
