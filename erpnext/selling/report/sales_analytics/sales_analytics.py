# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe import _, scrub
from frappe.utils import add_days, add_to_date, flt, getdate

from erpnext.accounts.utils import get_fiscal_year


def execute(filters=None):
	return Analytics(filters).run()


class Analytics(object):
	def __init__(self, filters=None):
		self.filters = frappe._dict(filters or {})
		self.date_field = (
			"transaction_date"
			if self.filters.doc_type in ["Sales Order", "Purchase Order"]
			else "posting_date"
		)
		self.months = [
			"Jan",
			"Feb",
			"Mar",
			"Apr",
			"May",
			"Jun",
			"Jul",
			"Aug",
			"Sep",
			"Oct",
			"Nov",
			"Dec",
		]
		self.get_period_date_ranges()

	def run(self):
		self.get_columns()
		self.get_data()
		self.get_chart_data()

		# Skipping total row for tree-view reports
		skip_total_row = 0

		if self.filters.tree_type in ["Supplier Group", "Item Group", "Customer Group", "Territory"]:
			skip_total_row = 1

		return self.columns, self.data, None, self.chart, None, skip_total_row

	def get_columns(self):
		self.columns = [
			{
				"label": _(self.filters.tree_type),
				"options": self.filters.tree_type if self.filters.tree_type != "Order Type" else "",
				"fieldname": "entity",
				"fieldtype": "Link" if self.filters.tree_type != "Order Type" else "Data",
				"width": 140 if self.filters.tree_type != "Order Type" else 200,
			}
		]
		if self.filters.tree_type in ["Supplier", "Item"]:
			self.columns.append(
				{
					"label": _(self.filters.tree_type + " Name"),
					"fieldname": "entity_name",
					"fieldtype": "Data",
					"width": 140,
				}
			)
		if self.filters.tree_type == "Customer":
			self.columns.append(
				{
					"label": _("Country"),
					"fieldname": "country",
					"fieldtype": "Link",
					"options": "Country",
					"width": 140,
				}
			)
			self.columns.append(
				{
					"label": _("Territory"),
					"fieldname": "territory",
					"fieldtype": "Link",
					"options": "Territory",
					"width": 140,
				}
			)
			self.columns.append(
				{
					"label": _("Customer Type"),
					"fieldname": "customer_type",
					"fieldtype": "Data",
					"width": 140,
				}
			)
		if self.filters.tree_type == "Item":
			self.columns.append(
				{
					"label": _("UOM"),
					"fieldname": "stock_uom",
					"fieldtype": "Link",
					"options": "UOM",
					"width": 100,
				}
			)

		for end_date in self.periodic_daterange:
			period = self.get_period(end_date)
			self.columns.append(
				{"label": _(period)+" (Qty)", "fieldname": scrub(period)+"_qty", "fieldtype": "Float", "width": 120}
			)
			self.columns.append(
				{"label": _(period+" (Value)"), "fieldname": scrub(period)+"_val", "fieldtype": "Float", "width": 120}
			)


		self.columns.append(
			{"label": _("Total Qty"), "fieldname": "total_qty", "fieldtype": "Float", "width": 120}
		)
		self.columns.append(
			{"label": _("Total Val"), "fieldname": "total", "fieldtype": "Float", "width": 120}
		)


	def get_data(self):
		if self.filters.tree_type in ["Customer", "Supplier"]:
			self.get_sales_transactions_based_on_customers_or_suppliers()
			self.get_rows()

		elif self.filters.tree_type == "Item":
			self.get_sales_transactions_based_on_items()
			self.get_rows()

		elif self.filters.tree_type in ["Customer Group", "Supplier Group", "Territory"]:
			self.get_sales_transactions_based_on_customer_or_territory_group()
			self.get_rows_by_group()

		elif self.filters.tree_type == "Item Group":
			self.get_sales_transactions_based_on_item_group()
			self.get_rows_by_group()

		elif self.filters.tree_type == "Order Type":
			if self.filters.doc_type != "Sales Order":
				self.data = []
				return
			self.get_sales_transactions_based_on_order_type()
			self.get_rows_by_group()

		elif self.filters.tree_type == "Project":
			self.get_sales_transactions_based_on_project()
			self.get_rows()

	def get_sales_transactions_based_on_order_type(self):
		# if self.filters["value_quantity"] == "Value":
		# value_field = "base_net_total"
		# else:
		# qty_field = "total_qty"
		value_field = """(select ifnull(sum(dni.base_amount),0) from `tabDelivery Note Item` dni
						where dni.parent = i.delivery_note
						and dni.docstatus = 1) - ifnull(sum(i.normal_loss_amt),0) - ifnull(sum(i.abnormal_loss_amt),0) + ifnull(sum(i.excess_amt),0) as value"""
		qty_field = """
						(select ifnull(sum(dni.qty),0) from `tabDelivery Note Item` dni
						where dni.parent = i.delivery_note
						and dni.docstatus = 1) - ifnull(sum(i.normal_loss),0) - ifnull(sum(i.abnormal_loss),0) + ifnull(sum(i.excess_qty),0) as qty
		"""
		self.entries = frappe.db.sql(
			""" select s.order_type as entity, s.{value_field} as value, s.{qty_field} as qty, s.{date_field}
			from `tab{doctype}` s, `tab{doctype} Item` i where s.name = i.parent and s.docstatus = 1 and s.company = %s and s.{date_field} between %s and %s
			and ifnull(s.order_type, '') != '' group by s.name order by s.order_type
		""".format(
				date_field=self.date_field, value_field=value_field, qty_field = qty_field, doctype=self.filters.doc_type
			),
			(self.filters.company, self.filters.from_date, self.filters.to_date),
			as_dict=1,
		)

		self.get_teams()

	def get_sales_transactions_based_on_customers_or_suppliers(self):
		cond = ''
		# if self.filters["value_quantity"] == "Value":
		# 	value_field = "base_net_total as value_field"
		# else:
		# 	value_field = "total_qty as value_field"
		# value_field = "base_net_total-total_normal_loss-total_abnormal_loss+total_excess_amount as value"
		# qty_field = "total_qty as qty"
		value_field = """(select ifnull(sum(dni.base_amount),0) from `tabDelivery Note Item` dni
						where dni.parent = i.delivery_note
						and dni.docstatus = 1) - ifnull(sum(i.normal_loss_amt),0) - ifnull(sum(i.abnormal_loss_amt),0) + ifnull(sum(i.excess_amt),0) as value"""
		# else:
		# qty_field = "total_qty as qty"
		qty_field = """
						(select ifnull(sum(dni.qty),0) from `tabDelivery Note Item` dni
						where dni.parent = i.delivery_note
						and dni.docstatus = 1) - ifnull(sum(i.normal_loss),0) - ifnull(sum(i.abnormal_loss),0) + ifnull(sum(i.excess_qty),0) as qty
		"""
		if self.filters.tree_type == "Customer":
			entity = "customer as entity"
			entity_name = "customer_name as entity_name"
			country = "country"
			territory = "territory"
			customer_type = "customer_type"
		else:
			entity = "supplier as entity"
			entity_name = "supplier_name as entity_name"
		if self.filters.territory:
			cond += " and b.territory = '{}'".format(self.filters.territory)
		if self.filters.country:
			cond += " and b.country = '{}'".format(self.filters.country)
		if self.filters.customer_type:
			cond += " and b.customer_type = '{}'".format(self.filters.customer_type)
		# self.entries = frappe.get_all(
		# 	self.filters.doc_type,
		# 	fields=[entity, entity_name, value_field, qty_field, self.date_field],
		# 	filters={
		# 		"docstatus": 1,
		# 		"company": self.filters.company,
		# 		self.date_field: ("between", [self.filters.from_date, self.filters.to_date]),
		# 	},
		# )
		self.entries = frappe.db.sql(
		"""
			select s.name, s.{entity}, s.{entity_name}, b.{country}, b.{territory}, b.{customer_type}, {value_field}, {qty_field}, s.{date_field}
			from `tab{doctype} Item` i , `tab{doctype}` s, `tabCustomer` b
			where s.name = i.parent and i.docstatus = 1 and s.company = %s
			and s.customer = b.name
			and s.{date_field} between %s and %s group by s.name
		""".format(
				entity = entity, entity_name = entity_name, country = country, territory = territory, customer_type = customer_type, date_field=self.date_field, value_field=value_field, doctype=self.filters.doc_type, qty_field=qty_field
			),
			(self.filters.company, self.filters.from_date, self.filters.to_date),
			as_dict=1,
		)
		# self.entries = frappe.db.sql("""
		# 	select a.{}, a.{}, b.{}, b.{}, b.{}, a.{}, a.{}, a.{} from `tab{}` s, `tab  `tabCustomer` b where
		# 	a.docstatus = 1
		# 	and a.customer = b.name
		# 	and a.company = '{}'
		# 	and a.{} between '{}' and '{}' {}
		# """.format(entity, entity_name, country, territory, customer_type, value_field, qty_field, self.date_field, self.filters.doc_type, self.filters.company, self.date_field, self.filters.from_date, self.filters.to_date, cond), as_dict=1)
		self.entity_names = {}
		for d in self.entries:
			self.entity_names.setdefault(d.entity, {"entity_name":d.entity_name, "country":d.country, 'territory': d.territory, 'customer_type': d.customer_type})
			# self.entity_names.setdefault(d.entity, d.entity_name)
		# frappe.msgprint(str(self.entity_names))

	def get_sales_transactions_based_on_items(self):

		# if self.filters["value_quantity"] == "Value":
		# else:
		# value_field = "i.base_net_amount-i.normal_loss_amt-i.abnormal_loss_amt+i.excess_amt as value"
		value_field = """(select ifnull(sum(dni.billed_amt),0) from `tabDelivery Note Item` dni
						where dni.parent = i.delivery_note
						and dni.docstatus = 1 and dni.item_code = i.item_code) - ifnull(sum(i.normal_loss_amt),0) - ifnull(sum(i.abnormal_loss_amt),0) + ifnull(sum(i.excess_amt),0) as value
		"""
		# qty_field = "i.stock_qty-i.normal_loss-i.abnormal_loss+i.excess_qty as qty"
		qty_field = """
						(select ifnull(sum(dni.qty),0) from `tabDelivery Note Item` dni
						where dni.parent = i.delivery_note
						and dni.docstatus = 1 and dni.item_code = i.item_code) - ifnull(sum(i.normal_loss),0) - ifnull(sum(i.abnormal_loss),0) + ifnull(sum(i.excess_qty),0) as qty
		"""
		self.entries = frappe.db.sql(
			"""
			select i.item_code as entity, i.item_name as entity_name, i.stock_uom, {value_field}, {qty_field}, s.{date_field}
			from `tab{doctype} Item` i , `tab{doctype}` s
			where s.name = i.parent and i.docstatus = 1 and s.company = %s
			and s.{date_field} between %s and %s group by s.name, i.item_code
		""".format(
				date_field=self.date_field, value_field=value_field, doctype=self.filters.doc_type, qty_field=qty_field
			),
			(self.filters.company, self.filters.from_date, self.filters.to_date),
			as_dict=1,
		)

		self.entity_names = {}
		for d in self.entries:
			self.entity_names.setdefault(d.entity, d.entity_name)

	def get_sales_transactions_based_on_customer_or_territory_group(self):
		# if self.filters["value_quantity"] == "Value":
		# value_field= "base_net_total as value"
		value_field = """(select ifnull(sum(dni.base_amount),0) from `tabDelivery Note Item` dni
						where dni.parent = i.delivery_note
						and dni.docstatus = 1) - ifnull(sum(i.normal_loss_amt),0) - ifnull(sum(i.abnormal_loss_amt),0) + ifnull(sum(i.excess_amt),0) as value"""
		# else:
		# qty_field = "total_qty as qty"
		qty_field = """
						(select ifnull(sum(dni.qty),0) from `tabDelivery Note Item` dni
						where dni.parent = i.delivery_note
						and dni.docstatus = 1) - ifnull(sum(i.normal_loss),0) - ifnull(sum(i.abnormal_loss),0) + ifnull(sum(i.excess_qty),0) as qty
		"""

		if self.filters.tree_type == "Customer Group":
			entity_field = "customer_group as entity"
		elif self.filters.tree_type == "Supplier Group":
			entity_field = "supplier as entity"
			self.get_supplier_parent_child_map()
		else:
			entity_field = "territory as entity"

		# self.entries = frappe.get_all(
		# 	self.filters.doc_type,
		# 	fields=["name", entity_field, value_field, qty_field, self.date_field],
		# 	filters={
		# 		"docstatus": 1,
		# 		"company": self.filters.company,
		# 		self.date_field: ("between", [self.filters.from_date, self.filters.to_date]),
		# 	},
		# )
		self.entries = frappe.db.sql(
		"""
			select s.name, s.{entity_field}, {value_field}, {qty_field}, s.{date_field}
			from `tab{doctype} Item` i , `tab{doctype}` s
			where s.name = i.parent and i.docstatus = 1 and s.company = %s
			and s.{date_field} between %s and %s group by s.name
		""".format(
				entity_field = entity_field, date_field=self.date_field, value_field=value_field, doctype=self.filters.doc_type, qty_field=qty_field
			),
			(self.filters.company, self.filters.from_date, self.filters.to_date),
			as_dict=1,
		)
		# frappe.msgprint(
		# 	"""
		# 	select s.{entity_field}, {value_field}, {qty_field}, s.{date_field}
		# 	from `tab{doctype} Item` i , `tab{doctype}` s
		# 	where s.name = i.parent and i.docstatus = 1 and s.company = '{company}'
		# 	and s.{date_field} between '{from_date}' and '{to_date}'
		# """.format(
		# 		entity_field = entity_field, date_field=self.date_field, value_field=value_field, doctype=self.filters.doc_type, qty_field=qty_field, from_date = self.filters.from_date, to_date = self.filters.to_date, company = self.filters.company
		# 	)
		# )
		self.get_groups()

	def get_sales_transactions_based_on_item_group(self):
		# if self.filters["value_quantity"] == "Value":
		# value_field = "base_amount"
		value_field = """(select ifnull(sum(dni.base_amount),0) from `tabDelivery Note Item` dni
						where dni.parent = i.delivery_note
						and dni.docstatus = 1 and dni.item_group = i.item_group) - ifnull(sum(i.normal_loss_amt),0) - ifnull(sum(i.abnormal_loss_amt),0) + ifnull(sum(i.excess_amt),0) as value
		"""
		# else:
		# qty_field = "qty"
		qty_field = """
						(select ifnull(sum(dni.qty),0) from `tabDelivery Note Item` dni
						where dni.parent = i.delivery_note
						and dni.docstatus = 1) - ifnull(sum(i.normal_loss),0) - ifnull(sum(i.abnormal_loss),0) + ifnull(sum(i.excess_qty),0) as qty
		"""

		self.entries = frappe.db.sql(
			"""
			select i.item_group as entity, {value_field}, {qty_field}, s.{date_field}
			from `tab{doctype} Item` i , `tab{doctype}` s
			where s.name = i.parent and i.docstatus = 1 and s.company = %s
			and s.{date_field} between %s and %s group by s.name, i.item_group
		""".format(
				date_field=self.date_field, value_field=value_field, doctype=self.filters.doc_type, qty_field=qty_field
			),
			(self.filters.company, self.filters.from_date, self.filters.to_date),
			as_dict=1,
		)

		self.get_groups()

	def get_sales_transactions_based_on_project(self):
		# if self.filters["value_quantity"] == "Value":
		# value_field = "base_net_total as value_field"
		value_field = """(select ifnull(sum(dni.base_amount),0) from `tabDelivery Note Item` dni
						where dni.parent = i.delivery_note
						and dni.docstatus = 1) - ifnull(sum(i.normal_loss_amt),0) - ifnull(sum(i.abnormal_loss_amt),0) + ifnull(sum(i.excess_amt),0) as value
		"""
		# else:
		# qty_field = "total_qty as value_field"
		qty_field = """
						(select ifnull(sum(dni.qty),0) from `tabDelivery Note Item` dni
						where dni.parent = i.delivery_note
						and dni.docstatus = 1) - ifnull(sum(i.normal_loss),0) - ifnull(sum(i.abnormal_loss),0) + ifnull(sum(i.excess_qty),0) as qty
		"""

		entity = "project as entity"

		# self.entries = frappe.get_all(
		# 	self.filters.doc_type,
		# 	fields=[entity, value_field, qty_field, self.date_field],
		# 	filters={
		# 		"docstatus": 1,
		# 		"company": self.filters.company,
		# 		"project": ["!=", ""],
		# 		self.date_field: ("between", [self.filters.from_date, self.filters.to_date]),
		# 	},
		# )
		self.entries = frappe.db.sql(
			"""
			select s.project as entity, {value_field}, {qty_field}, s.{date_field}
			from `tab{doctype} Item` i , `tab{doctype}` s
			where s.name = i.parent and i.docstatus = 1 and s.company = %s
			and s.{date_field} between %s and %s and (s.project is not NULL and s.project != '') group by s.name
		""".format(
				date_field=self.date_field, value_field=value_field, doctype=self.filters.doc_type, qty_field=qty_field
			),
			(self.filters.company, self.filters.from_date, self.filters.to_date),
			as_dict=1,
		)

	def get_rows(self):
		self.data = []
		self.get_periodic_data()

		for entity, period_data in self.entity_periodic_data.items():
			# frappe.msgprint(str(self.entity_names.get(entity)['country']))
			if self.filters.tree_type != "Customer":
				row = {
					"entity": entity,
					"entity_name": self.entity_names.get(entity) if hasattr(self, "entity_names") else None,
				}
			else:
				row = {
					"entity": entity,
					"entity_name": self.entity_names.get(entity)['entity_name'] if self.entity_names.get(entity)['entity_name'] else None,
					"country": self.entity_names.get(entity)['country'] if self.entity_names.get(entity)['country'] else None,
					"territory": self.entity_names.get(entity)['territory'] if self.entity_names.get(entity)['territory'] else None,
					"customer_type": self.entity_names.get(entity)['customer_type'] if self.entity_names.get(entity)['customer_type'] else None,	
				}
			total = total_qty = 0
			for end_date in self.periodic_daterange:
				period = self.get_period(end_date)
				# if self.filters.tree_type != "Customer":
				# 	amount = flt(period_data.get(period, 0.0))
				# 	row[scrub(period)] = amount
				# else:
				amount = flt(period_data.get(period+"_val", 0.0))
				qty = flt(period_data.get(period+"_qty", 0.0))
				row[scrub(period)+"_val"] = amount
				row[scrub(period)+"_qty"] = qty
				total_qty += qty
				total += amount


			row["total"] = total
			if self.filters.tree_type == "Item":
				row["stock_uom"] = period_data.get("stock_uom")
			# elif self.filters.tree_type == "Customer":
			row["total_qty"] = total_qty
			self.data.append(row)

	def get_rows_by_group(self):
		self.get_periodic_data()
		out = []

		for d in reversed(self.group_entries):
			row = {"entity": d.name, "indent": self.depth_map.get(d.name)}
			total = 0
			total_qty = 0
			for end_date in self.periodic_daterange:
				period = self.get_period(end_date)
				# amount = flt(self.entity_periodic_data.get(d.name, {}).get(period, 0.0))
				# row[scrub(period)] = amount
				# if d.parent and (self.filters.tree_type != "Order Type" or d.parent == "Order Types"):
				# 	self.entity_periodic_data.setdefault(d.parent, frappe._dict()).setdefault(period, 0.0)
				# 	self.entity_periodic_data[d.parent][period] += amount
				# total += amount
				amount = flt(self.entity_periodic_data.get(d.name, {}).get(period+"_val", 0.0))
				qty = flt(self.entity_periodic_data.get(d.name, {}).get(period+"_qty", 0.0))
				row[scrub(period)+"_val"] = amount
				row[scrub(period)+"_qty"] = qty
				if d.parent and (self.filters.tree_type != "Order Type" or d.parent == "Order Types"):
					self.entity_periodic_data.setdefault(d.parent, frappe._dict()).setdefault(period+"_val", 0.0)
					self.entity_periodic_data.setdefault(d.parent, frappe._dict()).setdefault(period+"_qty", 0.0)
					self.entity_periodic_data[d.parent][period+"_val"] += amount
					self.entity_periodic_data[d.parent][period+"_qty"] += qty
				total_qty += qty
				total += amount

			row["total"] = total
			row["total_qty"] = total_qty
			out = [row] + out

		self.data = out

	def get_periodic_data(self):
		self.entity_periodic_data = frappe._dict()

		for d in self.entries:
			if self.filters.tree_type == "Supplier Group":
				d.entity = self.parent_child_map.get(d.entity)
			period = self.get_period(d.get(self.date_field))
			# if self.filters.tree_type != "Customer":
			# 	self.entity_periodic_data.setdefault(d.entity, frappe._dict()).setdefault(period, 0.0)
			# 	self.entity_periodic_data[d.entity][period] += flt(d.value_field)
			# else:
			self.entity_periodic_data.setdefault(d.entity, frappe._dict()).setdefault(period+"_qty", 0.0)
			self.entity_periodic_data.setdefault(d.entity, frappe._dict()).setdefault(period+"_val",0.0)
			self.entity_periodic_data[d.entity][period+"_val"] += flt(d.value)
			self.entity_periodic_data[d.entity][period+"_qty"] += flt(d.qty)

			if self.filters.tree_type == "Item":
				self.entity_periodic_data[d.entity]["stock_uom"] = d.stock_uom

	def get_period(self, posting_date):
		if self.filters.range == "Weekly":
			period = "Week " + str(posting_date.isocalendar()[1]) + " " + str(posting_date.year)
		elif self.filters.range == "Monthly":
			period = str(self.months[posting_date.month - 1]) + " " + str(posting_date.year)
		elif self.filters.range == "Quarterly":
			period = "Quarter " + str(((posting_date.month - 1) // 3) + 1) + " " + str(posting_date.year)
		else:
			year = get_fiscal_year(posting_date, company=self.filters.company)
			period = str(year[0])
		return period

	def get_period_date_ranges(self):
		from dateutil.relativedelta import MO, relativedelta

		from_date, to_date = getdate(self.filters.from_date), getdate(self.filters.to_date)

		increment = {"Monthly": 1, "Quarterly": 3, "Half-Yearly": 6, "Yearly": 12}.get(
			self.filters.range, 1
		)

		if self.filters.range in ["Monthly", "Quarterly"]:
			from_date = from_date.replace(day=1)
		elif self.filters.range == "Yearly":
			from_date = get_fiscal_year(from_date)[1]
		else:
			from_date = from_date + relativedelta(from_date, weekday=MO(-1))

		self.periodic_daterange = []
		for dummy in range(1, 53):
			if self.filters.range == "Weekly":
				period_end_date = add_days(from_date, 6)
			else:
				period_end_date = add_to_date(from_date, months=increment, days=-1)

			if period_end_date > to_date:
				period_end_date = to_date

			self.periodic_daterange.append(period_end_date)

			from_date = add_days(period_end_date, 1)
			if period_end_date == to_date:
				break

	def get_groups(self):
		if self.filters.tree_type == "Territory":
			parent = "parent_territory"
		if self.filters.tree_type == "Customer Group":
			parent = "parent_customer_group"
		if self.filters.tree_type == "Item Group":
			parent = "parent_item_group"
		if self.filters.tree_type == "Supplier Group":
			parent = "parent_supplier_group"

		self.depth_map = frappe._dict()

		self.group_entries = frappe.db.sql(
			"""select name, lft, rgt , {parent} as parent
			from `tab{tree}` order by lft""".format(
				tree=self.filters.tree_type, parent=parent
			),
			as_dict=1,
		)

		for d in self.group_entries:
			if d.parent:
				self.depth_map.setdefault(d.name, self.depth_map.get(d.parent) + 1)
			else:
				self.depth_map.setdefault(d.name, 0)

	def get_teams(self):
		self.depth_map = frappe._dict()

		self.group_entries = frappe.db.sql(
			""" select * from (select "Order Types" as name, 0 as lft,
			2 as rgt, '' as parent union select distinct order_type as name, 1 as lft, 1 as rgt, "Order Types" as parent
			from `tab{doctype}` where ifnull(order_type, '') != '') as b order by lft, name
		""".format(
				doctype=self.filters.doc_type
			),
			as_dict=1,
		)

		for d in self.group_entries:
			if d.parent:
				self.depth_map.setdefault(d.name, self.depth_map.get(d.parent) + 1)
			else:
				self.depth_map.setdefault(d.name, 0)

	def get_supplier_parent_child_map(self):
		self.parent_child_map = frappe._dict(
			frappe.db.sql(""" select name, supplier_group from `tabSupplier`""")
		)

	def get_chart_data(self):
		length = len(self.columns)

		if self.filters.tree_type in ["Customer", "Supplier"]:
			labels = [d.get("label") for d in self.columns[2 : length - 1]]
		elif self.filters.tree_type == "Item":
			labels = [d.get("label") for d in self.columns[3 : length - 1]]
		else:
			labels = [d.get("label") for d in self.columns[1 : length - 1]]
		self.chart = {"data": {"labels": labels, "datasets": []}, "type": "line"}

		if self.filters["value_quantity"] == "Value":
			self.chart["fieldtype"] = "Currency"
		else:
			self.chart["fieldtype"] = "Float"