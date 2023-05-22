# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_first_day, get_last_day, add_to_date, flt
from erpnext.controllers.accounts_controller import AccountsController
from erpnext.accounts.general_ledger import make_gl_entries

class ProcessRentalBilling(AccountsController):
	def check_mandatory(self):
		for f in ['month', 'fiscal_year', 'branch', 'dzongkhag']:
			if not self.get(f):
				frappe.msgprint(_("Please set {0}").format(_(self.meta.get_label(f))), raise_exception=True)
	
	@frappe.whitelist()
	def get_tenant_list(self, process_type=None):
		# frappe.throw("tenant list")
		self.check_mandatory()
		rental_bill_date = self.posting_date
		month_start = get_first_day(rental_bill_date)
		month_end = get_last_day(rental_bill_date)
		condition = " and t1.building_category != 'Pilot Housing' and t1.branch = '{}'".format(self.branch)
		if self.dzongkhag:
			condition += " and t1.dzongkhag = '{dzongkhag}'".format(dzongkhag=self.dzongkhag)
		if self.ministry_agency:
			condition += " and t1.ministry_and_agency = '{ministry_agency}'".format(ministry_agency=self.ministry_agency)
		if self.tenant:
			condition += " and t1.name = '{tenant}'".format(tenant=self.tenant)

		if process_type == "create":
			# if self.tenant:
			# 	condition += " and t1.name = '{tenant}'".format(tenant=self.tenant)
			tenant_list = frappe.db.sql("""
				   	select t1.name
				   	from `tabTenant Information` t1
				   	where t1.docstatus = "1"
				   	and t1.status="Allocated" and t1.allocated_date <= '{month_end_date}'
				   	{cond}
				   	and not exists(select 1
						from `tabRental Bill` as t2
						where t2.tenant = t1.name
						and t2.docstatus != 2
						and t2.fiscal_year = '{fiscal_year}'
						and t2.month = '{month}'
					)
				   	order by t1.ministry_and_agency
			""".format(fiscal_year=self.fiscal_year, month=self.month, month_start_date=month_start, month_end_date=month_end, cond=condition), as_dict=True)
		else:
			# if self.tenant:
			# 	condition += " and t1.tenant = '{tenant}'".format(tenant=self.tenant)
			tenant_list = frappe.db.sql("""
						select t1.name
						from `tabRental Bill` as t1
						where t1.fiscal_year = '{fiscal_year}'
						and t1.month = '{month}'
						and t1.gl_entry = 0 and t1.docstatus != 2
						{cond}
						order by t1.branch, t1.name
				""".format(fiscal_year=self.fiscal_year, month=self.month, cond=condition), as_dict=True)

		return tenant_list

	@frappe.whitelist()
	def process_rental(self, process_type=None, name=None):
		# msg = '<span style="color:red;"> FAILED. Previous month rentall bill might not have process or <br/> rental charges might be missing in tenant information</span>'
		# format_string = 'href="#Form/Rental Bill/{0}"'.format('THI23001')
		# return {"msg":'<tr><td>{0}</td><td>{1}</td></tr>'.format('THI23001', msg), "flag":1}
		flag = 1
		self.check_permission('write')
		msg=""
		if name:
			try:
				if process_type == "create":
					# bill_date = self.fiscal_year+"-"+self.month+"-"+"01"
					posting_date = self.posting_date
					if self.month == "01":
						prev_fiscal_year = int(self.fiscal_year) - 1
						prev_month = "12"
					else:
						prev_fiscal_year = int(self.fiscal_year)
						prev_month = str(int(self.month) - 1).zfill(2)
					
					yearmonth = str(self.fiscal_year) + str(self.month)
					previous_bill_date = str(prev_fiscal_year)+"-"+str(prev_month)+"-"+"01"

					query = """
							select tenant_cid, tenant_name, customer_code, block, flat, 
							ministry_and_agency, location_name, branch, tenant_department_name, dzongkhag, 
							town_category, building_category, is_nhdcl_employee, rental_amount, building_classification,
							phone_no, allocated_date
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
				
							""".format(posting_date=posting_date, name=name, prev_fiscal_year=prev_fiscal_year, prev_month=prev_month, previous_bill_date=previous_bill_date)
							# or '{previous_bill_date}' between t.m_start_date and t.m_end_date, keep provision to process bill when the flat was under maintenance
					dtls = frappe.db.sql(query, as_dict=True)
					if dtls:
						for d in dtls:
							cost_center = frappe.db.get_value("Branch", d.branch, "cost_center")
							if not self.company:
								self.company = frappe.db.get_value("Branch", d.branch, "company")
							focals = frappe.db.sql("""select rental_focal, focal_name from `tabRental Focal and Agency` r inner join `tabRental Focal and Agency Item` i On i.parent=r.name 
											where r.is_active=1 and i.dzongkhag='{dzongkhag}' and i.ministry_and_agency='{ministry_and_agency}'""".format(dzongkhag=d.dzongkhag, ministry_and_agency=d.ministry_and_agency), as_dict=1)
							if not len(focals):
								frappe.throw("Missing Rental Focal and Agency master for Dzongkhag: {0} and Ministry and Agency: {1} OR it's inactive.".format(d.dzongkhag, d.ministry_and_agency))
							rb = frappe.get_doc({
								"doctype": "Rental Bill",
								"tenant": str(name),
								"tenant_cid" : str(d.tenant_cid),
								"customer_code": str(d.customer_code),
								"posting_date": posting_date,
								"tenant_name": str(d.tenant_name),
								"block_no": d.block,
								"fiscal_year": self.fiscal_year,
								"month": self.month,
								"flat_no": d.flat,
								"ministry_agency": d.ministry_and_agency,
								"location": d.location_name,
								"branch": d.branch,
								"department": d.tenant_department_name,
								"dzongkhag": d.dzongkhag,
								"town_category": d.town_category,
								"building_category": d.building_category,
								"building_classification": d.building_classification,
								"yearmonth": yearmonth,
								"rent_amount": d.rental_amount,
								"receivable_amount": d.rental_amount,
								"cost_center": cost_center,
								"company": self.company,
								"is_nhdcl_employee": d.is_nhdcl_employee,
								"rental_focal": focals[0]['rental_focal'],
								"focal_name": focals[0]['focal_name']
							})
							rb.insert()
							# rb_no = frappe.db.get_value("Rental Bill", {"tenant":name, "month":self.month, "fiscal_year": self.fiscal_year, "docstatus":0}, "name")
						msg = "Rental Bill Created Successfully for {0} amount Nu. {1}".format(d.tenant_name, d.rental_amount)
					else:
						flag = 0
						msg = "<span style='color:red;'> FAILED: Previous month rentall bill might be missing for tenant: {0} </span>".format(name)
				else:
					if process_type == "remove":
						rental_bill_status = frappe.db.get_value("Rental Bill", name, "docstatus")
						if rental_bill_status != 1:
							rb_list = frappe.db.sql("delete from `tabRental Bill` where name='{0}'".format(name))
							frappe.db.commit()
							msg = "Rental Bill Removed Successfully"
						else:
							flag = 0
							msg = "Rental Bill not allowed to be removed as it's already submitted"
					else:
						cost_center = frappe.db.get_value("Branch", self.branch, "cost_center")
						revenue_claim_account = frappe.db.get_single_value("Rental Account Setting", "revenue_claim_account")
						for a in frappe.db.sql("""
								select t.name as rental_bill, t.tenant, c.name as customer, t.receivable_amount, t.building_category
								from `tabRental Bill` t left join `tabCustomer` c on t.customer_code = c.customer_code
								where t.name = '{name}'
							""".format(name=name), as_dict=True):
							gl_entries = []
							pre_rent_account = frappe.db.get_single_value("Rental Account Setting", "pre_rent_account")
							pre_rent_amount = frappe.db.sql("""
													select ifnull(sum(credit) - sum(debit), 0) as pre_rent_amount
													from `tabGL Entry` 
													Where party_type='Customer' 
													and party = '{party}' and account = '{account}' and is_cancelled=0
												""".format(party=a.customer, account=pre_rent_account))[0][0]
							pre_rent_adjustment_amount, balance_receivable_amount = 0,0
							if pre_rent_amount > 0:
								if a.receivable_amount <= pre_rent_amount:
									pre_rent_adjustment_amount = flt(a.receivable_amount)
								else:
									pre_rent_adjustment_amount = flt(pre_rent_amount)
									balance_receivable_amount = flt(a.receivable_amount) - flt(pre_rent_amount)

								gl_entries.append(
									self.get_gl_dict({
										"account": pre_rent_account,
										"debit": flt(pre_rent_adjustment_amount),
										"debit_in_account_currency": flt(pre_rent_adjustment_amount),
										"voucher_no": a.rental_bill,
										"voucher_type": "Rental Bill",
										"cost_center": cost_center,
										"party": a.customer,
										"party_type": "Customer",
										"company": self.company,
										"remarks": str(a.tenant) + " Monthly Rental Bill for Year " + str(self.fiscal_year) + " Month " + str(self.month),
										# "business_activity": business_activity
									})
								)
							else:
								balance_receivable_amount = flt(a.receivable_amount)
							
							if balance_receivable_amount > 0:
								gl_entries.append(
									self.get_gl_dict({
										"account": revenue_claim_account,
										"debit": flt(balance_receivable_amount),
										"debit_in_account_currency": flt(balance_receivable_amount),
										"voucher_no": a.rental_bill,
										"voucher_type": "Rental Bill",
										"cost_center": cost_center,
										'party': a.customer,
										'party_type': 'Customer',
										"company": self.company,
										"remarks": str(a.tenant) + " Monthly Rental Bill for Year " + str(self.fiscal_year) + " Month " + str(self.month),
										# "business_activity": business_activity
									})
								)
							credit_account = frappe.db.get_value("Rental Account Setting Item",{"building_category":a.building_category}, "account")

							gl_entries.append(
								self.get_gl_dict({
									"account": credit_account,
									"credit": flt(a.receivable_amount),
									"credit_in_account_currency": flt(a.receivable_amount),
									"voucher_no": a.rental_bill,
									"voucher_type": "Rental Bill",
									"cost_center": cost_center,
									"company": self.company,
									"remarks": str(a.tenant) + " Rental Bill for " + str(a.building_category) +" Year "+ str(self.fiscal_year) + " Month " +str(self.month),
									# "business_activity": business_activity
									})
								)
							make_gl_entries(gl_entries, cancel=(self.docstatus == 2), update_outstanding="No", merge_entries=False)

							doc = frappe.get_doc("Rental Bill", a.rental_bill)
							doc.gl_entry=1
							doc.adjusted_amount=flt(pre_rent_adjustment_amount)
							doc.outstanding_amount=flt(a.receivable_amount) - flt(pre_rent_adjustment_amount)
							doc.submit()

						# rb = frappe.get_doc("Rental Bill", name)
						# rb.submit()
						msg = "Rental Bill Submitted Successfully"

				return {"msg": '<tr><td>{0}</td><td>{1}</td></tr>'.format(name, msg), "flag": flag}
			except Exception as e:
				flag = 0
				return {"msg": '<div style="color:red;"> Error: Tenant :{1} - {0}</div>'.format(str(e), name), "flag": flag}

