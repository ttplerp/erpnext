# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.model.document import Document
from erpnext.accounts.utils import make_asset_transfer_gl
from frappe.utils import getdate, nowdate
from erpnext.assets.asset_utils import check_valid_asset_transfer
from erpnext.custom_utils import get_branch_from_cost_center


class AssetMovement(Document):
	def validate(self):
		self.validate_cost_center()
		# self.validate_employee()
		self.validate_asset()
		self.posting_date = getdate(self.transaction_date) #required of transfer_gl

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
				# if d.to_employee:
				# 	frappe.throw(
				# 		_(
				# 			"Transferring cannot be done to an Employee. Please enter cost center where Asset {0} has to be transferred"
				# 		).format(d.asset),
				# 		title=_("Incorrect Movement Purpose"),
				# 	)
				if not d.target_cost_center and self.transfer_type == 'Cost Center To Cost Center':
					frappe.throw(_("Target Cost Center is required while transferring Asset {0}").format(d.asset))
				# if d.source_cost_center == d.target_cost_center:
				# 	frappe.throw(_("Source and Target Cost Center cannot be same"))

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
		for d in self.assets:
			if d.from_employee:
				current_custodian = frappe.db.get_value("Asset", d.asset, "custodian")

				if current_custodian != d.from_employee:
					frappe.throw(
						_("Asset {0} does not belongs to the custodian {1}").format(d.asset, d.from_employee)
					)

			if d.to_employee and frappe.db.get_value("Employee", d.to_employee, "company") != self.company:
				frappe.throw(
					_("Employee {0} does not belongs to the company {1}").format(d.to_employee, self.company)
				)

	def on_submit(self):
		self.set_latest_cost_center_in_asset()
		self.make_asset_transfer_gl_entry()

	def on_cancel(self):
		self.set_latest_cost_center_in_asset()
		self.cancel_asset_transfer_gl_entry()

	def make_asset_transfer_gl_entry(self):
		if self.purpose in ["Receipt","Issue"]:
			return

		for d in self.assets:
			if d.source_cost_center != d.target_cost_center and d.target_cost_center is not None:
				make_asset_transfer_gl(self, d.asset, self.transaction_date, d.source_cost_center, d.target_cost_center)
	
	def cancel_asset_transfer_gl_entry(self):
		if self.purpose in ["Receipt","Issue"]:
			return
		frappe.db.sql("delete from `tabGL Entry` where voucher_no = %s", self.name)

	def set_latest_cost_center_in_asset(self):
		current_cost_center, current_employee, current_employee_name, current_custodian_type = "", "", "", ""
		cond = "1=1"

		for d in self.assets:
			args = {"asset": d.asset, "company": self.company}

			# latest entry corresponds to current document's Cost Center, employee when transaction date > previous dates
			# In case of cancellation it corresponds to previous latest document's Cost Center, employee
			latest_movement_entry = frappe.db.sql(
				"""
				SELECT asm_item.target_cost_center, asm_item.target_custodian_type, asm_item.to_employee, asm_item.to_employee_name, 
					asm_item.to_desuup, asm_item.to_desuup_name, asm_item.to_other
				FROM `tabAsset Movement Item` asm_item, `tabAsset Movement` asm
				WHERE
					asm_item.parent=asm.name and
					asm_item.asset=%(asset)s and
					asm.company=%(company)s and
					asm.docstatus=1 and {0}
				ORDER BY
					asm.transaction_date desc limit 1
				""".format(
					cond
				),
				args, as_dict=True
			)
			# frappe.throw(str(latest_movement_entry))
			if latest_movement_entry:
				current_cost_center = latest_movement_entry[0]['target_cost_center']
				current_cost_center = current_cost_center if current_cost_center else d.source_cost_center
				current_custodian_type = latest_movement_entry[0]['target_custodian_type']
				if current_custodian_type == 'Employee':
					frappe.db.set_value("Asset", d.asset, "issue_to_employee", latest_movement_entry[0]['to_employee'])
					frappe.db.set_value("Asset", d.asset, "employee_name", latest_movement_entry[0]['to_employee_name'])
					frappe.db.set_value("Asset", d.asset, "issue_to_desuup", "")
					frappe.db.set_value("Asset", d.asset, "desuup_name", "")
					frappe.db.set_value("Asset", d.asset, "issue_to_other", "")
				elif current_custodian_type == 'Desuup':
					frappe.db.set_value("Asset", d.asset, "issue_to_desuup", latest_movement_entry[0]['to_desuup'])
					frappe.db.set_value("Asset", d.asset, "desuup_name", latest_movement_entry[0]['to_desuup_name'])
					frappe.db.set_value("Asset", d.asset, "issue_to_employee", "")
					frappe.db.set_value("Asset", d.asset, "employee_name", "")
					frappe.db.set_value("Asset", d.asset, "issue_to_other", "")
				else:
					frappe.db.set_value("Asset", d.asset, "issue_to_other", latest_movement_entry[0]['to_other'])
					frappe.db.set_value("Asset", d.asset, "issue_to_employee", "")
					frappe.db.set_value("Asset", d.asset, "employee_name", "")
					frappe.db.set_value("Asset", d.asset, "issue_to_desuup", "")
					frappe.db.set_value("Asset", d.asset, "desuup_name", "")
			
			frappe.db.set_value("Asset", d.asset, "cost_center", current_cost_center)
			branch = get_branch_from_cost_center(current_cost_center)
			frappe.db.set_value("Asset", d.asset, "branch", branch)
			frappe.db.set_value("Asset", d.asset, "issued_to", current_custodian_type)

			equipment = frappe.db.get_value("Equipment", {"asset_code": d.asset}, "name")
			if equipment:
				purpose = 'Cancel' if self.docstatus == 2 else ''
				save_equipment(equipment, branch, self.transaction_date, self.name, purpose)

	def save_equipment(equipment, branch, posting_date, ref_doc, purpose):
		equip = frappe.get_doc("Equipment", equipment)
		equip.branch = branch
		equip.create_equipment_history(branch, posting_date, ref_doc, purpose)
		equip.save()

	@frappe.whitelist()
	def get_asset_list(self):
		if not self.from_employee:
			frappe.throw("From Employee missing!")
		else:
			asset_list = frappe.db.sql("""
				select name, cost_center, issued_to, asset_name, description 
				from `tabAsset` 
				where issue_to_employee = '{}' 
				and docstatus = 1 
				""".format(self.from_employee),as_dict = 1)
			if asset_list:
				self.set("assets",[])
				for x in asset_list:
					row = self.append("assets",{})
					data = {
							"asset":x.name, 
							"asset_name":x.asset_name, 
							"description":x.description, 
							"from_employee":self.from_employee, 
							"from_employee_name":frappe.db.get_value("Employee", self.from_employee, 'employee_name'), 
							"source_cost_center": x.cost_center,
							"source_custodian_type": x.issued_to,
						}
					row.update(data)
