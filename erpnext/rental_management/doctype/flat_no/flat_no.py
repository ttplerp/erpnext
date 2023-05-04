# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class FlatNo(Document):
	def autoname(self):
		self.name = "/".join([self.block_no, self.flat_no])
