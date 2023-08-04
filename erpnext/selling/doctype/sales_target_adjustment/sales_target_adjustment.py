# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt
from frappe.model.document import Document

class SalesTargetAdjustment(Document):
	def on_submit(self):
		self.update_adjustment()

	def on_cancel(self):
		self.update_adjustment(cancel=True)

	def update_adjustment(self, cancel=False):
		sales_target_id = frappe.db.get_value("Sales Target",{"item_sub_group":self.item_sub_group, "fiscal_year":self.fiscal_year,"docstatus": 1},"name")
		if self.total:
			sales_target= frappe.get_doc("Sales Target", sales_target_id)
			for raw in self.item:
				# frappe.throw(str(sales_target_id))
				if raw.month and raw.adjusted_amount:
					item_name =frappe.db.sql("""
						select name from `tabSales Target Item` 
						where parent='{0}'
						and month='{1}'
					""".format(sales_target_id, raw.month))[0][0]
					sales_target_item= frappe.get_doc("Sales Target Item", item_name)
					total_t_qty = frappe.db.get_value("Sales Target Item",item_name,"total_target_qty")
					adjusted_t_qty = frappe.db.get_value("Sales Target Item",item_name,"adjusted_qty")
					if cancel:
						total_qty = flt(total_t_qty) - flt(raw.adjusted_amount)
						adj_qty =flt(adjusted_t_qty) - flt(raw.adjusted_amount)
						sales_target_item.db_set("adjusted_qty", flt(adj_qty,2))
						sales_target_item.db_set("total_target_qty", flt(total_qty,2))
					else:
						total_qty = flt(total_t_qty) + flt(raw.adjusted_amount)
						sales_target_item.db_set("adjusted_qty", flt(raw.adjusted_amount,2))
						sales_target_item.db_set("total_target_qty", flt(total_qty,2))
					# frappe.throw(str(sales_target_item))
			t_qty = frappe.db.get_value("Sales Target",sales_target_id,"total_target_qty")
			adj_qty = frappe.db.get_value("Sales Target",sales_target_id,"total_adjusted_qty")
			if cancel:
				t_total_qty = flt(t_qty) - flt(self.total)
				t_adj_qty = flt(adj_qty)- flt(self.total)
				sales_target.db_set("total_target_qty", flt(t_total_qty,2))
				sales_target.db_set("total_adjusted_qty", flt(t_adj_qty,2))
			else:
				t_total_qty = flt(t_qty)+ flt(self.total)
				t_adj_qty = flt(adj_qty) + flt(self.total)
				sales_target.db_set("total_target_qty", flt(t_total_qty,2))
				sales_target.db_set("total_adjusted_qty", flt(t_adj_qty,2))