# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt, cint
from datetime import date
from erpnext.assets.doctype.asset.depreciation import scrap_asset
from erpnext.assets.doctype.asset.depreciation import get_disposal_account_and_cost_center

class BulkAssetDisposal(Document):
	def validate(self): 
		# self.scrap_date = date.today()
		if self.scrap == "Sale Asset":
			self.valdiate_asset_category()

			if not self.branch:
				frappe.throw("Branch is required to make Sales Invoice.")

	def valdiate_asset_category(self):
		if not self.asset_category:
			return
			
		if self.item:
			for data in self.item:
				category = frappe.db.get_value("Asset", data.asset, "asset_category")
				if category != self.asset_category:
					frappe.throw("{} is under <b>{}</b> category. You can only sell from {} category!".format(data.asset, category, self.asset_category))

	def on_submit(self):
		if self.scrap == "Scrap Asset":
			self.scrap_asset()
		# else: 
		# 	self.sale_asset()
	
	def before_cancel(self):
		if self.scrap == "Scrap Asset":
			for a in self.item:
				vad_reverse = 0
				jv = frappe.get_doc("Journal Entry", frappe.db.get_value("Asset", a.asset, "journal_entry_for_scrap"))
				jede = frappe.db.sql("""
							select journal_entry, name, depreciation_amount from `tabDepreciation Schedule` where parent = '{0}' and year(schedule_date) = year('{1}')
							and month(schedule_date) = month('{1}') and journal_entry is not NULL
                         """.format(a.asset, self.scrap_date), as_dict=1)
				if jede:
					vad_reverse += flt(jede[0].depreciation_amount,2)
					jede_doc = frappe.get_doc("Journal Entry", jede[0].journal_entry)
					frappe.db.sql("update `tabDepreciation Schedule` set journal_entry = NULL where name = '{}'".format(jede[0].journal_entry))
					jede_doc.cancel()
					
				frappe.db.sql("update `tabAsset` set journal_entry_for_scrap = NULL, disposal_date = NULL, value_after_depreciation = value_after_depreciation+{} where name = '{}'".format(vad_reverse, a.asset))
				jv.cancel()

	def on_cancel(self):
		self.revert_asset()
	
	def scrap_asset(self):
		# Enqueue the heavy work per asset to avoid request timeout
		for data in self.item:
			# Use frappe.enqueue to run the worker in background. Pass asset and scrap_date.
			# Set timeout and queue as needed (timeout in seconds, eg: 300)
			frappe.enqueue(
				method="erpnext.assets.doctype.bulk_asset_disposal.bulk_asset_disposal._scrap_asset_worker",
				asset=data.asset,
				scrap_date=self.scrap_date,
				queue="long", # use long queue for heavy jobs
				tag="bulk_asset_disposal",
				timeout=600,
			)

			# depreciation_schedules = frappe.db.sql(
			# 	"""select name, journal_entry from `tabDepreciation Schedule` where parent = %s and schedule_date > %s and journal_entry is not NULL""",
			# 	(data.asset, self.scrap_date), as_dict=True,
			# )

			# for ds in depreciation_schedules:
			# 	if ds.get('journal_entry'):
			# 		frappe.db.sql(
			# 			"delete from `tabGL Entry` where voucher_no=%s and voucher_type='Journal Entry'",
			# 			ds.get('journal_entry'),
			# 		)
			# 		frappe.db.sql("delete from `tabJournal Entry Account` where parent=%s", ds.get('journal_entry'))
			# 		frappe.db.sql("delete from `tabJournal Entry` where name=%s", ds.get('journal_entry'))

			# 	frappe.db.sql("update `tabDepreciation Schedule` set journal_entry = NULL where name = %s", ds.get('name'))

			# scrap_asset(data.asset, self.scrap_date)

	#Written by Thukten for cancel
	def revert_asset(self):
		if self.sales_invoice:
			doc = frappe.get_doc("Sales Invoice", self.sales_invoice)
			doc.bulk_asset_disposal = ""
			doc.cancel()

		for a in self.get("item"):
			frappe.db.sql("update `tabAsset` set status = '{}' where name = '{}'".format(a.status, a.asset))		

@frappe.whitelist()
def sale_asset(branch, business_activity, name, scrap_date, customer, posting_date):
	item = frappe.db.sql("""select a.item_code, a.item_name, a.asset, a.uom
						from `tabBulk Asset Disposal Item` as a, `tabBulk Asset Disposal` as b 
						where a.parent = b.name 
						and b.name='{name}' 
						and a.docstatus = 1 
						and b.scrap_date = '{date}' 
						and b.scrap='Sale Asset'
						""".format(name=name, date=scrap_date),as_dict=1)
	si = frappe.new_doc("Sales Invoice")
	si.branch = branch
	si.business_activity = business_activity
	si.company = frappe.defaults.get_user_default("company")
	si.customer = customer
	si.set_posting_time = 1
	si.posting_date = posting_date
	company = frappe.defaults.get_user_default("company")
	si.currency = frappe.get_cached_value('Company', company ,  "default_currency")
	disposal_account, depreciation_cost_center = get_disposal_account_and_cost_center(company)
	si.bulk_asset_disposal = name
	for data in item:
		si.append("items", {
			"item_code": data.item_code,
			"item_name":data.item_name,
			"is_fixed_asset": 1,
			"asset": data.asset,
			"uom": data.uom,
			"income_account": disposal_account,
			# "serial_no": serial_no,
			"cost_center": depreciation_cost_center,
			"qty": 1,
			"business_activity":business_activity, 
			"rate": 0
		})
	return si


# Worker function to be executed via frappe.enqueue
def _scrap_asset_worker(asset, scrap_date, **kwargs):
	"""
	Background worker that removes future depreciation entries for an asset
	and then calls the existing scrap_asset from the depreciation module.
	This mirrors the logic previously executed synchronously in
	BulkAssetDisposal.scrap_asset.
	"""
	# Remove future depreciation entries, created due to rescheduling work
	try:
		# kwargs may include worker metadata such as 'job_id', 'tag', etc.
		if kwargs:
			frappe.log_error(message=str(kwargs), title="bulk_asset_disposal.worker_kwargs")
		# depreciation_schedules = frappe.db.sql(
		# 	"""select name, journal_entry, depreciation_amount, income_depreciation_amount, finance_book_id from `tabDepreciation Schedule` where parent = %s and schedule_date > %s and (journal_entry is not NULL or journal_entry != '')""",
		# 	(asset, scrap_date), as_dict=True,
		# )

		# for ds in depreciation_schedules:
		# 	asset_doc = frappe.get_doc("Asset", asset)
		# 	idx = cint(ds.finance_book_id)
		# 	finance_books = asset_doc.get("finance_books")[idx - 1]
		# 	finance_books.value_after_depreciation += ds.depreciation_amount
		# 	finance_books.income_tax_value_after_depreciation += ds.income_depreciation_amount
		# 	finance_books.db_update()

		# 	if ds.get('journal_entry'):
		# 		# Delete GL entries, journal entry accounts and journal entry
		# 		frappe.db.sql(
		# 			"delete from `tabGL Entry` where voucher_no=%s and voucher_type='Journal Entry'",
		# 			ds.get('journal_entry'),
		# 		)
		# 		frappe.db.sql("delete from `tabJournal Entry Account` where parent=%s", ds.get('journal_entry'))
		# 		frappe.db.sql("delete from `tabJournal Entry` where name=%s", ds.get('journal_entry'))

		# 	frappe.db.sql("update `tabDepreciation Schedule` set journal_entry = NULL where name = %s", ds.get('name'))

		# Finally call the depreciation scrap_asset function
		# (imported at top of module)
		scrap_asset(asset, scrap_date)
	except Exception:
		# Log exception but don't raise so worker doesn't crash silently
		frappe.log_error(frappe.get_traceback(), "bulk_asset_disposal._scrap_asset_worker")
