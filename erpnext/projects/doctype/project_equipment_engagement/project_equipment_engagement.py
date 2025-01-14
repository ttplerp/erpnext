# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt
from frappe.model.document import Document

class ProjectEquipmentEngagement(Document):
	def validate(self):
		self.validate_items()

	def validate_items(self):
		total_amount = 0.0
		for d in self.items:
			# if not d.rate:
			# 	frappe.throw("Please set Rate/Hr in {}".format(frappe.get_desk_link("Equipment", d.equipment)))
			total_amount += flt(d.amount)
		self.total_amount = flt(total_amount)

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
		self.set("equipments", [])

		if not equipments:
			error_msg = _(
				"No equipments found for the mentioned criteria:<br>Company: {0}"
			).format(
				frappe.bold(self.company),
			)
			frappe.throw(error_msg, title=_("No equipments found"))

		self.set("equipments", equipments)

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
