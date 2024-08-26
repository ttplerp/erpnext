# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe

from frappe.model.document import Document

class ApprenticeAddition(Document):
	def validate(self):
		self.validate_deployment_entry()

	def on_submit(self):
		self.add_desuups()

	def validate_deployment_entry(self):
		if not self.items:
			frappe.throw("No Desuup to Add")

		doc = frappe.get_doc("Desuup Deployment Entry", self.desuup_deployment_entry)
		if doc.status not in ["Approved", "On Going"] or doc.docstatus != 0:
			frappe.throw("{} should be {} or {} and the document should not be submitted or cancelled".format(
				frappe.get_desk_link("Desuup Deployment Entry", self.desuup_deployment_entry),
				frappe.bold("Approved"),
				frappe.bold("On Going"),
			))

	def add_desuups(self):
		doc = frappe.get_doc("Desuup Deployment Entry", self.desuup_deployment_entry)
		for i in self.get("items"):
			doc.append("items", {
				"desuup": i.desuup,
				"desuup_name": i.desuup_name,
				"deployment_pay_type": i.payment_type,
				"amount": i.amount,
				"location": i.location,
				"programme": i.programme,
				"status": "Reported",
				"reported_date": self.posting_date,
			})
		doc.save()
