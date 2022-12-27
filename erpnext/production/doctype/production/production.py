# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, cstr, flt, fmt_money, formatdate, nowtime, getdate
from erpnext.accounts.utils import get_fiscal_year

class Production(Document):
	def validate(self):
		pass
		# check_future_date(self.posting_date)
		# self.check_cop()
		# self.validate_data()
		# self.validate_warehouse()
		# self.validate_supplier()
		# self.validate_items()
		# self.validate_posting_time()
		# self.validate_transportation()
		# self.validate_raw_material_product_qty()
		# if self.coal_raising_type:
		# 	self.validate_coal_raising()

	def before_submit(self):
		pass
	def on_submit(self):
		pass
	def on_cancel(self):
		pass
	@frappe.whitelist()
	def get_finish_product(self):
		data = []
		if not self.branch and not self.posting_date:
			frappe.throw("Select branch and posting date to get the products after productions")

		if not self.raw_materials:
			frappe.throw("Please enter a raw material to get the Product")
		else:
			condition = ""
			for a in self.raw_materials:
				raw_material_item = a.item_code
				raw_material_qty = a.qty
				raw_material_unit = a.uom
				item_group = frappe.db.get_value("Item", a.item_code, "item_group")				
				cost_center = a.cost_center
				warehouse = a.warehouse
				expense_account = a.expense_account
				item_type = a.item_type
				if a.item_type:
					condition += " and item_type = '" + str(a.item_type) + "'"
				if a.warehouse:
					condition += " and warehouse = '" + str(a.warehouse) + "'"
		
		if raw_material_item:
			count = 0
			production_seting_code = ""
			for a in frappe.db.sql("""select name 
							from `tabProduction Settings`
							where branch = '{0}' and disable != 1
							and raw_material = '{1}'
							{3}
							and '{2}' between from_date and ifnull(to_date,now())		
				""".format(self.branch, raw_material_item, self.posting_date, condition), as_dict=True):
				count += 1
				production_seting_code = a.name
			
			if count > 1:
				frappe.throw("There are more than 1 production setting for this production parameters")

			if production_seting_code:
				for a in frappe.db.sql("""
						select parameter_type, ratio, item_code, item_name, item_type
						from `tabProduction Settings Item` 
						where parent = '{0}'				
					""".format(production_seting_code), as_dict=True):
					price_template = ""
					cop = ""
					product_qty = 0.00
					for b in frappe.db.sql("""select c.name, b.cop_amount 
						from `tabCost of Production` c, `tabCOP Branch` a, `tabCOP Rate Item` b 
						where c.name = a.parent and c.name = b.parent
						and a.branch = %s 
						and b.item_code = %s 
						and %s between c.from_date and c.to_date
					""",(str(self.branch), str(a.item_code), str(self.posting_date)), as_dict=True):
						price_template = b.name
						cop = b.cop_amount
					if flt(a.ratio) > 0:
						product_qty = (flt(a.ratio) * flt(raw_material_qty))/100
					data.append({
								"parameter_type": a.parameter_type,
								"item_code":a.item_code, 
								"item_name":a.item_name,
								"item_type":a.item_type, 
								"qty": product_qty,
								"uom": raw_material_unit,
								"price_template": price_template,
								"cop": cop,
								"cost_center": cost_center,
								"warehouse": warehouse,
								"expense_account": expense_account,
								"ratio": flt(a.ratio)
								})
				# frappe.msgprint("{}".format(data))
		if data:			
			return data
		else:
			frappe.msgprint("No records in production settings")

	@frappe.whitelist()
	def get_raw_material(self):
		data = []
		if not self.branch and not self.posting_date:
			frappe.throw("Select branch and posting date to get the raw materials")

		if not self.items:
			frappe.throw("Please enter a product to get the raw material")
		else:
			condition = ""
			for a in self.items:
				product_item = a.item_code
				product_qty = a.qty
				product_unit = a.uom				
				cost_center = a.cost_center
				warehouse = a.warehouse
				expense_account = a.expense_account
				item_type = a.item_type
				if a.item_type:
					condition += " and item_type = '" + str(a.item_type) + "'"
				if a.warehouse:
					condition += " and warehouse = '" + str(a.warehouse) + "'"
		
		if product_item:
			count = 0
			production_seting_code = ""
			for a in frappe.db.sql("""select name 
							from `tabProduction Settings`
							where branch = '{0}' and disable != 1
							and product = '{1}'
							{3}
							and '{2}' between from_date and ifnull(to_date,now())		
				""".format(self.branch, product_item, self.posting_date, condition), as_dict=True):
				count += 1
				production_seting_code = a.name
			
			if count > 1:
				frappe.throw("There are more than 1 production setting for this production parameters")

			if production_seting_code:
				for a in frappe.db.sql("""
						select parameter_type, ratio, item_code, item_name, item_type
						from `tabProduction Settings Item` 
						where parent = '{0}'				
				""".format(production_seting_code), as_dict=True):
					raw_material_qty = 0.00
					if flt(a.ratio) > 0:
						raw_material_qty = (flt(a.ratio) * flt(product_qty))/100
					data.append({
								"parameter_type": a.parameter_type,
								"item_code":a.item_code, 
								"item_name":a.item_name, 
								"item_type":a.item_type,
								"qty": raw_material_qty,
								"uom": product_unit,
								"cost_center": cost_center,
								"warehouse": warehouse,
								"expense_account": expense_account,
								})
		if data:			
			return data
		else:
			frappe.msgprint("No records in production settings")


