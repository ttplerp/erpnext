# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class UpdateDeploymentCategory(Document):
	def validate(self):
		pass

	def before_submit(self):
		if self.get("item"):
			for a in self.get("item"):
				if not a.deployment_category:
					frappe.throw("Row {} : Please map Deployment Category for Title {}".format(a.idx, a.deployment_title))
				else:
					doc = frappe.get_doc("Deployment Title", a.deployment_title)
					doc.deployment_category = a.deployment_category
					doc.save()
		else:
			frappe.throw("Not allowed to submit as item is mandatory")

	def on_submit(self):
		pass

	@frappe.whitelist()
	def get_deployment_title(self):
		self.set('item', [])
		for a in frappe.db.sql(""" select deployment_title
									from `tabDeployment Title`
									where deployment_category = "" 
									or deployment_category is NULL
						""", as_dict=True):
			row = self.append('item', {})
			row.update(a)