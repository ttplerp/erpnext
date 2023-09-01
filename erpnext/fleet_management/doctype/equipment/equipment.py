# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import nowdate, getdate, cint

class Equipment(Document):
	def validate(self):
		self.update_equipment_hiring_form()
		# self.validate_asset_fuelbook()
	
	# def validate_asset_fuelbook(self):
	# 	if self.asset_code:
	def update_equipment_hiring_form(self):
		if self.supplier != frappe.db.get_value(self.doctype, self.name,"supplier") and cint(self.hired_equipment) == 1:
			frappe.db.sql("update `tabEquipment Hiring Form` set supplier = '{}' where equipment = '{}'".format(self.supplier, self.name))
		
	@frappe.whitelist()
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
			self.append("equipment_history", {
				"branch": self.branch,
				"from_date": from_date,
				"supplier": self.supplier if self.hired_equipment else '',
				"reference_document": ref_doc,
				# "bank_name": self.bank_name,
				# "account_number": self.account_number,
				# "ifs_code": self.ifs_code
			})
		else:
			ln = len(self.equipment_history)-1
			if ln < 0:
				self.append("equipment_history", {
					"branch": self.branch,
					"from_date": from_date,
					"supplier": self.supplier if self.hired_equipment else '',
					"reference_document": ref_doc,
					# "bank_name": self.bank_name,
					# "account_number": self.account_number,
					# "ifs_code": self.ifs_code
				})
			elif self.branch != self.equipment_history[ln].branch or self.supplier != self.equipment_history[ln].supplier:
				self.append("equipment_history", {
					"branch": self.branch,
					"from_date": from_date,
					"supplier": self.supplier if self.hired_equipment else '',
					"reference_document": ref_doc,
					# "bank_name": self.bank_name,
					# "account_number": self.account_number,
					# "ifs_code": self.ifs_code
				})
			self.set_to_date()

	def set_to_date(self):
		if len(self.equipment_history) > 1:
			for a in range(len(self.equipment_history)-1):
				self.equipment_history[a].to_date = frappe.utils.data.add_days(
					getdate(self.equipment_history[a + 1].from_date), -1)
		else:
			self.equipment_history[0].to_date = None
	@frappe.whitelist()
	def get_operator_name(self, employee_type, employee):
		if employee_type and employee:
			if employee_type == "Muster Roll Employee":
				return frappe.db.get_value(employee_type, employee, "person_name")
			elif employee_type == "Employee":
				return frappe.db.get_value(employee_type, employee, "employee_name")