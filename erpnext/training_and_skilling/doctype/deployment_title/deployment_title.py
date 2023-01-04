# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class DeploymentTitle(Document):
	def validate(self):
		if self.deployment_category and frappe.db.exists("Deployment", {"deployment_title":self.deployment_title}):
			frappe.db.sql("""update `tabDeployment` 
							set deployment_category = "{}"
							where deployment_title = "{}"
						""".format(self.deployment_category, self.deployment_title))
			frappe.db.commit()