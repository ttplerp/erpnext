# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from frappe.utils import cstr, flt, fmt_money, formatdate, nowdate

class RevisedTechnicalSanction(Document):
	def validate(self):
		self.calculate_total_amount()

	def calculate_total_amount(self):
		total = 0
		if self.items: 
			for item in self.items:
				total += item.total

		self.total_amount = total - self.tools_and_plant - self.rm

	def on_submit(self):
		if self.technical_sanction:
			frappe.db.sql("update `tabTechnical Sanction` set revised_technical_sanction = '{rts}' where name ='{ts}'".format(rts=self.name, ts=self.technical_sanction))
		else: 
			frappe.throw("There is no technical sanction {}".format(self.technical_sanction))

	def on_cancel(self):
		if self.docstatus == 2:
			frappe.db.sql("update `tabTechnical Sanction` set revised_technical_sanction = '' where name ='{ts}'".format(ts=self.technical_sanction))

	def rts_bill_validate_service_qty(self, item_name=None):
		for d in self.get("items"):
			if d.service == item_name:
				rts_qty = flt(
					frappe.db.sql(
						"""select sum(i.qty)
					from `tabTechnical Sanction Item` i inner join `tabTechnical Sanction Bill` b on b.name=i.parent where i.service = %s
					and i.parenttype = 'Technical Sanction Bill' and b.revised_technical_sanction = %s and b.docstatus = 1""",
						(item_name, self.name),
					)[0][0]
				)

				if flt(rts_qty) and flt(rts_qty) > flt(d.qty):
					frappe.throw(
						_(
							"The total TS-Bill quantity {0} cannot be greater then total Revised Technical Sanction quantity {1} for Item {2} in Revised Technical Sanction {3}"
						).format(rts_qty, flt(d.qty), d.service, d.parent)
					)

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

		if len(item_price) == 0:
			cond = """where item_code=%(item_code)s
				and price_list=%(price_list)s
				and ifnull(uom, '') in ('', %(uom)s)"""

			chk_item = frappe.db.sql(
				""" select name, price_list_rate, uom
				from `tabItem Price` {conditions}
				""".format(
					conditions=cond
				),
				args,
			)
			if len(chk_item) != 0:
				frappe.throw("Posting date, not within the validity of Item Price list.")

			frappe.throw("Missing Item in Price List.")

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

@frappe.whitelist()
def prepare_bill(source_name, target_doc=None):
	def update_docs(obj, target, source_parent):
		target.revised_technical_sanction = obj.name
		target.tds_taxable_amount = target.total_gross_amount
		target.invoice_amount = target.total_gross_amount
	doc = get_mapped_doc("Revised Technical Sanction", source_name, {
		"Revised Technical Sanction": {
			"doctype": "Technical Sanction Bill","field_map":{
				"total_amount" : "total_gross_amount"
			},	
			"postprocess": update_docs,
			"validation": {"docstatus": ["=", 1]}
		},
	}, target_doc)
	return doc

