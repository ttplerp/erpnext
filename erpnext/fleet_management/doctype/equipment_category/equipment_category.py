# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class EquipmentCategory(Document):
	@frappe.whitelist()
	def get_pol_receive_account(self):
		account = frappe.db.get_single_value("Maintenance Settings", "pol_receive_account")
		if not account:
			frappe.throw("Please set pol receive account in Maintenance Settings")
		self.pol_receive_account = account
		return account
