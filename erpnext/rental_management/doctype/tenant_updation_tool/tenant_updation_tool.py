# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class TenantUpdationTool(Document):
	def validate(self):
		self.validate_same_data()

	def on_submit(self):
		doc = frappe.get_doc("Tenant Information", self.tenant)
		ministry_agency = self.new_ministry_agency if self.new_ministry_agency else doc.ministry_and_agency
		department = self.new_tenant_department if self.new_tenant_department else doc.tenant_department
		department_name = self.new_tenant_department_name if self.new_tenant_department_name else doc.tenant_department_name

		frappe.db.sql("update `tabTenant Information` set ministry_and_agency = \'"+ str(ministry_agency) +"\', tenant_department = \'"+ str(department) +"\', tenant_department_name = \'"+ str(department_name) +"\' where name= \'" + str(self.tenant) + "\'")

		frappe.msgprint("Tenant: {} information updated.".format(self.tenant))

	def on_cancel(self):
		doc = frappe.get_doc("Tenant Information", self.tenant)
		ministry_agency = self.ministry_agency
		department = self.tenant_department_id
		department_name = self.tenant_department

		frappe.db.sql("update `tabTenant Information` set ministry_and_agency = \'"+ str(ministry_agency) +"\', tenant_department = \'"+ str(department) +"\', tenant_department_name = \'"+ str(department_name) +"\' where name= \'" + str(self.tenant) + "\'")

		frappe.msgprint("Tenant: {} information reverted back to original.".format(self.tenant))

	def validate_same_data(self):
		if str(self.new_ministry_agency) == str(self.ministry_agency) and str(self.tenant_department_id) == str(self.new_tenant_department):
			frappe.throw("New Tenant Ministry/Agency and Department are same!")