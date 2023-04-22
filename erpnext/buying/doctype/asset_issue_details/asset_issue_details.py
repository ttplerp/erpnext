# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, cint, formatdate
from frappe.model.naming import make_autoname

class AssetIssueDetails(Document):
	# Added by Jai, 2 June, 2022
	def autoname(self):
		year = formatdate(self.entry_date, "YYYY")
		month = formatdate(self.entry_date, "MM")
		self.name = make_autoname(str("AID") + '.{}.{}.####'.format(year, month))
	
	def validate(self):
		pass
	
	# def before_save(self):
	#     frappe.msgprint(_("ITEM CODE: " + "{}").format(self.item_code))
	#     frappe.msgprint(_("PURCHASE RECEIPT: " + "{}").format(self.purchase_receipt))
	
	def check_qty_balance(self):
		total_qty = frappe.db.sql("""select sum(ifnull(qty,0)) total_qty 
								  from `tabAsset Received Entries`
								  where item_code="{}"
								  and ref_doc = "{}"
								  and docstatus = 1""".format(self.item_code, self.purchase_receipt))[0][0]
		issued_qty = frappe.db.sql("""select sum(ifnull(qty,0)) issued_qty
								   from `tabAsset Issue Details` 
								   where item_code ="{}"
								   and purchase_receipt = "{}"
								   and docstatus = 1 
								   and name != "{}" """.format(self.item_code, self.purchase_receipt, self.name))[0][0]
		
		balance_qty = flt(total_qty) - flt(issued_qty)
		if flt(self.qty) > flt(balance_qty):
			frappe.throw(_("Issuing Quantity cannot be greater than Balance Quantity i.e., {}").format(flt(balance_qty)), title="Insufficient Balance")
			
	def on_submit(self):
		self.check_qty_balance()
		
		item_doc = frappe.get_doc("Item",self.item_code)
		if not cint(item_doc.is_fixed_asset):
			frappe.throw(_("Item selected is not a fixed asset"))

		if item_doc.asset_category:
			asset_category = frappe.db.get_value("Asset Category", item_doc.asset_category, "name")
			fixed_asset_account, credit_account=frappe.db.get_value("Asset Category Account", {'parent':asset_category}, ['fixed_asset_account','credit_account'])
			if item_doc.asset_sub_category:
				check = frappe.db.sql("select 1 from `tabAsset Category` ac where '{0}' in (select name from `tabAsset Sub Category` asbc where asbc.asset_category = ac.name)".format( item_doc.asset_sub_category), as_dict=1)
				if check:
					for a in frappe.db.sql("select total_number_of_depreciations, income_depreciation_percent from `tabAsset Finance Book` where parent = '{0}' and `asset_sub_category`='{1}'".format(asset_category, item_doc.asset_sub_category), as_dict=1):
						total_number_of_depreciations = a.total_number_of_depreciations
						depreciation_percent = a.depreciation_percent
				else:
					frappe.throw(_("{} sub category do not exist for particular Asset Category").format(item_doc.asset_sub_category))
			else:
				frappe.throw(_("No Asset Sub-Category for Item: " +"{}").format(self.item_name))
		else:
			frappe.throw(_("<b>Asset Category</b> is missing for material {}").format(frappe.get_desk_link("Item", self.item_code)))

		item_data = frappe.db.get_value(
			"Item", self.item_code, ["asset_naming_series", "asset_category","asset_sub_category"], as_dict=1
		)

		qc = 0
		while (qc < self.qty):
			asset = frappe.get_doc(
				{
					"doctype": "Asset",
					"item_code": self.item_code,
					"asset_name": self.item_name,
					"description": self.item_description,
					# "naming_series": item_data.get("asset_naming_series") or "AST",
					"cost_center": self.receiving_cost_center,
					"company": self.company,
					"purchase_date": self.purchase_date,
					"calculate_depreciation": 1,
					"asset_rate": self.asset_rate,
					"purchase_receipt_amount": self.asset_rate,
					"gross_purchase_amount": self.asset_rate,
					"asset_quantity": 1,
					"purchase_receipt": self.purchase_receipt,
					"purchase_invoice": None,
					"next_depreciation_date": self.issued_date,
					"credit_account": credit_account,
					"asset_account": fixed_asset_account,
					"aid_reference": self.name,
					"business_activity": self.business_activity,
					"issued_to": self.issued_to,
					"issue_to_employee": self.issue_to_employee if self.issued_to == 'Employee' else None,
					"employee_name": self.employee_name if self.issued_to == 'Employee' else None,
					"issue_to_desuup": self.issue_to_desuup if self.issued_to == 'Desuup' else None,
					"desuup_name": self.desuup_name if self.issued_to == 'Desuup' else None,
					"issue_to_other": self.issue_to_other if self.issued_to == 'Other' else None,
				}
			)

			asset.flags.ignore_validate = True
			asset.flags.ignore_mandatory = True
			asset.set_missing_values()
			asset.insert()
			frappe.db.commit()
			qc += 1

	def on_cancel(self):
		for d in frappe.db.sql("select * from `tabAsset` where aid_reference='{}'".format(self.name), as_dict=1):
			if d.docstatus < 2:
				frappe.throw("You cannot cancel the document before cancelling Asset with code <a href='#Form/Asset/{0}'>{0}</a>".format(d.name))

# Following code added by SHIV on 2021/05/13
def get_permission_query_conditions(user):
	if not user: user = frappe.session.user
	user_roles = frappe.get_roles(user)

	if user == "Administrator" or "System Manager" in user_roles: 
		return

	return """(
		exists(select 1
			from `tabEmployee` as e
			where e.branch = `tabAsset Issue Details`.branch
			and e.user_id = '{user}')
		or
		exists(select 1
			from `tabEmployee` e, `tabAssign Branch` ab, `tabBranch Item` bi
			where e.user_id = '{user}'
			and ab.employee = e.name
			and bi.parent = ab.name
			and bi.branch = `tabAsset Issue Details`.branch)
	)""".format(user=user)

@frappe.whitelist()
def check_item_code(doctype, txt, searchfield, start, page_len, filters):
	cond = ""    
	if filters.get('item_code'):
		cond += " item_code = '{}'".format(filters.get('item_code'))
	query = "select ref_doc from `tabAsset Received Entries` where {cond}".format(cond=cond)
 
	return frappe.db.sql(query)
