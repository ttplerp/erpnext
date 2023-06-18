# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc

class MaintenanceApplicationForm(Document):
	pass

@frappe.whitelist()
def make_technical_sanction(source_name, target_doc=None):
	doclist = get_mapped_doc("Maintenance Application Form", source_name, {
		"Maintenance Application Form": {
			"doctype": "Technical Sanction",
			"field_map": {
				"parent": "name",
			},
			"validation": {
				#    "docstatus": ["=", 1]
			}
		},
	}, target_doc)

	return doclist