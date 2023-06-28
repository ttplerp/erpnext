# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.utils import flt, cint, nowdate, getdate, formatdate
from frappe.model.document import Document
from erpnext.custom_workflow import validate_workflow_states, notify_workflow_states

class AssetMovement(Document):
	def validate(self):
		# validate_workflow_states(self)
		self.check_for_targets()
		self.validate_cost_center()
		self.validate_employee()
		self.validate_asset()
	
	def check_for_targets(self):
		for idx, d in enumerate(self.assets):
			if d.target_cost_center and d.to_employee and idx == idx:
				frappe.throw("Target Cost Center and To Employee cannot be used together at Row: <b>{}</b>".format(idx+1))

	def validate_asset(self):
		for d in self.assets:
			status, company = frappe.db.get_value("Asset", d.asset, ["status", "company"])
			if self.purpose == "Transfer" and status in ("Draft", "Scrapped", "Sold"):
				frappe.throw(_("{0} asset cannot be transferred").format(status))

			if company != self.company:
				frappe.throw(_("Asset {0} does not belong to company {1}").format(d.asset, self.company))

			if not (d.source_cost_center or d.target_cost_center or d.from_employee or d.to_employee):
				frappe.throw(_("Either Cost Center or employee must be required"))

	def validate_cost_center(self):
		for d in self.assets:
			if self.purpose in ["Transfer", "Issue"]:
				if not d.source_cost_center:
					d.source_cost_center = frappe.db.get_value("Asset", d.asset, "cost_center")

				if not d.source_cost_center:
					frappe.throw(_("Source Cost Center is required for the Asset {0}").format(d.asset))

				if d.source_cost_center:
					current_cost_center = frappe.db.get_value("Asset", d.asset, "cost_center")

					if current_cost_center != d.source_cost_center:
						frappe.throw(
							_("Asset {0} does not belongs to the Cost Center {1}").format(d.asset, d.source_cost_center)
						)

			if self.purpose == "Issue":
				if d.target_cost_center:
					frappe.throw(
						_(
							"Issuing cannot be done to a Cost Center. Please enter employee who has issued Asset {0}"
						).format(d.asset),
						title=_("Incorrect Movement Purpose"),
					)
				if not d.to_employee:
					frappe.throw(_("Employee is required while issuing Asset {0}").format(d.asset))

			if self.purpose == "Transfer":
				if not d.target_cost_center and not d.to_employee:
					frappe.throw(_("Target Cost Center/ To Employee is required while transferring Asset {0}").format(d.asset))
				if d.source_cost_center == d.target_cost_center:
					frappe.throw(_("Source and Target Cost Center cannot be same"))

			if self.purpose == "Receipt":
				# only when asset is bought and first entry is made
				if not d.source_cost_center and not (d.target_cost_center or d.to_employee):
					frappe.throw(
						_("Target Cost Center or To Employee is required while receiving Asset {0}").format(d.asset)
					)
				elif d.source_cost_center:
					# when asset is received from an employee
					if d.target_cost_center and not d.from_employee:
						frappe.throw(
							_("From employee is required while receiving Asset {0} to a Target Cost Center").format(
								d.asset
							)
						)
					if d.from_employee and not d.target_cost_center:
						frappe.throw(
							_("Target Cost Center is required while receiving Asset {0} from an employee").format(d.asset)
						)
					if d.to_employee and d.target_cost_center:
						frappe.throw(
							_(
								"Asset {0} cannot be received at a cost center and given to employee in a single movement"
							).format(d.asset)
						)

	def validate_employee(self):
		for idx, d in enumerate(self.assets):
			if d.from_employee:
				current_custodian = self.from_employee
				if current_custodian != d.from_employee:
					frappe.throw(
						_("Asset {0} does not belongs to the custodian {1}").format(d.asset, d.from_employee)
					)
				
			if d.to_employee and frappe.db.get_value("Employee", d.to_employee, "company") != self.company:
				frappe.throw(
					_("Employee {0} does not belongs to the company {1}").format(d.to_employee, self.company)
				)
			
			if d.to_employee and d.to_employee == self.from_employee:
				frappe.throw(
					_("Row {}: From Employee and To Employee cannot be same").format(d.idx, d.to_employee)
				)

	def on_submit(self):
		self.set_latest_cost_center_in_asset()

	def on_cancel(self):
		self.set_latest_cost_center_in_asset(cancel=1)

	def set_latest_cost_center_in_asset(self, cancel=None):
		for d in self.assets:
			if cint(cancel) == 1:
				custodian = d.from_employee
				custodian_name = d.from_employee_name
				cost_center = d.source_cost_center
				branch = frappe.db.get_value("Branch", {"cost_center": d.source_cost_center}, "name")
			else:
				custodian = d.to_employee
				custodian_name = d.to_employee_name
				cost_center = d.target_cost_center if d.target_cost_center else frappe.db.get_value("Employee", d.to_employee, "cost_center")
			
			if d.from_employee != d.to_employee:
				frappe.db.set_value("Asset", d.asset, "custodian", custodian)
				frappe.db.set_value("Asset", d.asset, "custodian_name", custodian_name)
			
			if d.source_cost_center != d.target_cost_center:
				branch = frappe.db.get_value("Branch", {'cost_center':cost_center}, "name")
				frappe.db.set_value("Asset", d.asset, "cost_center", cost_center)
				frappe.db.set_value("Asset", d.asset, "branch", branch)
			
	@frappe.whitelist()
	def get_asset_list(self):
		if self.transfer_from == "Employee" and not self.from_employee:
			frappe.throw("From Employee is mandatory")
		elif self.transfer_from == "Cost Center" and not self.from_cost_center:
			frappe.throw("From Cost Center is mandatory")
		else:
			if self.transfer_from == "Employee":
				asset_list = frappe.db.sql("""
					SELECT name
					FROM `tabAsset`
					WHERE custodian = %s AND docstatus = 1
					AND status NOT IN ('Scrapped', 'Sold')
					""", self.from_employee, as_dict=1)

				if asset_list:
					self.set("assets", [])
					for x in asset_list:
						row = self.append("assets", {})
						data = {
							"asset": x.name,
							"from_employee": self.from_employee,
							"source_cost_center": frappe.db.get_value("Employee", self.from_employee, "cost_center"),
						}
						row.update(data)
				else:
					frappe.throw("No Asset Record Found")
			else:
				asset_list = frappe.db.sql("""
					SELECT name
					FROM `tabAsset`
					WHERE (custodian = '' OR custodian IS NULL)
					AND cost_center = %s
					AND docstatus = 1
					AND status NOT IN ('Scrapped', 'Sold')
					""", self.from_cost_center, as_dict=1)

				if asset_list:
					self.set("assets", [])
					for x in asset_list:
						row = self.append("assets", {})
						data = {
							"asset": x.name,
							"source_cost_center": self.from_cost_center,
						}
						row.update(data)
				else:
					frappe.throw("No Asset Record Found")

def get_permission_query_conditions(user):
	if not user: user = frappe.session.user
	user_roles = frappe.get_roles(user)

	if user == "Administrator" or "System Manager" in user_roles: 
		return

	return """(
		exists(select 1
			from `tabEmployee` as e
			where e.branch = `tabAsset Movement`.branch
			and e.user_id = '{user}')
		or
		exists(select 1
			from `tabEmployee` e, `tabAssign Branch` ab, `tabBranch Item` bi
			where e.user_id = '{user}'
			and ab.employee = e.name
			and bi.parent = ab.name
			and bi.branch = `tabPurchase Invoice`.branch)
	)""".format(user=user)
			