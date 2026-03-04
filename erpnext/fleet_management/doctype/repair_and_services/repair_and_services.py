# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from erpnext.custom_utils import check_future_date
from erpnext.controllers.stock_controller import StockController
from frappe.utils import flt, cint, nowdate, time_diff_in_hours, nowtime
from frappe import _, qb, throw
from frappe.model.mapper import get_mapped_doc
from erpnext.custom_workflow import validate_workflow_states
from erpnext.stock.stock_ledger import get_valuation_rate
from erpnext.stock.get_item_details import get_bin_details

class RepairAndServices(StockController):
	def __init__(self, *args, **kwargs):
		super(RepairAndServices, self).__init__(*args, **kwargs)

	def validate(self):
		# validate_workflow_states(self)
		self.update_items()
		self.validate_rate()
		self.calculate_total_amount()
		self.calculate_tds_amount()
		self.calculate_gst()
		self.update_outstanding_amount()

	def on_submit(self):
		if not self.bill_no or not self.bill_date:
			frappe.throw("Please set Bill number and Bill date.")
		self.post_repair_and_service_invoice()
		
	def validate_rate(self):
		for i in self.items:
			if not i.maintain_stock and self.out_source and i.rate <= 0:
				frappe.throw("Rate at Row# {} cannot be {}.".format(i.idx, i.rate))

	def update_stock_ledger(self):
		sl_entries = []
		for a in self.items:
			if a.maintain_stock:
				sl_entries.append(
					self.get_sl_entries(
						a,
						{
							"actual_qty": -1 * flt(a.qty),
							"warehouse": a.warehouse,
							"incoming_rate": 0,
						},
					)
				)

		if self.docstatus == 2:
			sl_entries.reverse()
		self.make_sl_entries(sl_entries, self.amended_from and "Yes" or "No")

	def calculate_total_amount(self):
		self.total_amount = self.net_amount = 0
	
		deduction = self.calculate_deductions()
		addition  = self.calculate_additions()

		
		for a in self.items:
			a.charge_amount = flt(flt(a.rate) * flt(a.qty))
			self.total_amount += flt(a.charge_amount)

		self.net_amount = flt(self.total_amount) - flt(deduction) + flt(addition)


	def calculate_tds_amount(self):
		tds_amount = 0.0
		if self.tds_percent and self.tds_account:
			tds_amount = flt(self.tds_percent)/100 * flt(self.net_amount)
		self.tds_amount = flt(tds_amount)

	def calculate_deductions(self):
		deduction = 0.0
		if self.deductions:
			for d in self.deductions:
				deduction += flt(d.amount)
		self.deduction_amount = flt(deduction)
		return deduction

	def calculate_additions(self):
		addition = 0.0
		if self.additions:
			for d in self.additions:
				addition += flt(d.amount)
		self.addition_amount = flt(addition)
		return addition

	def calculate_gst(self):
		self.gst_amount = 0.0
		self.gst_account = ""
		
		if self.apply_gst and self.taxes_and_charges:
			tax_template = frappe.get_doc("Purchase Taxes and Charges Template", self.taxes_and_charges)
			if tax_template.taxes:
				for tax in tax_template.taxes:
					if tax.charge_type == "On Net Total":
						self.gst_amount = flt(self.net_amount) * flt(tax.rate) / 100
					elif tax.charge_type == "Actual":
						self.gst_amount = flt(tax.tax_amount)
					
					if tax.account_head:
						self.gst_account = tax.account_head
					
					break

	def update_outstanding_amount(self):
		outstanding = flt(self.net_amount) + flt(self.gst_amount) - flt(self.tds_amount)
		self.outstanding_amount = outstanding
		self.grand_total = outstanding

	def update_items(self):
		for a in self.items:
			if cint(a.maintain_stock) == 1:
				if not a.warehouse:
					a.warehouse = self.set_warehouse
				a.rate = get_valuation_rate(
					a.item_code,
					a.warehouse,
					self.doctype,
					self.name,
					company=self.company,
				)
				a.cost_center = self.cost_center
				a.charge_amount = flt(a.qty) * flt(a.rate)
				a.expense_account = frappe.db.get_value(
					"Item Default", {"parent": a.item_code}, "expense_account"
				)

	def post_repair_and_service_invoice(self):
		doc = frappe.new_doc("Repair And Service Invoice")
		doc.update({
			"doctype": "Repair And Service Invoice",
			"posting_date": self.posting_date,
			"repair_and_services_type": self.repair_and_services_type,
			"branch": self.branch,
			"party_type": self.party_type,
			"party": self.party,
			"equipment": self.equipment,
			"cost_center": self.cost_center,
			"bill_no": self.bill_no,
			"bill_date": self.bill_date,
			"settle_imprest_advance": 1 if self.imprest_settlement else 0,
			"imprest_party": self.imprest_party if self.imprest_settlement else "",
			"company": self.company,
			"grand_total": self.grand_total,
			"total_amount": self.total_amount,
			"outstanding_amount": self.outstanding_amount,
			"deduction_amount": self.deduction_amount,
			"addition_amount": self.addition_amount,
			"repair_and_services": self.name,
			"gst_account": self.gst_account, 
			"gst_amount": self.gst_amount,
			"tds_percent": self.tds_percent if self.tds_percent and self.tds_amount > 0 else "",
			"tds_amount": self.tds_amount if self.tds_percent and self.tds_amount > 0 else 0,
			"tds_account": self.tds_account if self.tds_percent and self.tds_amount > 0 else "",
		})

		if self.items:
			for item in self.items:
				doc.append("items", {
					"type" : item.type,
					"item_code" : item.item_code,
					"item_name" : item.item_name,
					"rate" : item.rate,
					"qty" : item.qty,
					"parts_no" : item.parts_no,
					"maintain_stock" : item.maintain_stock,
					"remarks" : item.remarks,
				})

		if self.deductions:
			for d in self.deductions:
				doc.append("deductions", {
					"deduction_type": d.deduction_type,
					"account": d.account,
					"amount": d.amount,
				})
		if self.additions:
			for d in self.additions:
				doc.append("additions", {
					"addition_type": d.addition_type,
					"account": d.account,
					"amount": d.amount,
				})

		doc.insert()
		frappe.msgprint(
			_("Repair And Service Invoice {} has been successfully posted.").format(
				frappe.get_desk_link(doc.doctype, doc.name)
			)
		)

	@frappe.whitelist()
	def get_imprest_advance_account(self):
		if not frappe.db.get_value("Company", self.company, "imprest_advance_account"):
			frappe.throw("Please set Imprest Advance Account in Company Settings")
		return frappe.db.get_value("Company", self.company, "imprest_advance_account")

@frappe.whitelist()
def make_mr(source_name, target_doc=None):
	if frappe.db.exists("Material Request", {"repair_and_services": source_name}):
		frappe.throw("Material Request already exists for this transaction")

	def set_missing_values(source, target):
		target.material_request_type = "Material Issue"
		for a in source.items:
			if a.maintain_stock == 1 and a.qty > 0:
				row = target.append("items", {})
				row.warehouse = a.warehouse
				row.item_code = a.item_code
				row.item_name = a.item_name
				row.uom = a.uom
				row.stock_uom = a.uom
				row.qty = flt(a.qty)
				row.rate = flt(a.rate)
				row.cost_center = a.cost_center
				row.issue_to_equipment = source.equipment
				row.amount = flt(a.charge_amount)
				row.actual_qty = get_bin_details(
					a.item_code, a.warehouse, source.company
				)["actual_qty"]

	def update_item(obj, target, source_parent):
		target.issue_to_equipment = source_parent.equipment
		target.stock_uom = obj.uom

	doclist = get_mapped_doc(
		"Repair And Services",
		source_name,
		{
			"Repair And Services": {
				"doctype": "Material Request",
				"field_map": {"repair_and_services": "name"},
			},
		},
		target_doc,
		set_missing_values,
	)
	return doclist

def get_permission_query_conditions(user):
	if not user:
		user = frappe.session.user
	user_roles = frappe.get_roles(user)

	if user == "Administrator" or "System Manager" in user_roles:
		return

	return """(
		`tabRepair And Services`.owner = '{user}'
		or
		exists(select 1
			from `tabEmployee` as e
			where e.branch = `tabRepair And Services`.branch
			and e.user_id = '{user}')
		or
		exists(select 1
			from `tabEmployee` e, `tabAssign Branch` ab, `tabBranch Item` bi
			where e.user_id = '{user}'
			and ab.employee = e.name
			and bi.parent = ab.name
			and bi.branch = `tabRepair And Services`.branch)
	)""".format(
		user=user
	)