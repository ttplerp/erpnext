# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import (
	add_days,add_months, cint, date_diff, flt, get_datetime, get_last_day, get_first_day, getdate, month_diff, nowdate,	today, get_year_ending,	get_year_start,
)


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

@frappe.whitelist()	
def remove_from_barred():
	for a in frappe.db.sql("""
							select name, barred, to_date from `tabBarred Desuup`
							where to_date < '{}'
							and barred = 1
						""".format(getdate(today())), as_dict=True):
		frappe.db.sql("update `tabBarred Desuup` set barred=0 where name='{}'".format(a.name))
	frappe.db.commit()
 