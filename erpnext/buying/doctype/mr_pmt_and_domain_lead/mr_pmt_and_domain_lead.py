# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt
import frappe

from frappe.model.document import Document

class MRPMTAndDomainLead(Document):
	
	def validate(self):
		self.domain_item_duplicate()
		self.pmt_item_duplicate()

	def domain_item_duplicate(self):
		data = []
		for d in self.get("domain_item"):
			if d.cost_center not in data:
				data.append(d.cost_center)
			else:
				frappe.throw("#row {}, duplicate data in Domain List!".format(d.idx))
	
	def pmt_item_duplicate(self):
		data = []
		for d in self.get("pmt_item"):
			if d.cost_center not in data:
				data.append(d.cost_center)
			else:
				frappe.throw("#row {}, duplicate data in PMT List!".format(d.idx))
	@frappe.whitelist()
	def get_domain_list(self, cost_center):
		# self.set('domain_item', [])
		for d in frappe.db.sql("""select name as cost_center, parent_cost_center as domain from `tabCost Center` 
			where disabled = 0 and parent_cost_center='{}'""".format(cost_center), as_dict=1):
			
			row = self.append('domain_item', {})
			row.update(d)
		
		return "Done"
	
	@frappe.whitelist()
	def get_pmt_list(self, cost_center):
		# self.set('pmt_item', [])
		for d in frappe.db.sql("""select name as cost_center, parent_cost_center as domain from `tabCost Center` 
			where disabled = 0 and parent_cost_center='{}'""".format(cost_center), as_dict=1):
			
			row = self.append('pmt_item', {})
			row.update(d)
		
