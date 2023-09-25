# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import cint, cstr, flt, formatdate, getdate, now

class OpeningBRSEntry(Document):
	def validate(self):
		self.validate_amount()

	def validate_amount(self):
		for d in self.details:
			if(flt(d.credit) > 0 and flt(d.debit) > 0):
				frappe.throw(_("At Row {0} either Credit Amount should be 0 or Debit Amount should be 0 for party {1}").format(d.idx, d.party))

