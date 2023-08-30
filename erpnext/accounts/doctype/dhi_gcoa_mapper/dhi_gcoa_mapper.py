# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class DHIGCOAMapper(Document):
	def validate(self):
		self.check_for_duplicate_gl_in_child_table()
	
	def check_for_duplicate_gl_in_child_table(self):
		account_set = set()  # Create a set to store encountered account values
		
		for idx, d in enumerate(self.items):
			if d.account in account_set:
				frappe.throw("Duplicate account found in the child table at <b>Row: {}</b> and account name is <b>{}</b>".format(idx+1, d.account))
			
			# Add the current account to the set
			account_set.add(d.account)

@frappe.whitelist()
def filter_account(doctype, txt, searchfield, start, page_len, filters):
	query = """
		SELECT 
			dg.account_code,
			dg.account_name,
			dg.account_type
		FROM `tabDHI GCOA` dg 
		WHERE NOT EXISTS(
			SELECT 1 FROM 
			`tabDHI GCOA Mapper` dgm
			WHERE dg.account_code = dgm.account_code
		)
		
	"""
	return frappe.db.sql(query)
