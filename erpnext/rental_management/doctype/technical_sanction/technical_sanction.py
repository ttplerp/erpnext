# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class TechnicalSanction(Document):
	pass

	@frappe.whitelist()
	def get_item_price(self, args):
		# frappe.throw(str(args))
		if not args.price_list:
			frappe.throw("Price List missing!")
			
		conditions = """where item_code=%(item_code)s
			and price_list=%(price_list)s
			and ifnull(uom, '') in ('', %(uom)s)"""

		if args.get("posting_date"):
			conditions += """ and %(posting_date)s between
				ifnull(valid_from, '2000-01-01') and ifnull(valid_upto, '2500-12-31')"""

		item_price = frappe.db.sql(
			""" select name, price_list_rate, uom
			from `tabItem Price` {conditions}
			order by valid_from desc, ifnull(batch_no, '') desc, uom desc """.format(
				conditions=conditions
			),
			args,
		)

		# if len(item_price) == 0:
		# 	frappe.throw("Missing Item in Price List.")

		return item_price

@frappe.whitelist()
def get_price_list(doctype, txt, searchfield, start, page_len, filters):
	# frappe.throw("this is ok")
	cond = " and bs.docstatus=1"
	if filters and filters.get("region"):
		cond += " and bs.region = '%s'" % filters.get("region")
	else:
		cond += " and bs.region is null"

	return frappe.db.sql(
		"""select pl.name from `tabBSR Service` bs, `tabPrice List` pl
			where bs.price_list = pl.name {cond}
			order by pl.name limit %(page_len)s offset %(start)s""".format(
			key=searchfield, cond=cond
		),
		{"txt": "%" + txt + "%", "start": start, "page_len": page_len},
	)
	# where `{key}` LIKE %(txt)s {cond}

	# cond = " and docstatus=1"
	# if filters and filters.get("region"):
	# 	cond += " and region = '%s'" % filters.get("region")
	# else:
	# 	cond += " and region is null"

	# return frappe.db.sql(
	# 	"""select price_list from `tabBSR Service`
	# 		where `{key}` LIKE %(txt)s {cond}
	# 		order by name limit %(page_len)s offset %(start)s""".format(
	# 		key=searchfield, cond=cond
	# 	),
	# 	{"txt": "%" + txt + "%", "start": start, "page_len": page_len},
	# )