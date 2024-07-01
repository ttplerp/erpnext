# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import getdate
from frappe.utils import flt, getdate, cint, today, add_years, date_diff, nowdate
from frappe import _

class Equipment(Document):
	def before_save(self):
		for i, item in enumerate(sorted(self.operators, key=lambda item: item.start_date), start=1):
			item.idx = i

	def validate(self):
		if not self.equipment_number:
			self.equipment_number = self.name
		
		if not self.equipment_history:
			self.create_equipment_history(branch = self.branch, on_date = today(), ref_doc = self.name, purpose = 'Submit')

		if len(self.operators) > 1:
			for a in range(len(self.operators)-1):
				self.operators[a].end_date = frappe.utils.data.add_days(getdate(self.operators[a + 1].start_date), -1)
			self.operators[len(self.operators) - 1].end_date = ''

		if self.is_disabled == 1:
			last_row = self.equipment_history[len(self.equipment_history) - 1]
			if not last_row.to_date:
				last_row.to_date = getdate(nowdate())

		# if self.asset_code:
		# 	# eq_name = frappe.db.sql("select name from tabEquipment where exists (select e.asset_code from tabEquipment e where e.asset_code = '{}')".format(self.asset_code))
		# 	# if eq_name:
		# 	eq_name = frappe.db.exists({
		# 		'doctype': 'Equipment',
		# 		'asset_code': self.asset_code
		# 	})
		# 	if eq_name:
		# 		frappe.throw(_("Asset Code '{}' is already being used by Equipment: '{}'".format(self.asset_code,eq_name)))

	def create_equipment_history(self, branch, on_date, ref_doc, purpose):
		from_date = on_date
		if purpose == "Cancel":
			to_remove = []
			for a in self.equipment_history:
				if a.reference_document == ref_doc:
					to_remove.append(a)
		
			[self.remove(d) for d in to_remove]
			self.set_to_date()
			return
				
		if not self.equipment_history:
			self.append("equipment_history",{
									"branch": self.branch,
									"from_date": from_date,
			"reference_document": ref_doc
			})
		else:
			#doc = frappe.get_doc(self.doctype,self.name)
			ln = len(self.equipment_history)-1
			if self.branch != self.equipment_history[ln].branch:
				self.append("equipment_history",{
						"branch": self.branch,
						"from_date": from_date,
						"reference_document": ref_doc
			})
		self.set_to_date()

	def set_to_date(self):
		if len(self.equipment_history) > 1:
                        for a in range(len(self.equipment_history)-1):
                                self.equipment_history[a].to_date = frappe.utils.data.add_days(getdate(self.equipment_history[a + 1].from_date), -1)
		else:
			self.equipment_history[0].to_date = None

	def validate_asset(self):
		if self.asset_code:
			equipments = frappe.db.sql("select name from tabEquipment where asset_code = %s and name != %s", (self.asset_code, self.name), as_dict=True)
			if equipments:
				frappe.throw("The Asset is already linked to another equipment")
	
@frappe.whitelist()
def get_yards(equipment):
	t, m = frappe.db.get_value("Equipment", equipment, ['equipment_type', 'equipment_model'])
	data = frappe.db.sql("select lph, kph from `tabHire Charge Parameter` where equipment_type = %s and equipment_model = %s", (t, m), as_dict=True)
	if not data:
		frappe.throw("Setup yardstick for " + str(m))
	return data

@frappe.whitelist()
def get_equipments(doctype, txt, searchfield, start, page_len, filters):
	return frappe.db.sql("select a.equipment as name from `tabHiring Approval Details` a where docstatus = 1 and a.parent = \'"+ str(filters.get("ehf_name")) +"\'")

def sync_branch_asset():
	objs = frappe.db.sql("select e.name, a.branch from tabEquipment e, tabAsset a where e.asset_code = a.name and e.branch != a.branch", as_dict=True)
	for a in objs:
		frappe.db.sql("update tabEquipment set branch = %s where name = %s", (a.branch, a.name))


