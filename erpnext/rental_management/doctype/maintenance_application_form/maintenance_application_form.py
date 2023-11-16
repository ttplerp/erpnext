# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc

from frappe import _

class MaintenanceApplicationForm(Document):
	def get_query(self, doctype, txt, searchfield, start, page_len, filters):
		if searchfield == "linked_field":
			return frappe.db.sql("""
                SELECT name, other_field
                FROM `tabLinkedDocType`
                WHERE other_field LIKE %(txt)s
                ORDER BY other_field ASC
                LIMIT %(start)s, %(page_len)s
            """, {
                "txt": "%%%s%%" % txt,
                "start": start,
                "page_len": page_len
            })
	def validate(self):
		if self.maf_status =="On Hold":
			pass
		elif self.workflow_state == "Waiting Supervisor Approval":
			self.maf_status ="In Process"
		

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


# @frappe.whitelist()
# def send_typed_input(typed_input):
#     # Perform necessary actions with the typed_input
#     # For example:
#     frappe.msgprint(typed_input)  # To print the input as a message in Frappe

#     # Return a message or data
#     return 'success'
import frappe
import json
from frappe import _

@frappe.whitelist(allow_guest=True)
def get_cid_detail(tenant_cid):
    try:
        # Execute SQL query
        sql_query = """
        SELECT name, tenant_name, block_no, flat_no, location_name,dzongkhag,locations,phone_no, name
        FROM `tabTenant Information` 
        WHERE tenant_cid = %(tenant_cid)s
        """
        # Parameters to pass to the query
        query_params = {"tenant_cid": tenant_cid}

        data = frappe.db.sql(sql_query, query_params, as_dict=True)
		
        # Convert data to JSON format
        

        # Return the data as JSON to the client side
        return data
    except Exception as e:
        frappe.log_error(_("Error in get_tenant_name: {0}").format(e))
        return None
