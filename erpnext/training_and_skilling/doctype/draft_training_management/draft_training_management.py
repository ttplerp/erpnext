# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class DraftTrainingManagement(Document):
	def validate(self):
		pass
	
	def on_submit(self):
		'''
		if self.change_status:
			doc=frappe.get_doc("Training Management", self.training_management)
			if doc.status == self.status:
				frappe.throw("Please change the Status since you have checked Change Status")
		'''
		#doc = frappe.get_doc("Training Management", self.training_management)
		frappe.db.sql("update `tabTraining Management` set docstatus=0, status='{0}', workflow_state='{0}' where name='{1}'".format(self.status, self.training_management))
		frappe.db.sql("update `tabTrainee Details` set docstatus=0 where parent='{}'".format(self.training_management))
		#else:
		#	frappe.throw("Document is already in draft mode")

		frappe.db.commit()

