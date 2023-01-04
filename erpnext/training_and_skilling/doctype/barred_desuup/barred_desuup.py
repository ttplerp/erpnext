# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class BarredDesuup(Document):
	def validate(self):
		self.validate_duplicate()

	def validate_duplicate(self):
		dtl = frappe.db.sql("""select name, from_date, to_date
						from `tabBarred Desuup`
						where docstatus !=2
						and 
							(
								'{0}' between from_date and to_date
								or '{1}' between from_date and to_date
								or from_date between '{0}' and '{1}'
								or to_date between '{0}' and '{1}'
							)
						and desuung_id = '{2}'
					""".format(self.from_date, self.to_date, self.desuung_id), as_dict=True)
		if dtl:
			frappe.throw("Desuung ID {} is already <b>from {} till {}</b> in Document : {}".format(self.desuung_id, self.from_date, self.to_date, dtl[0].name))
