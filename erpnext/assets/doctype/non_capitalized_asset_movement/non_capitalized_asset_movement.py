# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

class NonCapitalizedAssetMovement(Document):
	def validate(self):
		self.validate_asset()
		self.validate_location()
		self.validate_employee()

	def validate_asset(self):
		for d in self.items:
			status, company = frappe.db.get_value("Non Capitalized Asset", d.asset, ["status", "company"])
			# if self.purpose == "Transfer" and status in ("Draft", "Scrapped", "Sold"):
			if self.purpose == "Transfer" and status in ("Draft"):
				frappe.throw(_("{0} asset cannot be transferred").format(status))

			if company != self.company:
				frappe.throw(_("Asset {0} does not belong to company {1}").format(d.asset, self.company))

			if not (d.source_location or d.target_location or d.from_employee or d.to_employee):
				frappe.throw(_("Either location or employee must be required"))


	def validate_location(self):
		for d in self.items:
			if self.purpose in ["Transfer", "Issue"]:
				current_location = frappe.db.get_value("Non Capitalized Asset", d.asset, "location")
				if d.source_location:
					if current_location != d.source_location:
						frappe.throw(
							_("Asset {0} does not belongs to the location {1}").format(
								d.asset, d.source_location
							)
						)
				else:
					d.source_location = current_location

			if self.purpose == "Issue":
				if d.target_location:
					frappe.throw(
						_(
							"Issuing cannot be done to a location. Please enter employee to issue the Asset {0} to"
						).format(d.asset),
						title=_("Incorrect Movement Purpose"),
					)
				if not d.to_employee:
					frappe.throw(_("Employee is required while issuing Asset {0}").format(d.asset))

			if self.purpose == "Transfer":
				if d.to_employee:
					frappe.throw(
						_(
							"Transferring cannot be done to an Employee. Please enter location where Asset {0} has to be transferred"
						).format(d.asset),
						title=_("Incorrect Movement Purpose"),
					)
				if not d.target_location:
					frappe.throw(
						_("Target Location is required while transferring Asset {0}").format(d.asset)
					)
				if d.source_location == d.target_location:
					frappe.throw(_("Source and Target Location cannot be same"))

			if self.purpose == "Receipt":
				if not (d.source_location) and not (d.target_location or d.to_employee):
					frappe.throw(
						_("Target Location or To Employee is required while receiving Asset {0}").format(
							d.asset
						)
					)
				elif d.source_location:
					if d.from_employee and not d.target_location:
						frappe.throw(
							_(
								"Target Location is required while receiving Asset {0} from an employee"
							).format(d.asset)
						)
					elif d.to_employee and d.target_location:
						frappe.throw(
							_(
								"Asset {0} cannot be received at a location and given to an employee in a single movement"
							).format(d.asset)
						)

	def validate_employee(self):
		for d in self.items:
			if d.from_employee:
				current_custodian = frappe.db.get_value("Non Capitalized Asset", d.asset, "custodian")

				if current_custodian != d.from_employee:
					frappe.throw(
						_("Asset {0} does not belongs to the custodian {1}").format(d.asset, d.from_employee)
					)

			if d.to_employee and frappe.db.get_value("Employee", d.to_employee, "company") != self.company:
				frappe.throw(
					_("Employee {0} does not belongs to the company {1}").format(d.to_employee, self.company)
				)

	def on_submit(self):
		self.set_latest_location_and_custodian_in_asset()
		self.update_asset_history()

	def on_cancel(self):
		self.set_latest_location_and_custodian_in_asset()
		self.update_asset_history(cancel=True)

	def set_latest_location_and_custodian_in_asset(self):
		current_location, current_employee = "", ""
		cond = "1=1"

		for d in self.items:
			args = {"asset": d.asset, "company": self.company}

			# latest entry corresponds to current document's location, employee when transaction date > previous dates
			# In case of cancellation it corresponds to previous latest document's location, employee
			latest_movement_entry = frappe.db.sql(
				f"""
				SELECT asm_item.target_location, asm_item.to_employee
				FROM `tabNon Capitalized Asset Movement Item` asm_item, `tabNon Capitalized Asset Movement` asm
				WHERE
					asm_item.parent=asm.name and
					asm_item.asset=%(asset)s and
					asm.company=%(company)s and
					asm.docstatus=1 and {cond}
				ORDER BY
					asm.posting_date desc limit 1
				""",
				args,
			)
			if latest_movement_entry:
				current_location = latest_movement_entry[0][0]
				current_employee = latest_movement_entry[0][1]

			if self.purpose == "Transfer":
				frappe.db.set_value("Non Capitalized Asset", d.asset, "location", current_location, update_modified=False)
				
			elif self.purpose == "Issue":
				frappe.db.set_value("Non Capitalized Asset", d.asset, "custodian", current_employee, update_modified=False)
				frappe.db.set_value("Non Capitalized Asset", d.asset, "custodian_name", frappe.db.get_value("Employee", {'name': current_employee}, "employee_name"), update_modified=False)
			else:
				frappe.db.set_value("Non Capitalized Asset", d.asset, "location", current_location, update_modified=False)
				frappe.db.set_value("Non Capitalized Asset", d.asset, "custodian", "", update_modified=False)

			if current_location and current_employee:
				frappe.msgprint("Asset received at Location '{0}' and issued to Employee {1}".format(
						frappe.get_desk_link("Location", current_location),
						frappe.get_desk_link("Employee", current_employee),
					)
				)
			
			elif current_location:
				frappe.msgprint("Asset transferred to Location {}".format(
						frappe.get_desk_link("Location", current_location)
					))
				
			elif current_employee:
				frappe.msgprint(
					_("Asset issued to Employee {0}".format(frappe.get_desk_link("Employee", current_employee))
					)
				)

	def update_asset_history(self, cancel=False):
		if cancel:
			frappe.db.sql("delete from `tabNon Capitalized Asset History` where reference_name='{}'".format(self.name))
			for d in self.items:
				doc = frappe.get_doc("Non Capitalized Asset", d.asset)
				doc.location = d.source_location
				doc.custodian = d.from_employee
				doc.save(ignore_permissions=True)
		else:
			for d in self.items:
				doc = frappe.get_doc("Non Capitalized Asset", d.asset)
				row = doc.append("asset_history", {})
				row.reference_name          = self.name
				row.branch          		= self.branch
				row.from_date         		= doc.posting_date
				row.to_date           		= self.posting_date
				if self.purpose == "Transfer":
					row.location     			= d.target_location
				elif self.purpose == "Issue":
					row.custodian     			= d.to_employee
					row.location     			= d.source_location

				elif self.purpose == "Receipt":
					row.location     			= d.target_location
				row.type          		= self.purpose

				row.save(ignore_permissions=True)

	def make_filters(self):
		filters = frappe._dict(
			company=self.company,
			branch=self.branch
		)
		return filters

	@frappe.whitelist()
	def fill_asset_details(self):
		filters = self.make_filters()
		assets = get_asset_list(filters=filters, as_dict=True)
		self.set("items", [])

		if not assets:
			error_msg = _(
				"No assets found for the mentioned criteria:<br>Company: {0}"
			).format(
				frappe.bold(self.company),
			)
			frappe.throw(error_msg, title=_("No equipments found"))

		self.set("items", assets)

def get_asset_list(
	filters,
	as_dict=True,
) -> list:
	Asset = frappe.qb.DocType("Non Capitalized Asset")
	query = (
		frappe.qb.from_(Asset)
		.where(
			(Asset.status == "Usable")
			& (Asset.company == filters.company)
			& (Asset.branch == filters.branch)
			
		)
		.select(
			Asset.name.as_("asset"),
			Asset.asset_name,
			Asset.location.as_("source_location"),
		)
	)
	return query.run(as_dict=as_dict)

