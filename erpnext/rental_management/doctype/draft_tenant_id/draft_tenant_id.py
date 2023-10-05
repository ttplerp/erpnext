# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class DraftTenantID(Document):
	def validate(self):
		pass

	def on_submit(self):
		self.change_flat_status()
		frappe.db.sql("update `tabTenant Information` set docstatus = 0 where name= '{0}' ".format(self.tenant_id))
		frappe.db.commit()

	def change_flat_status(self):
		if self.flat_id:
			frappe.db.sql("""update `tabFlat No` set status = "Unallocated" where name= '{0}' """.format(self.flat_id))
			frappe.db.commit()
