# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import formatdate, flt, getdate, add_days, add_months
from calendar import monthrange
from datetime import date
from erpnext.accounts.general_ledger import make_gl_entries
from frappe.model.naming import make_autoname
from erpnext.controllers.accounts_controller import AccountsController
from collections import defaultdict

class RentalBill(AccountsController):
	def autoname(self):
		if not self.dzongkhag:
			frappe.throw("Dzongkhag name is missing")
		if not frappe.db.get_value("Dzongkhag", self.dzongkhag, "rental_dzo_abbr"):
			frappe.throw("Dzongkhag Abbr is missing in Dzongkhag master")

		# dz = self.dzongkhag
		# dzo_prefix = dz[:3]
		abbr = frappe.db.get_value("Dzongkhag", self.dzongkhag, "rental_dzo_abbr")
		prefix = abbr.upper()
		
		bill_code = "RB" + str(prefix) + "/" + str(formatdate(self.fiscal_year, "YY")) + str(self.month) + '/.####'
		self.name = make_autoname(bill_code)
	def validate(self):
		self.set_missing_value()
		self.set_rental_amount()
		""" provision to check if Payment Entry is cancelled or not """

	def on_submit(self):
		self.make_gl_entry()
	
	def on_cancel(self):
		self.ignore_linked_doctypes = (
			"GL Entry",
			"Payment Ledger Entry",
		)
		# account_frozen_date = frappe.db.get_single_value("Accounts Settings", "acc_frozen_upto")
		# if getdate(self.posting_date) < getdate(account_frozen_date):
		# 	frappe.throw("Not permitted to Cancel this Document.")
		# frappe.db.sql("delete from `tabGL Entry` where voucher_no = '{}'".format(self.name))
		self.make_gl_entry()
	
	def set_missing_value(self):
		self.is_nhdcl_employee = 1 if frappe.db.get_value("Tenant Information", self.tenant, "is_nhdcl_employee") else 0
		if not self.cost_center:
			self.cost_center = frappe.db.get_value("Branch", self.branch, "cost_center")
		if not self.company:
			self.company = frappe.db.get_value("Branch", self.branch, "company")
		# if self.employment_type == "Civil Servant":
		for k in ['dzongkhag', 'ministry_agency']:
			if not self.get(k):
				frappe.msgprint(_("Missing value for {0}").format(_(self.meta.get_label(k))), raise_exception=True)

		if not self.rental_focal:
			focals = []
			# if self.employment_type == "Civil Servant":
			focals = frappe.db.sql("""select rental_focal, rental_focal_name from `tabTenant Information` where name = '{tenant}'""".format(tenant=self.tenant), as_dict=1)
			# else:
				
			if not len(focals):
				frappe.throw("Missing Rental Focal for Tenant: {0} - {1}".format(self.tenant, self.tenant_name))
			self.rental_focal = focals[0]['rental_focal']
			self.focal_name = focals[0]['rental_focal_name']
		
		self.yearmonth = str(self.fiscal_year) + str(self.month)
	
	def set_rental_amount(self):
		if not self.adjusted_amount and not self.receivable_amount:
			posting_date = self.posting_date
			if self.month == "01":
				prev_fiscal_year = int(self.fiscal_year) - 1
				prev_month = "12"
			else:
				prev_fiscal_year = int(self.fiscal_year)
				prev_month = str(int(self.month) - 1).zfill(2)
			
			previous_bill_date = str(prev_fiscal_year)+"-"+str(prev_month)+"-"+"01"

			query = """
					select tenant_cid, tenant_name, customer_code, block, flat, flat_no,
					ministry_and_agency, location_name, branch, tenant_department_name, dzongkhag, 
					town_category, building_category, is_nhdcl_employee, rental_amount, building_classification,
					phone_no, allocated_date, locations
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
		
					""".format(posting_date=posting_date, name=self.tenant, prev_fiscal_year=prev_fiscal_year, prev_month=prev_month, previous_bill_date=previous_bill_date)
					# or '{previous_bill_date}' between t.m_start_date and t.m_end_date, keep provision to process bill when the flat was under maintenance
			dtls = frappe.db.sql(query, as_dict=True)
			if dtls:
				for d in dtls:
					total_property_mgt_amount = frappe.db.get_value("Flat No", d.flat_no, "total_property_management_amount")
					prop_mgt_amount = 0
					for pm_item in frappe.db.sql("select * from `tabProperty Management Item` where is_percent=1 and parent='{}'".format(d.flat_no), as_dict=1):
						prop_mgt_amount = flt(d.rental_amount * (pm_item.percent / 100), 2)
						total_property_mgt_amount += prop_mgt_amount
					total_property_management_amount = total_property_mgt_amount if total_property_mgt_amount > 0 else 0
					self.rent_amount = d.rental_amount
					self.receivable_amount = flt(d.rental_amount + total_property_management_amount)
			else:
				frappe.throw("No rental amount to bill")
		
		""" Pre-rent calc. and update receivable amount """
		pre_rent_account = frappe.db.get_single_value("Rental Account Setting", "pre_rent_account")
		pre_rent_amount = frappe.db.sql("""
				select ifnull(sum(credit) - sum(debit), 0) as pre_rent_amount
				from `tabGL Entry` 
				Where party_type='Customer' 
				and party = '{party}' and account = '{account}' and is_cancelled=0
			""".format(party=self.customer, account=pre_rent_account))[0][0]
		self.adjusted_amount = 0
		if pre_rent_amount > 0:
			if flt(self.rent_amount + self.property_management_amount) <= pre_rent_amount:
				self.adjusted_amount = flt(self.rent_amount) + self.property_management_amount
			else:
				self.adjusted_amount = flt(pre_rent_amount)
		
		self.receivable_amount = flt(self.rent_amount + self.property_management_amount + self.gst_amount)
		self.outstanding_amount = flt(self.rent_amount + self.property_management_amount + self.gst_amount) - flt(self.adjusted_amount)

	def make_gl_entry(self):
		revenue_claim_account = frappe.db.get_single_value("Rental Account Setting", "revenue_claim_account")
		if not revenue_claim_account:
			frappe.throw("Revenue Claim Account missing in Rental Account Setting")
		gl_entries = []
		pre_rent_account = frappe.db.get_single_value("Rental Account Setting", "pre_rent_account")
		if not pre_rent_account:
			frappe.throw("Pre Rent Account missing in Rental Account Setting")
		acc_property_management = frappe.db.get_single_value("Rental Account Setting", "property_management_account")
		if not acc_property_management:
			frappe.throw("Property Management Account missing in Rental Account Setting")

		if self.adjusted_amount > 0:
			gl_entries.append(
				self.get_gl_dict({
					"account": pre_rent_account,
					"debit": flt(self.adjusted_amount),
					"debit_in_account_currency": flt(self.adjusted_amount),
					"voucher_no": self.name,
					"voucher_type": "Rental Bill",
					"cost_center": self.cost_center,
					"party": self.customer,
					"party_type": "Customer",
					"company": self.company,
					"remarks": str(self.tenant) + " Monthly Rental Bill for Year " + str(self.fiscal_year) + " Month " + str(self.month),
					# "business_activity": business_activity
				})
			)
		
		# if flt(self.receivable_amount - self.property_management_amount) > 0:
		if flt(self.outstanding_amount)  > 0:
			gl_entries.append(
				self.get_gl_dict({
					"account": revenue_claim_account,
					"debit": flt(self.outstanding_amount),
					"debit_in_account_currency": flt(self.outstanding_amount),
					"voucher_no": self.name,
					"voucher_type": "Rental Bill",
					"cost_center": self.cost_center,
					'party': self.customer,
					'party_type': 'Customer',
					"company": self.company,
					"remarks": str(self.tenant) + " Monthly Rental Bill for Year " + str(self.fiscal_year) + " Month " + str(self.month),
					# "business_activity": business_activity
				})
			)

		if self.property_management_amount > 0:
			gl_entries.append(
				self.get_gl_dict({
					"account": acc_property_management,
					"credit": flt(self.property_management_amount),
					"credit_in_account_currency": flt(self.property_management_amount),
					"voucher_no": self.name,
					"voucher_type": "Rental Bill",
					"cost_center": self.cost_center,
					"company": self.company,
					"remarks": str(self.tenant) + " Property Management amount for Year " + str(self.fiscal_year) + " Month " + str(self.month),
					# "business_activity": business_activity
				})
			)
		
		credit_account = frappe.db.get_value("Rental Account Setting Item",{"building_category":self.building_category}, "account")
		gl_entries.append(
			self.get_gl_dict({
				"account": credit_account,
				"credit": flt(self.receivable_amount - self.property_management_amount- self.gst_amount),
				"credit_in_account_currency": flt(self.receivable_amount - self.property_management_amount),
				"voucher_no": self.name,
				"voucher_type": "Rental Bill",
				"cost_center": self.cost_center,
				"company": self.company,
				"remarks": str(self.tenant) + " Rental Bill for " + str(self.building_category) +" Year "+ str(self.fiscal_year) + " Month " +str(self.month),
				# "business_activity": business_activity
				})
			)
		if self.gst_amount > 0:
			gst_output_account = frappe.db.get_value("Company",self.company, "output_gst_account")
			if not gst_output_account:
				frappe.throw("GST Output GST Account missing in Company")
			gl_entries.append(
				self.get_gl_dict({
					"account": gst_output_account,
					"credit": flt(self.gst_amount),
					"credit_in_account_currency": flt(self.gst_amount),
					"voucher_no": self.name,
					"voucher_type": "Rental Bill",
					"cost_center": self.cost_center,
					"company": self.company,
					"remarks": str(self.tenant) + " GST for Year " + str(self.fiscal_year) + " Month " + str(self.month),
					# "business_activity": business_activity
				})
			)
		# frappe.throw("<pre>{}</pre>".format(frappe.as_json(gl_entries)))
		make_gl_entries(gl_entries, cancel=(self.docstatus == 2), update_outstanding="No", merge_entries=True)
		self.db_set("gl_entry", 1)

def send_followup_emails():
	docs = frappe.db.sql("""
		SELECT
			name,
			posting_date,
			tenant_cid,
			tenant_name
		FROM `tabRental Bill`
		WHERE
			receivable_amount >
			(
				IFNULL(received_amount, 0)
				+ IFNULL(discount_amount, 0)
				+ IFNULL(tds_amount, 0)
				+ IFNULL(adjusted_amount, 0)
			)

			AND IFNULL(received_amount, 0) > 0
	""", as_dict=1)
	today = getdate()
	grouped = defaultdict(list)
	email_body = ""

	for d in docs:
		posting_date = getdate(d.posting_date)
		one_month = add_months(posting_date, 1)
		one_n_half_month = add_days(one_month, 15)
		two_month = add_months(posting_date, 2)
		if today == one_month:
			grouped["One Month"].append(d)
		elif today == one_n_half_month:
			grouped["One Month and 15 Days"].append(d)
		elif today == two_month:
			grouped["Two Months"].append(d)
		# Do not send empty email
	if not grouped:
		return
	
	for reminder_type, records in grouped.items():
		email_body += f"""
		<p>The following rental bills are {reminder_type} due for follow-up:</p>

		<table style="border-collapse: collapse; width: 100%;">
			<thead>
				<tr>
					<th style="border:1px solid #ddd;padding:8px;">Rental Bill ID</th>
					<th style="border:1px solid #ddd;padding:8px;">Tenant CID</th>
					<th style="border:1px solid #ddd;padding:8px;">Tenant Name</th>
				</tr>
			</thead>
			<tbody>
		"""
		for r in records:
			email_body += f"""
				<tr>
					<td style="border:1px solid #ddd;padding:8px;">{r.name}</td>
					<td style="border:1px solid #ddd;padding:8px;">{r.tenant_cid or ""}</td>
					<td style="border:1px solid #ddd;padding:8px;">{r.tenant_name or ""}</td>
				</tr>
			"""
		email_body += "</tbody></table>"

		frappe.sendmail(
			# recipients=["leki.tshewang@nhdcl.bt"],
			# cc=["user2@gmail.com", "user3@gmail.com"],
			recipients=["leki.tshewang@nhdcl.bt"],
			cc=["contactlhendup@gmail.com", "bumpa.dema@nhdcl.bt", "dm.ghalley@nhdcl.bt", "dema@nhdcl.bt", "rinzin.dema@nhdcl.bt", "dorji.wangmo@nhdcl.bt", "sangay.dorji@nhdcl.bt", "seema.uroan@nhdcl.bt"],
			subject="Reminder for Rental Due",
			message=f"""
				<p>Dear Sir/Mam,</p>
				{email_body}
				<br>
				<p>Thank you.</p>
			"""
		)
