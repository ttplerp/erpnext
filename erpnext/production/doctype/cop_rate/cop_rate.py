# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document

class COPRate(Document):
	pass

@frappe.whitelist()
def get_cop_amount(posting_date, item_code):
	if not posting_date or not item_code:
		frappe.throw("Item Code and Posting Date are mandatory")
	cop_amount = frappe.db.sql("select rate from `tabCOP Rate` where item_code = %s and valid_from >= %s", (item_code, posting_date), as_dict=1)
	return cop_amount and flt(cop_amount[0].cop_amount) or 0.0

