# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

class EquipmentTransfer(Document):

	def on_submit(self):
		self.validate_items()
		self.update_equipment()

	def on_cancel(self):
		self.update_equipment(cancel=True)

	def validate_items(self):
		if not self.items:
			frappe.throw(
				"At least one equipment is required to submit this transfer.",
				title="Equipment Missing"
			)
		
		for item in self.items:
			if not item.to_branch:
				frappe.throw(
					"Please specify the destination branch for the equipment: {}.".format(
						frappe.bold(item.equipment)
					),
					title="Destination Branch Missing"
				)
			
			if item.to_branch == self.branch:
				frappe.throw(
					"Cannot transfer equipment {} to the same branch ({}). Please select a different destination branch.".format(
						frappe.bold(item.equipment), frappe.bold(item.to_branch)
					),
					title="Invalid Transfer"
				)

	def update_equipment(self, cancel=False):
		for item in self.items:
			equipment_doc = frappe.get_doc("Equipment", item.equipment)
			
			if cancel:
				equipment_doc.branch = self.branch
				equipment_doc.cost_center = self.cost_center
			else:
				equipment_doc.branch = item.to_branch
				equipment_doc.cost_center = item.to_cost_center
			
			equipment_doc.save(ignore_permissions=True)

	def make_filters(self):
		filters = frappe._dict(
			company=self.company,
			branch=self.branch
		)
		return filters

	@frappe.whitelist()
	def fill_equipment_details(self):
		filters = self.make_filters()
		equipments = get_equipment_list(filters=filters, as_dict=True)
		self.set("items", [])

		if not equipments:
			error_msg = _(
				"No equipments found for the mentioned criteria:<br>Company: {0}"
			).format(
				frappe.bold(self.company),
			)
			frappe.throw(error_msg, title=_("No equipments found"))

		self.set("items", equipments)

def get_equipment_list(
	filters,
	as_dict=True,
) -> list:
	Equipment = frappe.qb.DocType("Equipment")
	query = (
		frappe.qb.from_(Equipment)
		.where(
			(Equipment.status == "Running")
			& (Equipment.company == filters.company)
			& (Equipment.branch == filters.branch)
			
		)
		.select(
			Equipment.name.as_("equipment"),
			Equipment.rate_per_hour,
		)
	)
	return query.run(as_dict=as_dict)

