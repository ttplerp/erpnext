# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

class RectifyBudgetConsumption(Document):
	def validate(self):
		self.set_missing_values()

	def set_missing_values(self):
		if not self.document:
			frappe.throw(_("Document value is missing."))
		if not self.rectified_reference:
			frappe.throw(_("Rectified Reference is missing."))

		if not frappe.db.exists(self.document_type, self.document):
			frappe.throw(_("Document {0} of type {1} does not exist.").format(self.document, self.document_type))
		if not frappe.db.exists(self.rectified_type, self.rectified_reference):
			frappe.throw(_("Rectified Reference {0} of type {1} does not exist.").format(self.rectified_reference, self.rectified_type))

		if self.document_type == "Expense Claim":
			posting_date, doc_owner = frappe.get_value(self.document_type, self.document, ["posting_date", "owner"])
			self.document_date = posting_date
			self.document_owner = doc_owner
		if self.rectified_type == "Journal Entry":
			posting_date, rect_owner = frappe.get_value(self.rectified_type, self.rectified_reference, ["posting_date", "owner"])
			self.rectified_ref_date = posting_date
			self.rectified_owner = rect_owner

		self.user = frappe.session.user
	
	def on_submit(self):
		for d in frappe.get_all("Committed Budget", filters={"reference_type": self.document_type, "reference_no": self.document}, fields=["name"]):
			frappe.db.sql("Update `tabCommitted Budget` set reference_date=NULL where name=%s", d.name)

		for d in frappe.get_all("Consumed Budget", filters={"reference_type": self.document_type, "reference_no": self.document}, fields=["name"]):
			frappe.db.sql("Update `tabConsumed Budget` set reference_date=NULL where name=%s", d.name)

	def on_cancel(self):
		for d in frappe.get_all("Committed Budget", filters={"reference_type": self.document_type, "reference_no": self.document}, fields=["name"]):
			frappe.db.sql("Update `tabCommitted Budget` set reference_date=%s where name=%s", (self.document_date, d.name))

		for d in frappe.get_all("Consumed Budget", filters={"reference_type": self.document_type, "reference_no": self.document}, fields=["name"]):
			frappe.db.sql("Update `tabConsumed Budget` set reference_date=%s where name=%s", (self.document_date, d.name))