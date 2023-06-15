# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class RateAnalysis(Document):
	pass

	@frappe.whitelist()
	def get_item_price(self, args):
		# frappe.throw(str(args))
		if not args.price_list:
			frappe.throw("Price List value missing!")
			
		conditions = """where item_code=%(item_code)s
			and price_list=%(price_list)s
			and ifnull(uom, '') in ('', %(uom)s)"""

		# conditions += "and ifnull(batch_no, '') in ('', %(batch_no)s)"

		# if not ignore_party:
		# 	if args.get("customer"):
		# 		conditions += " and customer=%(customer)s"
		# 	elif args.get("supplier"):
		# 		conditions += " and supplier=%(supplier)s"
		# 	else:
		# 		conditions += "and (customer is null or customer = '') and (supplier is null or supplier = '')"

		if args.get("posting_date"):
			conditions += """ and %(posting_date)s between
				ifnull(valid_from, '2000-01-01') and ifnull(valid_upto, '2500-12-31')"""

		return frappe.db.sql(
			""" select name, price_list_rate, uom
			from `tabItem Price` {conditions}
			order by valid_from desc, ifnull(batch_no, '') desc, uom desc """.format(
				conditions=conditions
			),
			args,
		)
