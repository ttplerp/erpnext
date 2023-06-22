# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import add_to_date, get_last_day, flt, getdate, cint
from frappe import _
import datetime

class TenantInformation(Document):
	def autoname(self):
		if not self.dzongkhag:
			frappe.throw("Dzongkhag name is missing")
		dz = self.dzongkhag
		dzo_prefix = dz[:3]
		prefix = dzo_prefix.upper()
		dt = datetime.datetime.today()
		current_year = str(dt.year)
		pre_name = prefix + current_year[2:]
		for b in frappe.db.sql("select ifnull(substring(max(name),6,4),0) as code from `tabTenant Information` where name like '{0}%'""".format(pre_name), as_dict=True):
			sl = cint(b.code)
		if sl > 0:
			sl += 1
		else:
			sl = 1
		if len(str(sl)) == 1:
			serial = "000" + str(sl)
		elif len(str(sl)) == 2:
			serial = "00" + str(sl)
		elif len(str(sl)) == 3:
			serial = "0" + str(sl)
		else:
			serial = str(sl)

		self.name = pre_name + serial
	
	def validate(self):
		self.set_missing_values()
		self.validate_allocation()
		if not self.rental_charges:
			self.calculate_rent_charges()
		if not self.is_nhdcl_employee:
			self.nhdcl_employee = ''

	def on_submit(self):
		if self.status == "Surrendered":
			frappe.throw("Not allowed to submit a document with status Surrendered")

		self.create_customer()
		if not self.customer_code:
			frappe.throw("An issue occured with auto Customer creation, alert you System developer.")

	def set_missing_values(self):
		if self.building_category != "Pilot Housing" and not self.initial_rental_amount:
			self.initial_rental_amount = round(flt(self.total_floor_area) * flt(self.rate_per_sqft))

		if self.building_category == "Pilot Housing" and not self.original_monthly_instalment:
			if self.pilot_account_details:
				monthly_installment_amount = 0.0
				for a in self.pilot_account_details:
					monthly_installment_amount += flt(a.amount)

				self.original_monthly_instalment = monthly_installment_amount
		""" Property Management Detail, This shift to locations """
		# if self.block_no and not self.get('rental_property_management_item'):
		# 	self.set('rental_property_management_item', [])
		# 	for d in frappe.db.sql("select * from `tabProperty Management Item` where parent='{}'".format(self.locations), as_dict=1):
		# 		self.append('rental_property_management_item', {
		# 			'property_management_type': d.property_management_type,
		# 			'amount': d.amount
		# 		})

		# prop_mgt_amt = 0
		# for a in self.get('rental_property_management_item'):
		# 	prop_mgt_amt += flt(a.amount)
		# self.total_property_management_amount = prop_mgt_amt

	def validate_allocation(self):
		if self.status != "Surrendered":
			cid = frappe.db.get_value("Tenant Information", {"locations":self.locations, "building_category":self.building_category, "building_classification":self.building_classification, "block_no":self.block_no, "flat_no":self.flat_no, "docstatus":1, "status":"Allocated", "name": ("!=", self.name)}, "tenant_cid")
			tenant_code = frappe.db.get_value("Tenant Information", {"locations":self.locations, "building_category":self.building_category, "building_classification":self.building_classification, "block_no":self.block_no, "flat_no":self.flat_no, "docstatus":1, "status":"Allocated", "name": ("!=", self.name)}, "name")
			if cid:
				frappe.throw("The allocated Flat is already rented to a Tenant with CID No: {0} and Tenant code: {1}".format(cid, tenant_code))
			else:
				if frappe.db.exists("Tenant Information", {"locations":self.locations, "building_category":self.building_category, "block_no":self.block_no, "flat_no":self.flat_no, "docstatus": 1, "status":"Surrendered"}):
					
					surrendered_date, tenant_code = frappe.db.get_value("Tenant Information", {"locations":self.locations, "building_category":self.building_category, "block_no":self.block_no, "flat_no":self.flat_no, "docstatus": 1, "status":"Surrendered"}, ["surrendered_date","name"])
					if surrendered_date and getdate(self.allocated_date) < getdate(surrendered_date):
						frappe.throw("Allocation Date {0} cannot be before surrendered date {1} for tenant {2}".format(self.allocated_date, surrendered_date, tenant_code))
		if self.tenant_cid:
			if frappe.db.exists("Tenant Information", {"tenant_cid":self.tenant_cid, "status":"Allocated", "docstatus":1, "name": ("!=", self.name)}):
				tenant_code = frappe.db.get_value("Tenant Information", {"tenant_cid":self.tenant_cid, "status":"Allocated", "name": ("!=", self.name)}, "name")
				frappe.throw("You cannot create a tenant with CID ({}) as rental status Allocated. The CID is already assigned with Tenant Code {}".format(self.tenant_cid, tenant_code))

	def create_customer(self):
		#Validate Creation of Duplicate Customer in Customer Master
		#if customer exist with same tenant_cid, set the customer_code from existing customer 
		if frappe.db.exists("Customer", {"customer_id":self.tenant_cid, "customer_group": "Rental"}):
			cus = frappe.get_doc("Customer", {"customer_id":self.tenant_cid, "customer_group": "Rental"})
			existing_customer_code = frappe.db.get_value("Customer", {"customer_id":self.tenant_cid, "customer_group": "Rental"}, "customer_code")
			if existing_customer_code:
				#self.customer_code = existing_customer_code
				self.db_set("customer_code", existing_customer_code)
			else:
				last_customer_code = frappe.db.sql("select customer_code from tabCustomer where customer_group='Rental' order by customer_code desc limit 1;");
				if last_customer_code:
					customer_code = str(int(last_customer_code[0][0]) + 1)
				else:
					customer_code = frappe.db.get_value("Customer Group", "Rental", "customer_code_base")
					if not customer_code:
						frappe.throw("Setup Customer Code Base in Rental Customer Group")
				self.db_set("customer_code", customer_code)
				cus.customer_code = customer_code

			cus.mobile_no = self.phone_no
			# cus.location = self.location
			# cus.dzongkhag = self.dzongkhag
			cus.save()
			# self.db_set("customer_code", cus.name)

		else:
			last_customer_code = frappe.db.sql("select customer_code from tabCustomer where customer_group='Rental' order by customer_code desc limit 1;");
			if last_customer_code:
				customer_code = str(int(last_customer_code[0][0]) + 1)
			else:
				customer_code = frappe.db.get_value("Customer Group", "Rental", "customer_code_base")
				if not customer_code:
					frappe.throw("Setup Customer Code Base in Rental Customer Group")
			self.db_set("customer_code", customer_code)
			cus_name = self.tenant_name + "-" + customer_code

			cus = frappe.new_doc("Customer")
			cus.customer_code = customer_code
			cus.name = cus_name
			cus.customer_name = cus_name
			cus.customer_group = "Rental"
			cus.customer_id = self.tenant_cid
			cus.territory = "Bhutan"
			cus.mobile_no = self.phone_no
			# cus.location = self.location
			# cus.dzongkhag = self.dzongkhag
			# cus.cost_center = frappe.get_value("Branch", self.branch, "cost_center")
			cus.branch = self.branch
			cus.save()
			self.db_set("customer", cus.name)
			
	@frappe.whitelist()
	def calculate_rent_charges(self):
		self.set('rental_charges', [])
		if self.building_category == "Pilot Housing":
			check_required = ["allocated_date", "repayment_period", "original_monthly_instalment", "initial_allotment_date"]
			for k in check_required:
				if not self.get(k):
					frappe.msgprint(_("{0} is required").format(_(self.meta.get_label(k))), raise_exception=True)
					
			to_date = add_to_date(get_last_day(add_to_date(self.initial_allotment_date, days=-10)), years=self.repayment_period)
			# frappe.throw(str(to_date))
			rent_obj = self.append("rental_charges", {
							"from_date": self.initial_allotment_date,
							"to_date": to_date,
							"increment": 0.00,
							"rental_amount": round(self.original_monthly_instalment)
						})
			# rent_obj.save()
		else:
			check_required = ["allocated_date", "rental_term_year", "no_of_year_for_increment", "percent_of_increment"]
			for k in check_required:
				if not self.get(k):
					frappe.msgprint(_("{0} is required").format(_(self.meta.get_label(k))), raise_exception=True)

			increment_year = int(self.no_of_year_for_increment)
			percentage = self.percent_of_increment
			rental_term_year = int(self.rental_term_year)
			start_date = self.allocated_date
			end_date = add_to_date(get_last_day(add_to_date(self.allocated_date, days=-10)), years=increment_year)
			increment = 0.00
			actual_rent = 0.00
			
			for i in range(0, rental_term_year, increment_year):
				if i > 1:
					start_date = add_to_date(start_date, years=increment_year)
					end_date = add_to_date(end_date, years=increment_year)
					increment = flt(actual_rent) * flt(flt(percentage)/100) if actual_rent > 0 else flt(self.initial_rental_amount) * flt(flt(percentage)/100)
					actual_rent = flt(actual_rent) + flt(increment) if actual_rent > 0 else flt(self.initial_rental_amount) + flt(increment)
				actual_rent = actual_rent if actual_rent > 0 else self.initial_rental_amount		
				#frappe.msgprint("{0} start: {1} and  end_date: {2} increment {3} and rent {4}".format(i, start_date, end_date, increment, actual_rent))
				rent_obj = self.append("rental_charges", {
							"from_date": start_date,
							"to_date": end_date,
							"increment": increment,
							"rental_amount": round(actual_rent)
						})

				# rent_obj.save()
		
