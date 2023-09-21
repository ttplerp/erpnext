# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import get_first_day, get_last_day, add_to_date, flt

class RentalBillEntry(Document):
	def before_submit(self):
		if not self.number_of_rental_bills:
			frappe.throw("No data to Submit.")
			
	def check_mandatory(self):
		for f in ['month', 'fiscal_year', 'branch', 'posting_date']:
			if not self.get(f):
				frappe.msgprint(_("Please set {0}").format(_(self.meta.get_label(f))), raise_exception=True)
	
	@frappe.whitelist()
	def get_tenant_list(self):
		# frappe.throw("tenant list")
		self.check_mandatory()
		self.set('items', [])
		rental_bill_date = self.posting_date
		month_start = get_first_day(rental_bill_date)
		month_end = get_last_day(rental_bill_date)

		if self.month == "01":
			prev_fiscal_year = int(self.fiscal_year) - 1
			prev_month = "12"
		else:
			prev_fiscal_year = int(self.fiscal_year)
			prev_month = str(int(self.month) - 1).zfill(2)

		condition = " and t1.building_category != 'Pilot Housing' and t1.branch = '{}'".format(self.branch)
		if self.dzongkhag:
			condition += " and t1.dzongkhag = '{dzongkhag}'".format(dzongkhag=self.dzongkhag)
		if self.ministry_agency:
			condition += " and t1.ministry_and_agency = '{ministry_agency}'".format(ministry_agency=self.ministry_agency)
		if self.tenant:
			condition += " and t1.name = '{tenant}'".format(tenant=self.tenant)

		tenant_list = frappe.db.sql("""
				select t1.name tenant, t1.tenant_name tenant_name
				from `tabTenant Information` t1
				where t1.docstatus = "1"
				and t1.status="Allocated" and t1.allocated_date <= '{month_end_date}'
				{cond}
				and (exists(select 1
					from `tabRental Bill` as t3
					where t3.tenant = t1.name
					and t3.docstatus != 2 
					and t3.fiscal_year = '{prev_fiscal_year}'
					and t3.month = '{prev_month}'
				) 
				or not exists(select 1
					from `tabRental Bill` as t2
					where t2.tenant = t1.name
					and t2.docstatus != 2
				))
				order by t1.dzongkhag, t1.name
		""".format(fiscal_year=self.fiscal_year, month=self.month, month_start_date=month_start, month_end_date=month_end, cond=condition, prev_fiscal_year=prev_fiscal_year, prev_month=prev_month), as_dict=True)

		for d in tenant_list:
			row = self.append('items', {})
			row.update(d)
		
		self.db_set("number_of_rental_bills", len(tenant_list))
		# return self.number_of_rental_bills

	@frappe.whitelist()
	def create_rental_bill(self):
		posting_date = self.posting_date
		if self.month == "01":
			prev_fiscal_year = int(self.fiscal_year) - 1
			prev_month = "12"
		else:
			prev_fiscal_year = int(self.fiscal_year)
			prev_month = str(int(self.month) - 1).zfill(2)
		
		previous_bill_date = str(prev_fiscal_year)+"-"+str(prev_month)+"-"+"01"

		rb_count = 0
		successful = 0
		failed = 0
		for f in self.get("items"):
			rb_count += 1
			error=''
			try:
				query = """
					select tenant_cid, tenant_name, customer, block, flat, block_no, flat_no,
					ministry_and_agency, location_name, branch, tenant_department_name, dzongkhag, 
					town_category, building_category, is_nhdcl_employee, rental_amount, building_classification,
					phone_no, allocated_date, locations, employment_type
					from `tabTenant Information` t 
					inner join `tabTenant Rental Charges` r 
					on t.name = r.parent 
					where '{posting_date}' between r.from_date and r.to_date
					and (exists(select 1
							from `tabRental Bill` as t2
							where t2.tenant = t.name
							and t2.docstatus != 2 
							and t2.fiscal_year = '{prev_fiscal_year}'
							and t2.month = '{prev_month}'
						) 
						or not exists(select 1
							from `tabRental Bill` as t3
							where t3.tenant = '{name}'
							and t3.docstatus != 2   
						)
					
					)
					and t.name = '{name}';
		
					""".format(posting_date=posting_date, name=f.tenant, prev_fiscal_year=prev_fiscal_year, prev_month=prev_month, previous_bill_date=previous_bill_date)

				dtls = frappe.db.sql(query, as_dict=True)
				if dtls:
					for d in dtls:
						cost_center = frappe.db.get_value("Branch", d.branch, "cost_center")
						if not self.company:
							self.company = frappe.db.get_value("Branch", d.branch, "company")
						""" calc. property mgt. amount """
						total_property_mgt_amount = frappe.db.get_value("Flat No", d.flat_no, "total_property_management_amount")
						total_property_management_amount = prop_mgt_amount = 0
						for pm_item in frappe.db.sql("select * from `tabProperty Management Item` where is_percent=1 and parent='{}'".format(d.flat_no), as_dict=1):
							prop_mgt_amount = flt(d.rental_amount * (pm_item.percent / 100), 2)
							total_property_mgt_amount += prop_mgt_amount
						total_property_management_amount = total_property_mgt_amount if total_property_mgt_amount > 0 else 0

						rb = frappe.get_doc({
							"doctype": "Rental Bill",
							"tenant": str(f.tenant),
							"tenant_cid" : str(d.tenant_cid),
							"customer": str(d.customer),
							"posting_date": posting_date,
							"tenant_name": str(d.tenant_name),
							"block_no": d.block,
							"fiscal_year": self.fiscal_year,
							"month": self.month,
							"flat_no": d.flat,
							"flat_id": d.flat_no,
							"ministry_agency": d.ministry_and_agency,
							"location": d.location_name,
							"branch": d.branch,
							"department": d.tenant_department_name,
							"dzongkhag": d.dzongkhag,
							"town_category": d.town_category,
							"building_category": d.building_category,
							"building_classification": d.building_classification,
							"rent_amount": d.rental_amount,
							"receivable_amount": flt(d.rental_amount + total_property_management_amount),
							"cost_center": cost_center,
							"company": self.company,
							"is_nhdcl_employee": d.is_nhdcl_employee,
							"property_management_amount": total_property_management_amount,
							"rental_bill_entry": self.name,
							"employment_type": d.employment_type,
						})
						rb.insert()
						successful += 1
			except Exception as e:
				error = str(e)
				failed += 1

			rental_bill_entry_item = frappe.get_doc("Rental Bill Entry Item", {"parent": rb.rental_bill_entry, "tenant": rb.tenant})
			if error:
				rental_bill_entry_item.db_set("status", "Failed")
				rental_bill_entry_item.db_set("error_msg", error)
			else:
				rental_bill_entry_item.db_set("rental_bill", rb.name)
				rental_bill_entry_item.db_set("status", "Success")
				rental_bill_entry_item.db_set("rental_focal", rb.rental_focal)
				rental_bill_entry_item.db_set("rental_amount", rb.receivable_amount)
		
		rental_bill_entry = frappe.get_doc("Rental Bill Entry", self.name)
		if failed > 0 and failed < successful:
			rental_bill_entry.db_set("bill_created",1)
		elif failed == 0 and successful > 0:
			rental_bill_entry.db_set("bill_created",1)
		elif successful == 0 and failed > 0:
			rental_bill_entry.db_set("bill_created",0)
		rental_bill_entry.db_set("number_of_rental_bills", rb_count)
		rental_bill_entry.db_set("successful", successful)
		rental_bill_entry.db_set("failed", failed)
		rental_bill_entry.reload()
			
	@frappe.whitelist()
	def submit_rental_bill(self):
		successful = 0
		failed = 0
		for f in self.get("items"):
			error = ''
			try:
				doc = frappe.get_doc("Rental Bill", f.rental_bill)
				doc.submit()
				successful += 1
			except Exception as e:
				error = str(e)
				failed += 1

			rental_bill_entry_item = frappe.get_doc("Rental Bill Entry Item", {"parent": self.name, "tenant": f.tenant})
			if error:
				rental_bill_entry_item.db_set("status", "Failed")
				rental_bill_entry_item.db_set("error_msg", error)
			else:
				rental_bill_entry_item.db_set("status", "Submitted")
		
		rental_bill_entry = frappe.get_doc("Rental Bill Entry", self.name)
		if failed > 0 and failed < successful:
			rental_bill_entry.db_set("bill_submitted",1)
		elif failed == 0 and successful > 0:
			rental_bill_entry.db_set("bill_submitted",1)
		elif successful == 0 and failed > 0:
			rental_bill_entry.db_set("bill_submitted",0)
		rental_bill_entry.db_set("successful", successful)
		rental_bill_entry.db_set("failed", failed)
		rental_bill_entry.reload()

	@frappe.whitelist()
	def remove_rental_bill(self):
		for f in self.get("items"):
			# if f.rental_bill:
			# 	frappe.db.delete("Rental Bill", {"name": f.rental_bill, "docstatus": 0})

			rental_bill_entry_item = frappe.get_doc("Rental Bill Entry Item", {"parent": self.name, "tenant": f.tenant})
			rental_bill_entry_item.db_set("status", "")
			rental_bill_entry_item.db_set("rental_bill", "")
			rental_bill_entry_item.db_set("rental_amount", 0.00)
			if rental_bill_entry_item.error_msg:
				rental_bill_entry_item.db_set("error_msg", "")
		
		rental_bill_entry = frappe.get_doc("Rental Bill Entry", self.name)
		rental_bill_entry.db_set("number_of_rental_bills",0)
		rental_bill_entry.db_set("bill_created",0)
		rental_bill_entry.db_set("bill_submitted",0)
		rental_bill_entry.db_set("successful", 0)
		rental_bill_entry.db_set("failed", 0)
		rental_bill_entry.reload()