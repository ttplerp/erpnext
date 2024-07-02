# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from datetime import date
from frappe.model.document import Document
from frappe.utils import cint, flt, nowdate, add_days, getdate, fmt_money, add_to_date, DATE_FORMAT, date_diff, get_last_day
from frappe.query_builder.functions import Count, Extract, Sum

class DesuupPayrollEntry(Document):
	def validate(self):
		# self.validate_posting_date()
		# self.set_month_dates()
		pass

	def on_submit(self):
		self.submit_pay_slip()
		self.post_to_journal_entry()

	def submit_pay_slip(self):
		self.check_permission('write')
		ps_list = self.get_desuup_pay_slips(ps_status=0)

		if len(ps_list) > 300:
			frappe.enqueue(submit_pay_slips_for_desuups, timeout=600, desuup_payroll_entry=self, pay_slips=ps_list)
		else:
			submit_pay_slips_for_desuups(self, ps_list, publish_progress=False)

	def get_desuup_pay_slips(self, ps_status, as_dict=False):
		ps_list = frappe.db.sql("""
					select ps.name
						  from `tabDesuup Pay Slip` ps
						  where ps.docstatus = %s 
						  and ps.start_date >= %s
						  and ps.end_date <= %s
						  and ps.desuup_payroll_entry = %s
					""" % ('%s','%s','%s','%s'), (ps_status, self.start_date, self.end_date, self.name), as_dict=as_dict)
		return ps_list

	@frappe.whitelist()
	def set_month_dates(self):
		months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
		month = str(int(months.index(self.month_name))+1).rjust(2,"0")

		month_start_date = "-".join([str(date.today().year), month, "01"])
		month_end_date   = get_last_day(month_start_date)

		self.start_date = month_start_date
		self.end_date = month_end_date
		self.month = month
	
	def get_conditions(self):
		cond = ''
		if self.training_management and self.payment_for == "Trainee":
			cond += " and t1.name = '{}'".format(self.training_management)
		if self.desuup_deployment and self.payment_for == "OJT":
			cond += " and t1.name = '{}'".format(self.desuup_deployment)
		if self.domain:
			cond += " and t1.domain = '{}'".format(self.domain)
		if self.programme:
			cond += " and t1.programme_classification = '{}'".format(self.programme)
		if self.training_center:
			cond += " and t1.training_center = '{}'".format(self.training_center)
		return cond

	def get_desuup_list(self):
		desuup_list = []
		if self.payment_for == "Trainee":
			cond = self.get_conditions()
		
			desuup_list = frappe.db.sql("""
							select t1.name as reference_name, 'Training Management' as reference_doctype, t2.desuup_id as desuup, t2.desuup_name, t2.is_mess_member 
							from `tabTraining Management` t1, `tabTrainee Details` t2
							where t1.name = t2.parent
							and t1.course_cost_center = '{}'
							and t1.status='On Going' and '{}' between t1.training_start_date and t1.training_end_date 
							{} order by t2.desuup_name
							""".format(self.cost_center, getdate(self.posting_date), cond), as_dict=True)
			
		elif self.payment_for == "OJT":
			cond = self.get_conditions()
			desuup_list = frappe.db.sql("""
							select 'Desuup Deployment Entry' as reference_doctype, t1.name as reference_name, t2.desuup, t2.desuup_name, t2.deployment_type 
							from `tabDesuup Deployment Entry` t1, `tabDesuup Deployment Entry Item` t2
							where t1.name = t2.parent
							and t1.deployment_status='On Going' and '{}' between t1.start_date and t1.end_date {} order by t2.desuup_name
							""".format(getdate(self.posting_date), cond), as_dict=True)
		return desuup_list

	@frappe.whitelist()
	def get_desuup_details(self):
		self.set('items', [])
		desuups = self.get_desuup_list()
		if not desuups:
			frappe.throw(_("No desuups for the mentioned criteria"))

		for d in desuups:
			self.append('items', d)

		self.number_of_desuups = len(desuups)
		return self.number_of_desuups
	
	@frappe.whitelist()
	def create_pay_slips(self):
		self.check_permission('write')
		self.created = 1

		dsp_list = [d.desuup for d in self.items]

		# get branch and cost center
		 
		if dsp_list:
			args = frappe._dict({
				"posting_date": self.posting_date,
				"start_date": self.start_date,
				"end_date": self.end_date,
				"month": self.month,
				"desuup_payroll_entry": self.name,
				"payment_to": self.payment_for,
				"branch": self.branch,
				"cost_center": self.cost_center,
				"month_name": self.month_name,
				"month": self.month,
			})
			if len(dsp_list) > 300:
				frappe.enqueue(create_pay_slips_for_desuups, timeout=600, desuups=dsp_list, args=args)
			else:
				create_pay_slips_for_desuups(dsp_list, args, publish_progress=False)
				# since this method is called via frm.call this doc needs to be updated manually
				self.reload()

	def post_to_journal_entry(self):
		total_payable = 0
		total_expense = 0
		total_advance = 0

		# get party details
		mess_adv_party = frappe.db.get_value("Desuup Mess Advance", {'from_date':self.start_date, 'to_date': self.end_date, 'month':self.month, 'reference_name': self.training_management}, "paid_to")
		mess_adv_party_name = frappe.db.get_value("Employee", mess_adv_party, "employee_name")

		bank_account = frappe.db.get_value("Company", self.company, "default_bank_account")

		adv_account = frappe.db.get_single_value("Desuup Settings", "mess_advance_account")
		deduction_account = frappe.db.get_single_value("Desuup Settings", "deduction_account")
		if self.payment_for == "Trainee":
			payable_account = frappe.db.get_single_value("Desuup Settings", "stipend_payable_account")
			expense_account = frappe.db.get_single_value("Desuup Settings", "stipend_expense_account")
		elif self.payment_for == "OJT":
			payable_account = frappe.db.get_single_value("Desuup Settings", "ojt_payable_account")
			expense_account = frappe.db.get_single_value("Desuup Settings", "ojt_expense_account")
		if not bank_account:
			frappe.throw("Stre")
	
		journal = [
            {
                "type": "payable",
				"entry_type": "Journal Entry",
                "series": "Journal Voucher",
                "is_submitable": 1,
            },
            {
                "type": "payment",
				"entry_type": "Bank Entry",
                "series": "Bank Payment Voucher",
                "is_submitable": 0,
            },
        ]

		for j in journal:
			je = frappe.new_doc("Journal Entry")
			je.flags.ignore_permission = 1

			je.update({
				"doctype": "Journal Entry",
				"voucher_type": j["entry_type"],
                "naming_series": j["series"],
				"title": "Desuup Payment Entry " + self.name,
				"branch": self.branch,
				"posting_date": self.posting_date,
				"company": self.company,
				"reference_doctype":self.doctype,
				"reference_name":self.name,
			})

			if j["type"] == "payable":
				for d in frappe.db.sql("""
							select name from `tabDesuup Pay Slip`
							where desuup_payroll_entry = '{}' 
							and net_pay > 0
							""".format(self.name), as_dict=True):
					pay_slip = frappe.get_doc("Desuup Pay Slip", d.name)
					total_payable += flt(pay_slip.net_pay, 2)
					if pay_slip.payment_to == "Trainee":
						total_expense += flt(pay_slip.stipend_amount, 2)
						total_advance += flt(pay_slip.advance_amount_used, 2)
					elif pay_slip.payment_to == "OJT":
						total_expense += flt(pay_slip.net_pay, 2)

					if flt(pay_slip.deduction_amount, 2) > 0:
						je.append(
							"accounts",
							{
								"account": deduction_account,
								"credit": flt(pay_slip.deduction_amount, 2),
								"credit_in_account_currency": flt(pay_slip.deduction_amount, 2),
								"cost_center": self.cost_center,
								"party_check": 1,
								"party_type": "Desuup",
								"party": pay_slip.desuup,
								"party_name": pay_slip.desuup_name,
								"reference_type": self.doctype,
								"reference_name": self.name,
							}
						)	
					
				if total_advance > 0:
					je.append(
						"accounts",
						{
						"account": adv_account,
						"credit": flt(total_advance, 2),
						"credit_in_account_currency": flt(total_advance, 2),
						"cost_center": self.cost_center,
						"party_check": 1,
						"party_type": "Employee",
						"party": mess_adv_party,
						"party_name": mess_adv_party_name,
						"reference_type": self.doctype,
						"reference_name": self.name,
					})	

				je.append(
						"accounts",
						{
							"account": expense_account,
							"debit": flt(total_expense, 2),
							"debit_in_account_currency": flt(total_expense, 2),
							"cost_center": self.cost_center,
						})
				
				je.append(
					"accounts",
					{
						"account": payable_account,
						"credit": flt(total_payable,2),
						"credit_in_account_currency": flt(total_payable,2),
						"cost_center": self.cost_center,
					})	
			else:
				je.append(
                            "accounts",
                            {
                                "account": payable_account,
                                "debit_in_account_currency": flt(total_payable, 2),
                                "debit": flt(total_payable, 2),
                                "cost_center": self.cost_center,
                            },
                        )

				je.append(
                    "accounts",
                    {
                        "account": bank_account,
                        "credit_in_account_currency": flt(total_payable, 2),
                        "credit": flt(total_payable, 2),
                        "cost_center": self.cost_center,
                    },
                )

			if j["is_submitable"] == 1:
				je.submit()
			else:
				je.insert()

def get_existing_pay_slips(desuups, args):
	return frappe.db.sql_list("""
		select distinct desuup from `tabDesuup Pay Slip`
		where docstatus != 2
		and start_date >= %s and end_date <= %s
		and desuup in (%s)
		""" % ('%s', '%s', ', '.join(['%s']*len(desuups))), [args.start_date, args.end_date] + desuups)

def create_pay_slips_for_desuups(desuups, args, title=None, publish_progress=True):
	pay_slips_exists_for = get_existing_pay_slips(desuups, args)
	successful = 0
	failed = 0
	count = 0

	payroll_entry = frappe.get_doc("Desuup Payroll Entry", args.desuup_payroll_entry)
	
	for dsp in payroll_entry.get("items"):
		if dsp.desuup in desuups and dsp.desuup:
			error = None
			args.update({
				"doctype": "Desuup Pay Slip",
				"desuup": dsp.desuup,
				"is_mess_member": dsp.is_mess_member,
				"deployment_type": dsp.deployment_type if dsp.reference_doctype == 'Desuup Deployment Entry' else '',
				"reference_doctype": dsp.reference_doctype,
				"reference_name": dsp.reference_name,
			})

			try:
				pay_slip = frappe.get_doc(args)
				deduction = next((d.amount for d in payroll_entry.get("deductions") if d.desuup == dsp.desuup), None)
				if deduction is not None:
					pay_slip.deduction_amount = deduction
				else:
					pay_slip.deduction_amount = 0
						
				if pay_slip.payment_to != 'OJT':
					pay_slip.get_desuup_attendance()
				pay_slip.calculate_amount()
				pay_slip.insert()

				# dsp.total_days_present = pay_slip.total_days_present
				# dsp.amount = pay_slip.net_pay
				successful += 1
			except Exception as e:
				error = str(e)
				failed += 1
			count += 1

			# update child table
			ped = frappe.get_doc("Desuup Payroll Entry Item", dsp.name)
			ped.db_set("pay_slip", pay_slip.name)
			if error:
				ped.db_set("status", "Failed")
			else:
				ped.db_set("status", "Success")

	payroll_entry.db_set("desuup_pay_slips_created", 0 if failed else 1)
	payroll_entry.db_set("successful", cint(payroll_entry.successful)+cint(successful))
	payroll_entry.db_set("failed", cint(payroll_entry.number_of_desuups)-(cint(payroll_entry.successful)))
	payroll_entry.reload()

def submit_pay_slips_for_desuups(desuup_payroll_entry, pay_slips, publish_progress=True):
	submitted_ps = []
	not_submitted_ps = []
	frappe.flags.via_desuup_payroll_entry = True

	count = 0
	refresh_interval = 25
	total_count = len(pay_slips)
	for ps in pay_slips:
		ps_obj = frappe.get_doc("Desuup Pay Slip", ps[0])
		if ps_obj.net_pay < 0:
			not_submitted_ps.append(ps[0])
		else:
			try:
				ps_obj.submit()
				submitted_ps.append(ps_obj)
			except frappe.ValidationError:
				not_submitted_ps.append(ps[0])
		
		count += 1
	
	if submitted_ps:
		frappe.msgprint(_("Pay Slip submitted for period from {0} to {1}")
			.format(ps_obj.start_date, ps_obj.end_date))

		# desuup_payroll_entry.email_pay_slip(submitted_ps)
		desuup_payroll_entry.db_set("desuup_pay_slips_submitted", 1)
		desuup_payroll_entry.reload()
	
	if not submitted_ps and not not_submitted_ps:
		frappe.msgprint(_("No pay slip found to submit for the above selected criteria OR pay slip already submitted"))

	if not_submitted_ps:
		frappe.msgprint(_("Could not submit some Pay Slips"))
