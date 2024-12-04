# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, get_first_day, get_last_day, getdate, get_datetime, today
from frappe.model.document import Document
from frappe.model.naming import make_autoname
from time import sleep

class DepreciationEntry(Document):
	def validate(self):
		self.set_schedule_dates()

	def on_submit(self):
		self.check_mandatory()
		self.process_depreciation_entry()

	def on_cancel(self):
		self.cancel_depreciation_entry(publish_progress=True)

	def on_cancel_after_draft(self):
		self.cancel_depreciation_entry(publish_progress=True)

	def validate_posting_date(self):
		if not (getdate(self.posting_date) >= getdate(self.from_date) and getdate(self.posting_date) <= getdate(self.to_date)):
			frappe.throw(_("<b>Posting Date</b> should be between <b>{}</b> and <b>{}</b>").format(str(self.from_date), str(self.to_date)))
		if getdate(self.posting_date) > getdate(today()):
			frappe.throw(_("<b>Posting Date</b> cannot be a future date"))

	def process_depreciation_entry(self):
		frappe.enqueue(process_depreciation_entry, job_name='DEPRECIATIONENTRY', timeout=1500, doc=self, publish_progress=True)
		# self.process_depreciation_entry()

	# def process_depreciation_entry(self):
	# 	self.make_gl_entries()
	# 	self.update_schedules()
	# 	self.set_value_after_depreciation()
	# 	self.update_asset_status()
	# 	frappe.db.commit()
	# 	frappe.msgprint(_("Depreciation Entry {} created successfully...").format(doc.name), alert=True)

	def cancel_depreciation_entry(self, publish_progress=False):
		title = 'Cancelling Depreciation Entry'
		# self.check_cbs_upload()
		show_progress(publish_progress, 5, 'Rollback changes on Depreciation Schedule...', title)
		self.update_schedules(cancel=True, publish_progress=publish_progress, title=title)
		show_progress(publish_progress, 25, 'Rollback changes on Assets...', title)
		self.set_value_after_depreciation()
		self.update_asset_status()
		show_progress(publish_progress, 50, 'Removing Depreciation Entry Details...', title)
		self.remove_depreciation_details()
		show_progress(publish_progress, 75, 'Removing GL Entries...', title)
		self.remove_gl_entries()
		show_progress(publish_progress, 100, 'Depreciation Entry cancelled successfully...', title)
		frappe.msgprint(_("Depreciation Entry {} cancelled successfully...").format(self.name), alert=True)

	def check_cbs_upload(self):
		cbs_entry = frappe.db.get_value("CBS Entry Upload", {"voucher_type": "Depreciation Entry", "voucher_no": self.name, "docstatus": ("!=",2)}, "cbs_entry")
		if cbs_entry:
			frappe.throw(_("Unable to cancel this entry as the depreciation expenses are already pushed to <b>CBS</b> via {}")\
							.format(frappe.get_desk_link("CBS Entry", cbs_entry)), title="Failed")

	def check_mandatory(self):
		if not flt(self.total_depreciation_amount):
			frappe.throw(_("No asset details found for processing Depreciation"))

	def make_gl_entries(self, publish_progress=False, title=None):
		gl_list = self.get_gl_entries(publish_progress, title)
		if not gl_list:
			return
		values = ', '.join(map(str, gl_list))
		frappe.db.sql("""INSERT INTO `tabGL Entry`(name, posting_date, account, 
					cost_center, against,
					debit, credit, account_currency, 
					debit_in_account_currency, credit_in_account_currency, 
					voucher_type, voucher_no, against_voucher_type, against_voucher,
					remarks, company, 
					owner, creation, modified_by, modified, docstatus, idx, is_opening, is_advance, 
					fiscal_year, use_cheque_lot)
				VALUES {}""".format(values))

	def get_gl_entries(self, publish_progress=False, title=None):
		gl_list = []
		asset_category = self.get_asset_category()
		li = frappe.db.sql("""select a.name asset, a.company, a.cost_center, a.branch, 
						a.asset_category, 
						ded.name, ded.schedule_date, 
						ded.depreciation_amount, ded.accumulated_depreciation_amount,
						ded.income_depreciation_amount, ded.income_accumulated_depreciation
					from `tabDepreciation Entry Detail` ded, `tabAsset` a
					where ded.depreciation_entry = "{}"
					and a.name = ded.parent
				""".format(self.name), as_dict=True)
		for i in li:
			if not i.cost_center:
				frappe.throw(_("Cost Center is missing for {}").format(frappe.get_desk_link("Asset", i.asset)))
			# elif not i.business_activity:
			# 	frappe.throw(_("Business Activity is missing for {}").format(frappe.get_desk_link("Asset", i.asset)))
			elif not i.asset_category:
				frappe.throw(_("Asset Category is mandatory for {}").format(frappe.get_desk_link("Asset Category", i.asset_category)))

			asset_category_account = asset_category[i.asset_category]
			if not asset_category_account or not len(asset_category_account):
				frappe.throw(_("Accounting details are missing for {}").format(frappe.get_desk_link("Asset Category", i.asset_category)))
			accumulated_depreciation_account = asset_category_account[0].accumulated_depreciation_account
			depreciation_expense_account 	 = asset_category_account[0].depreciation_expense_account

			for j in ('debit', 'credit'):
				gl_name = make_autoname('GLD.YY.MM.DD.######')
				gl_list.append((
					gl_name, str(self.posting_date), depreciation_expense_account if j == 'debit' else accumulated_depreciation_account, 
					i.cost_center, depreciation_expense_account if j == 'credit' else accumulated_depreciation_account,
					i.depreciation_amount if j == 'debit' else 0, i.depreciation_amount if j == 'credit' else 0, 'BTN', 
					i.depreciation_amount if j == 'debit' else 0, i.depreciation_amount if j == 'credit' else 0,
					'Depreciation Entry', self.name, "Asset", i.asset,
					'Depreciation for {}-{}'.format(str(self.month), str(self.fiscal_year)), self.company,
					frappe.session.user, str(get_datetime()), frappe.session.user, str(get_datetime()), 1, 0, 'No', 'No',
					getdate(self.to_date).strftime('%Y'), 0
				))
		return gl_list

	def update_schedules(self, cancel=False, publish_progress=False, title=None):
		cond = ""
		if cancel:
			cond = "depreciation_entry = NULL"
		else:
			cond = 'depreciation_entry = "{}"'.format(self.name)
		frappe.db.sql("""update `tabDepreciation Schedule` ds
				set {cond},
					modified = NOW(), modified_by = "{modified_by}"
				where ds.schedule_date between "{from_date}" and "{to_date}"
				and exists(select 1
						from `tabDepreciation Entry Detail` ded
						where ded.depreciation_entry = "{name}"
						and ded.name = ds.name)
		""".format(cond=cond, from_date=str(self.from_date), to_date=str(self.to_date), 
				modified_by=frappe.session.user, name=self.name))
		frappe.db.commit()

	def set_value_after_depreciation(self):
		# taking too long
		# li = frappe.db.sql("""select distinct(parent) asset_name from `tabDepreciation Entry Detail`
		# 						where depreciation_entry = "{}" order by parent""".format(self.name), as_dict=True)
		# for i in li:
		# 	asset = frappe.get_doc("Asset", i.asset_name)
		# 	asset.set_value_after_depreciation()
		# 	asset.set_status()
		# frappe.db.commit()
		frappe.db.sql("""update `tabAsset` a, `tabAsset Finance Book` b
			set b.value_after_depreciation = ifnull(a.gross_purchase_amount,0)
											 - ifnull(a.opening_accumulated_depreciation,0)
											 - ifnull((select sum(ifnull(ds.depreciation_amount,0))
												from `tabDepreciation Schedule` ds
												where ds.parent = a.name
												and (ifnull(ds.journal_entry,'') != '' or ifnull(ds.depreciation_entry,'') != '')
												),0)
			where b.parent=a.name and exists(select 1
				from `tabDepreciation Entry Detail` ded
				where ded.depreciation_entry = "{}"
				and ded.parent = a.name)
			""".format(self.name))
		frappe.db.commit()

	def update_asset_status(self):
		frappe.db.sql("""update `tabAsset` a
			set a.status = (CASE 
								WHEN journal_entry_for_scrap IS NOT NULL THEN 'Scrapped'
								WHEN status = 'Sold' THEN status
								WHEN ifnull(value_after_depreciation,0) <= ifnull(expected_value_after_useful_life,0) THEN 'Fully Depreciated'
								WHEN ifnull(value_after_depreciation,0) < ifnull(gross_purchase_amount) THEN 'Partially Depreciated'
								ELSE status
							END), 
				a.disable_depreciation = (CASE
											WHEN (CASE 
												WHEN journal_entry_for_scrap IS NOT NULL THEN 'Scrapped'
												WHEN status = 'Sold' THEN status
												WHEN ifnull(value_after_depreciation,0) <= ifnull(expected_value_after_useful_life,0) THEN 'Fully Depreciated'
												WHEN ifnull(value_after_depreciation,0) < ifnull(gross_purchase_amount) THEN 'Partially Depreciated'
												ELSE status
												END) NOT IN ('Submitted', 'Partially Depreciated') THEN 1
											WHEN asset_status IN ('Auctioned', 'Marked for Auction') THEN 1
											ELSE 0
										END) 
			where exists(select 1
				from `tabDepreciation Entry Detail` ded
				where ded.depreciation_entry = "{}"
				and ded.parent = a.name)
			""".format(self.name))
		frappe.db.commit()

	def remove_gl_entries(self):
		frappe.db.sql(""" delete from `tabGL Entry` where voucher_type = "Depreciation Entry" and voucher_no="{}" """.format(self.name))

	def get_asset_category(self):
		asset_category = frappe._dict()
		for i in frappe.db.get_all("Asset Category"):
			doc = frappe.get_doc("Asset Category", i.name)
			asset_category.setdefault(i.name, doc.get('accounts'))
		return asset_category

	def set_schedule_dates(self):
		month_id = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"].index(self.month[:3])
		month_id = str(month_id+1).rjust(2, "0")
		self.from_date = getdate("-".join([self.fiscal_year, month_id, "01"]))
		self.to_date = get_last_day(getdate(self.from_date))

		if str(self.posting_date)[0:4] != self.fiscal_year:
			frappe.throw(_("Posting date should be within fiscal year <b>{}</b>").format(self.fiscal_year))
		elif str(self.posting_date) < str(self.from_date):
			frappe.throw(_("Posting date cannot be beyond <b>{}</b>").format(self.from_date))
		elif getdate(self.posting_date) > getdate(today()):
			frappe.throw(_("<b>Posting Date</b> cannot be a future date"))

	@frappe.whitelist()
	def get_depreciation_details(self):
		if self.docstatus != 0:
			return
		self.create_depreciation_details()

	def create_depreciation_details(self, publish_progress=False, title=None):
		self.set_schedule_dates()
		self.remove_depreciation_details()
		depreciation_schedules = frappe.db.sql("""
			select ds.name, "{depreciation_entry}" as dep_entry,
				ds.schedule_date, ds.depreciation_amount, ds.accumulated_depreciation_amount, 
				ds.income_depreciation_amount, ds.income_accumulated_depreciation,
				ds.parent, ds.idx, ds.owner, ds.creation, ds.modified, ds.modified_by
			from `tabAsset` a, `tabDepreciation Schedule` ds
			where a.docstatus = 1
			and a.disable_depreciation = 0
			and ds.parent = a.name
			and ds.schedule_date between "{from_date}" and "{to_date}"
			and ds.depreciation_amount > 0
			and ifnull(ds.journal_entry, '') = ''
			and ifnull(ds.depreciation_entry, '') = ''
			and not exists(select 1
						from `tabDepreciation Entry Detail` ded
						where ded.name = ds.name
						and ded.depreciation_entry != "{depreciation_entry}"
						and ded.docstatus != 2)
			and not exists(
				select 1 from `tabJournal Entry` je,
				`tabJournal Entry Account` jea
				where jea.parent = je.name
				and je.voucher_type = 'Depreciation Entry'
				and jea.reference_name = a.name
				and je.posting_date between "{from_date}" and "{to_date}"
				and je.docstatus = 1
			)
			order by a.name
		""".format(depreciation_entry = self.name, from_date = str(self.from_date), to_date=str(self.to_date)))
		if len(depreciation_schedules) > 0:
			for a in depreciation_schedules:
				frappe.db.sql("""
					insert into `tabDepreciation Entry Detail` (name, depreciation_entry, 
						schedule_date, depreciation_amount, accumulated_depreciation_amount, 
						income_depreciation_amount, income_accumulated_depreciation,
						parent, idx, owner, creation, modified, modified_by)
					VALUES('{}','{}','{}',{},{},{},{},'{}',{},'{}','{}','{}','{}')
					""".format(a[0], a[1], a[2], a[3], a[4], a[5], a[6], a[7], a[8], a[9], a[10], a[11], a[12]))
		# frappe.db.sql("""
		# 	insert into `tabDepreciation Entry Detail` (name, depreciation_entry, 
		# 		schedule_date, depreciation_amount, accumulated_depreciation_amount, 
		# 		income_depreciation_amount, income_accumulated_depreciation,
		# 		parent, idx, owner, creation, modified, modified_by)
		# 	select ds.name, "{depreciation_entry}",
		# 		ds.schedule_date, ds.depreciation_amount, ds.accumulated_depreciation_amount, 
		# 		ds.income_depreciation_amount, ds.income_accumulated_depreciation,
		# 		ds.parent, ds.idx, ds.owner, ds.creation, ds.modified, ds.modified_by
		# 	from `tabAsset` a, `tabDepreciation Schedule` ds
		# 	where a.docstatus = 1
		# 	and a.disable_depreciation = 0
		# 	and ds.parent = a.name
		# 	and ds.schedule_date between "{from_date}" and "{to_date}"
		# 	and ds.depreciation_amount > 0
		# 	and ifnull(ds.journal_entry, '') = ''
		# 	and ifnull(ds.depreciation_entry, '') = ''
		# 	and not exists(select 1
		# 				from `tabDepreciation Entry Detail` ded
		# 				where ded.name = ds.name
		# 				and ded.depreciation_entry != "{depreciation_entry}"
		# 				and ded.docstatus != 2)
		# 	and not exists(
		# 		select 1 from `tabJournal Entry` je,
		# 		`tabJournal Entry Account` jea
		# 		where jea.parent = je.name
		# 		and je.voucher_type = 'Depreciation Entry'
		# 		and jea.reference_name = a.name
		# 		and je.posting_date between "{from_date}" and "{to_date}"
		# 		and je.docstatus = 1
		# 	)
		# 	order by a.name
		# """.format(depreciation_entry = self.name, from_date = str(self.from_date), to_date=str(self.to_date)))
		self.update_summary()
		self.save()
		self.reload()

	def remove_depreciation_details(self):
		frappe.db.sql(""" delete from `tabDepreciation Entry Detail` where depreciation_entry="{}" """.format(self.name))

	def update_summary(self):
		self.set('summary', [])
		self.total_noof_assets 		= 0
		self.total_noof_schedules 	= 0
		self.total_depreciation_amount = 0

		li = frappe.db.sql("""select a.asset_category, 
							COUNT(DISTINCT(a.name)) noof_assets, COUNT(*) noof_schedules, 
							sum(d.depreciation_amount) total_depreciation
						from `tabDepreciation Entry Detail` d, `tabAsset` a
						where d.depreciation_entry = "{}"
						and a.name = d.parent
						group by a.asset_category""".format(self.name), as_dict=True)
		total_noof_assets, total_noof_schedules, total_depreciation_amount = 0, 0, 0
		for i in li:
			row = self.append('summary', {})
			row.update(i)
			total_noof_assets 	 += i.noof_assets
			total_noof_schedules += i.noof_schedules
			total_depreciation_amount += i.total_depreciation
		self.total_noof_assets = total_noof_assets
		self.total_noof_schedules = total_noof_schedules
		self.total_depreciation_amount = total_depreciation_amount

def show_progress(publish_progress, progress, description, title=None):
	if publish_progress:
		frappe.publish_progress(progress, 
						title = title if title else _("No Title..."),
						description = description)
		sleep(1)

@frappe.whitelist()
def process_depreciation_entry(doc, publish_progress=False):
	title = 'Processing Depreciation Entry'
	show_progress(publish_progress, 5, 'Creating GL Entries...', title)
	doc.make_gl_entries(publish_progress, title)
	show_progress(publish_progress, 25, 'Updating Depreciation Schedules...', title)
	doc.update_schedules()
	show_progress(publish_progress, 50, 'Updating Assets...', title)
	doc.set_value_after_depreciation()
	show_progress(publish_progress, 75, 'Updating Assets...', title)
	doc.update_asset_status()
	show_progress(publish_progress, 99, 'Complted successfully...', title)
	frappe.db.commit()
	frappe.msgprint(_("Depreciation Entry {} created successfully...").format(doc.name), alert=True)
