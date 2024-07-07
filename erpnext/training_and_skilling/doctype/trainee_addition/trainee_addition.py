# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class TraineeAddition(Document):
	def validate(self):
		self.validate_tm()

	def validate_tm(self):
		doc = frappe.get_doc("Training Management",self.training_management)
		if doc.status not in ["Approved", "On Going"] and doc.docstatus != 0:
			frappe.throw("Training Management {} should be {} or {} and the document should not be submitted or cancelled")

	def on_submit(self):
		doc = frappe.get_doc("Training Management",self.training_management)
		for i in self.get("item"):
			doc.append("trainee_details", {
								"desuup_id": i.did,
								"desuup_cid": i.cid,
								"desuup_name": i.desuup_name,
								"mobile": i.mobile_no
			})
		doc.save()


