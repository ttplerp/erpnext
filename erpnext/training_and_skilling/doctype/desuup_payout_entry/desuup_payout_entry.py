# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
import calendar
from frappe import _
from datetime import date
from frappe.model.document import Document
from frappe.utils import cint, flt, nowdate, add_days, getdate, fmt_money, add_to_date, DATE_FORMAT, date_diff, get_last_day, get_datetime
from frappe.query_builder.functions import Count, Extract, Sum
from frappe.model.mapper import get_mapped_doc

class DesuupPayoutEntry(Document):
	def validate(self):
		# self.validate_cost_center()
		# self.set_month_dates()
		self.calculate_total_net_amount()
		self.calculate_amount()
		self.validate_data()

	def calculate_total_net_amount(self):
		net_amount = 0
		refund_amount = 0
		for amt in self.items:
			net_amount += amt.net_amount
			refund_amount += amt.refundable_amount
		self.total_net_amount = net_amount
		self.total_refundable_amount = refund_amount

	def validate_data(self):
		for i in self.get("items"):
			if flt(i.mess_advance_amount) < flt(i.mess_advance_used):
				frappe.throw("In Row #{}: The used advance amount ({}) exceeds the total claimed advance ({}). Please adjust the values.".format(
					frappe.bold(i.idx), 
					frappe.bold(i.mess_advance_used), 
					frappe.bold(i.mess_advance_amount)
				))

			if i.total_days_present <= 0 and not i.refundable_amount:
				frappe.throw("Remove Row #{} or mark attendance for desuup {}".format(
					frappe.bold(i.idx), 
					frappe.bold(i.desuup)
				))

	def calculate_amount(self):
		month_start_date = "-".join([str(date.today().year), self.month, "01"])
		month_end_date   = get_last_day(month_start_date)
		days_in_month = calendar.monthrange(month_end_date.year, month_end_date.month)[1]

		for item in self.get("items"):
			total_days = self.get_desuup_attendance(item.desuup, item.reference_doctype, item.reference_name)
			item.days_in_month = days_in_month
			item.total_days_present = total_days
			
			# if item.reference_doctype == "Training Management":
			# 	monthly_stipend_amt, monthly_mess_amt = self.get_stipend_amount()

			# 	item.monthly_stipend_amount = monthly_stipend_amt
			# 	mess_adv_amt, adv_party = self.get_advance_amount(item.desuup, item.reference_doctype, item.reference_name)
			# 	if item.is_mess_member and mess_adv_amt > 0:
			# 		item.monthly_mess_amount = monthly_mess_amt

			# 		item.mess_advance_party = adv_party
			# 		item.mess_advance_amount = mess_adv_amt

			# 		if item.days_in_month == item.total_days_present:
			# 			stipend = flt(monthly_stipend_amt - monthly_mess_amt)
			# 			adv_amt = flt(monthly_mess_amt)

			# 			item.stipend_amount = flt(stipend, 2)
			# 			item.mess_advance_used = flt(adv_amt, 2)	
			# 		else:
			# 			if flt(item.total_days_present) > 30:
			# 				stipend = flt(monthly_stipend_amt - monthly_mess_amt)
			# 				adv_amt = flt(monthly_mess_amt)

			# 				item.stipend_amount = flt(stipend, 2)
			# 				item.mess_advance_used = flt(adv_amt, 2)	
			# 			else:
			# 				stipend = flt(monthly_stipend_amt - monthly_mess_amt)/flt(30)
			# 				adv_amt = flt(monthly_mess_amt)/flt(30)

			# 				item.stipend_amount = flt(stipend * total_days, 2)
			# 				item.mess_advance_used = flt(adv_amt * total_days, 2)

			# 		item.refundable_amount = flt(item.mess_advance_amount, 2) - flt(item.mess_advance_used)

			# 		item.net_amount = flt(flt(item.stipend_amount) + flt(item.total_arrear_amount)) - flt(item.total_deduction_amount)
			# 	else:
			# 		if item.days_in_month != item.total_days_present:
			# 			item.stipend_amount = flt(monthly_stipend_amt)/flt(30) * flt(total_days)
			# 			item.net_amount = flt(flt(item.stipend_amount) + flt(item.total_arrear_amount)) - flt(item.total_deduction_amount)
			# 		else:
			# 			item.stipend_amount = flt(monthly_stipend_amt)
			# 			item.net_amount = flt(flt(item.stipend_amount) + flt(item.total_arrear_amount)) - flt(item.total_deduction_amount)

			# elif item.reference_doctype == "Desuup Deployment Entry":
			# 	# if item.monthly_pay_amount <= 0:
			# 	# 	frappe.throw("Monthly Pay amount cannot be 0 or less")
			# 	if item.days_in_month == item.total_days_present:
			# 		item.total_amount = flt(item.monthly_pay_amount)
			# 	else:
			# 		item.total_amount = flt(item.monthly_pay_amount)/30
			# 		item.total_amount = item.total_amount * total_days
					
			# 	total_amount = flt(item.total_amount, 2) + flt(item.total_arrear_amount)
			# 	if flt(total_amount) < flt(item.total_deduction_amount):
			# 		frappe.throw("Row #{} cannot be more deduction {} ".format(item.idx, item.total_deduction_amount))
			# 	else:
			# 		item.net_amount = flt(flt(total_amount) - flt(item.total_deduction_amount), 2)

			monthly_stipend_amt, monthly_mess_amt = self.get_stipend_amount()
			if self.payment_for == "Trainee":
				item.monthly_stipend_amount = monthly_stipend_amt
			mess_adv_amt, adv_party = self.get_advance_amount(item.desuup, item.reference_doctype, item.reference_name)
			if item.is_mess_member and mess_adv_amt > 0:
				item.monthly_mess_amount = monthly_mess_amt

				item.mess_advance_party = adv_party
				item.mess_advance_amount = mess_adv_amt

				if item.days_in_month == item.total_days_present:
					stipend = flt(item.monthly_stipend_amount - monthly_mess_amt)
					adv_amt = flt(monthly_mess_amt)

					item.stipend_amount = flt(stipend, 2)
					item.mess_advance_used = flt(adv_amt, 2)	
				else:
					if flt(item.total_days_present) > 30:
						stipend = flt(item.monthly_stipend_amount - monthly_mess_amt)
						adv_amt = flt(monthly_mess_amt)

						item.stipend_amount = flt(stipend, 2)
						item.mess_advance_used = flt(adv_amt, 2)	
					else:
						stipend = flt(item.monthly_stipend_amount - monthly_mess_amt)/flt(30)
						adv_amt = flt(monthly_mess_amt)/flt(30)

						item.stipend_amount = flt(stipend * total_days, 2)
						item.mess_advance_used = flt(adv_amt * total_days, 2)
			else:
				if item.days_in_month == item.total_days_present:
					stipend = flt(item.monthly_stipend_amount)

					item.stipend_amount = flt(stipend, 2)
				else:
					if flt(item.total_days_present) > 30:
						stipend = flt(item.monthly_stipend_amount)

						item.stipend_amount = flt(stipend, 2)
					else:
						stipend = flt(item.monthly_stipend_amount)/flt(30)

						item.stipend_amount = flt(stipend * total_days, 2)

			item.refundable_amount = flt(item.mess_advance_amount, 2) - flt(item.mess_advance_used)

			item.net_amount = flt(flt(item.stipend_amount) + flt(item.total_arrear_amount)) - flt(item.total_deduction_amount)

			# elif item.reference_doctype == "Desuup Deployment Entry":
			# 	# if item.monthly_pay_amount <= 0:
			# 	# 	frappe.throw("Monthly Pay amount cannot be 0 or less")
			# 	if item.days_in_month == item.total_days_present:
			# 		item.total_amount = flt(item.monthly_pay_amount)
			# 	else:
			# 		item.total_amount = flt(item.monthly_pay_amount)/30
			# 		item.total_amount = item.total_amount * total_days
					
			# 	total_amount = flt(item.total_amount, 2) + flt(item.total_arrear_amount)
			# 	if flt(total_amount) < flt(item.total_deduction_amount):
			# 		frappe.throw("Row #{} cannot be more deduction {} ".format(item.idx, item.total_deduction_amount))
			# 	else:
			# 		item.net_amount = flt(flt(total_amount) - flt(item.total_deduction_amount), 2)

	def get_advance_amount(self, desuup, ref_doctype, ref_name):
		adv_list = frappe.db.sql("""
				SELECT t1.name, sum(t2.amount) as amount, t1.paid_to 
				FROM `tabDesuup Mess Advance` t1, `tabDesuup Mess Advance Item` t2 
				WHERE t1.name = t2.parent
				AND t2.reference_doctype = %s
				AND t2.reference_name = %s
				AND t2.desuup = %s
				AND t1.docstatus = 1
				AND t1.month = %s
			""", (ref_doctype, ref_name, desuup, self.month), as_dict=True)

		# Check if the query returns any results and then get the amount
		if adv_list:
			adv_amt = flt(adv_list[0].amount)
			adv_party = adv_list[0].paid_to
		else:
			adv_amt = 0  # Or handle it accordingly
			adv_party = ""
		return adv_amt, adv_party

	def get_stipend_amount(self):
		monthly_stipend = frappe.db.get_single_value("Desuup Settings", "monthly_stipend")
		mess_adv_amt = frappe.db.get_single_value("Desuup Settings", "mess_advance")
		if not monthly_stipend:
			frappe.throw("Please set monthly Stipend amount in Desuup Settings")
		if not mess_adv_amt:
			frappe.throw("Please set monthly mess advance in Desuup Settings")

		return monthly_stipend, mess_adv_amt

	def get_desuup_attendance(self, desuup, ref_doctype, ref_name):
		total_days = 0
		query = """
			SELECT a.name as desuup_attendance, a.status, a.attendance_date
			FROM `tabDesuup Attendance` a
			WHERE a.docstatus = 1
			AND a.desuup = %s
			AND a.attendance_date BETWEEN %s AND %s
			AND a.status IN ('Present', 'Half Day')
			AND a.reference_doctype = %s
			AND a.reference_name = %s
		"""
		# Execute the query with parameters
		attendance_records = frappe.db.sql(query, (desuup, self.start_date, self.end_date, ref_doctype, ref_name), as_dict=True)
		for record in attendance_records:
			if record.status == "Present":
				total_days += 1
			elif record.status == "Half Day":
				total_days += 0.5
		return total_days

	def on_submit(self):
		self.make_accounting_entry()

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
		if self.training_center and self.payment_for == "Trainee":
			cond += " and t1.training_center = '{}'".format(self.training_center)

		# OJT addtional condition
		if self.desuup_deployment and self.payment_for == "OJT":
			cond += " AND t1.name = '{}'".format(self.desuup_deployment)

		if self.desuup_deployment and self.payment_for == "Production":
			cond += " AND t1.name = '{}'".format(self.desuup_deployment)
		
		return cond

	def get_desuup_list(self):
		desuup_list = []
		cond = self.get_conditions()
		params = {
			'start_date': getdate(self.start_date),
			'end_date': getdate(self.end_date),
			"ref_name": self.training_management if self.payment_for == "Trainee" else self.desuup_deployment,
		}

		if self.payment_for == "Trainee":
			desuup_list = frappe.db.sql("""
				SELECT 
					t1.name AS reference_name, 
					'Training Management' AS reference_doctype, 
					t1.training_start_date AS from_date, 
					t1.training_end_date AS to_date,
					t2.reporting_date, 
					t2.exit_date, 
					t1.branch, 
					t1.course_cost_center AS cost_center, 
					t2.desuup_id AS desuup, 
					t2.desuup_name, 
					t2.is_mess_member
				FROM 
					`tabTraining Management` t1
				INNER JOIN 
					`tabTrainee Details` t2 ON t1.name = t2.parent
				WHERE 
					t1.status = 'On Going'
					AND t2.reporting_date IS NOT NULL
					AND (
						t1.training_start_date BETWEEN %(start_date)s AND %(end_date)s 
						OR t1.training_end_date BETWEEN %(start_date)s AND %(end_date)s
						OR %(start_date)s BETWEEN t1.training_start_date AND t1.training_end_date
						OR %(end_date)s BETWEEN t1.training_start_date AND t1.training_end_date
					)
					AND (
						t2.exit_date IS NULL 
						OR t2.exit_date > %(start_date)s
					)
					AND t2.desuup_id NOT IN (
						SELECT desuup
						FROM `tabDesuup Payout Item` 
						WHERE (
							from_date BETWEEN %(start_date)s AND %(end_date)s 
							OR to_date BETWEEN %(start_date)s AND %(end_date)s
							OR %(start_date)s BETWEEN from_date AND to_date
							OR %(end_date)s BETWEEN from_date AND to_date
						)
						AND reference_name = %(ref_name)s
						AND docstatus IN (1)
					)
					{}
				ORDER BY 
					t2.desuup_name
			""".format(cond), params, as_dict=True)

		elif self.payment_for == "OJT":
			desuup_list = frappe.db.sql("""
				SELECT 
				'Desuup Deployment Entry' as reference_doctype, 
				t1.name as reference_name, 
				t2.desuup, 
				t2.desuup_name, 
				t2.amount as monthly_pay_amount, 
				t1.branch, 
				t1.cost_center,
				t1.start_date from_date,
				t1.end_date to_date,
				t2.reported_date,
				t2.exit_date,
				t2.is_mess_member,
				t2.amount as monthly_stipend_amount  
				FROM `tabDesuup Deployment Entry` t1, `tabDesuup Deployment Entry Item` t2
				WHERE t1.name = t2.parent
				AND t1.deployment_type = 'OJT'
				AND t1.status='On Going'
				AND t2.reported_date IS NOT NULL 
				AND (
					t1.start_date BETWEEN %(start_date)s AND %(end_date)s 
					OR t1.end_date BETWEEN %(start_date)s AND %(end_date)s
					OR %(start_date)s BETWEEN t1.start_date AND t1.end_date
					OR %(end_date)s BETWEEN t1.start_date AND t1.end_date
				)
				AND (
						t2.exit_date IS NULL 
						OR t2.exit_date > %(start_date)s
					)
				AND t2.desuup NOT IN (
					SELECT desuup
					FROM `tabDesuup Payout Item` 
					WHERE (
						from_date BETWEEN %(start_date)s AND %(end_date)s 
						OR to_date BETWEEN %(start_date)s AND %(end_date)s
						OR %(start_date)s BETWEEN from_date AND to_date
						OR %(end_date)s BETWEEN from_date AND to_date
					)
					AND docstatus IN (1)
					AND reference_name = %(ref_name)s
				)
				{}
				ORDER BY t2.desuup_name
			""".format(cond), params, as_dict=True)

		elif self.payment_for == "Production":
			desuup_list = frappe.db.sql("""
				SELECT 
				'Desuup Deployment Entry' as reference_doctype, 
				t1.name as reference_name, 
				t2.desuup, 
				t2.desuup_name, 
				t2.amount as monthly_pay_amount, 
				t1.branch, 
				t1.cost_center,
				t1.start_date from_date,
				t1.end_date to_date,
				t2.reported_date,
				t2.exit_date,
				t2.is_mess_member,
				t2.amount as monthly_stipend_amount  
				FROM `tabDesuup Deployment Entry` t1, `tabDesuup Deployment Entry Item` t2
				WHERE t1.name = t2.parent
				AND t1.deployment_type = 'Production' 
				AND t1.status='On Going'
				AND t2.reported_date IS NOT NULL 
				AND (
					t1.start_date BETWEEN %(start_date)s AND %(end_date)s 
					OR t1.end_date BETWEEN %(start_date)s AND %(end_date)s
					OR %(start_date)s BETWEEN t1.start_date AND t1.end_date
					OR %(end_date)s BETWEEN t1.start_date AND t1.end_date
				)
				AND (
					t2.exit_date IS NULL 
					OR t2.exit_date > %(start_date)s
				)
				AND t2.desuup NOT IN (
					SELECT desuup
					FROM `tabDesuup Payout Item` 
					WHERE (
						from_date BETWEEN %(start_date)s AND %(end_date)s 
						OR to_date BETWEEN %(start_date)s AND %(end_date)s
						OR %(start_date)s BETWEEN from_date AND to_date
						OR %(end_date)s BETWEEN from_date AND to_date
					)
					AND docstatus IN (1)
					AND reference_name = %(ref_name)s
				)
				{}
				ORDER BY t2.desuup_name
			""".format(cond), params, as_dict=True)

		for desuup in desuup_list:
			if getdate(desuup['from_date']) < getdate(self.start_date):
				desuup['from_date'] = self.start_date
			if getdate(desuup['to_date']) > getdate(self.end_date):
				desuup['to_date'] = self.end_date
			
			# For Trainee, use reporting_date as from_date if it falls within the same month as start_date
			if self.payment_for == "Trainee" and desuup.get('reporting_date'):
				reporting_date = getdate(desuup['reporting_date'])
				start_date = getdate(desuup['from_date'])
				if reporting_date.month == start_date.month and reporting_date.year == start_date.year:
					desuup['from_date'] = reporting_date

			# For OJT, use reported_date as from_date if it falls within the same month as start_date
			if self.payment_for == "OJT" and desuup.get('reported_date'):
				reported_date = getdate(desuup['reported_date'])
				start_date = getdate(desuup['from_date'])
				if reported_date.month == start_date.month and reported_date.year == start_date.year:
					desuup['from_date'] = reported_date
			
			# Use exit_date as to_date if it exists and falls within the date range
			# if desuup.get('exit_date'):
			# 	exit_date = getdate(desuup['exit_date'])
			# 	end_date = getdate(desuup['to_date'])
			# 	if exit_date < end_date:
			# 		desuup['to_date'] = exit_date

			if desuup.get('exit_date'):
				exit_date = getdate(desuup['exit_date'])
				end_date = getdate(desuup['to_date'])
				if exit_date.month == end_date.month and exit_date.year == end_date.year:
					desuup['to_date'] = exit_date

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
		self.calculate_amount()
		return self.number_of_desuups

	@frappe.whitelist()
	def make_accounting_entry(self):
		# Retrieve accounts from settings
		adv_account = frappe.db.get_single_value("Desuup Settings", "mess_advance_account")
		deduction_account = frappe.db.get_single_value("Desuup Settings", "deduction_account")
		arrear_account = frappe.db.get_single_value("Desuup Settings", "arrear_account")
		refundable_account = frappe.db.get_single_value("Desuup Settings", "refundable_mess_account")

		if self.payment_for == "Trainee":
			payable_account = frappe.db.get_single_value("Desuup Settings", "stipend_payable_account")
			expense_account = frappe.db.get_single_value("Desuup Settings", "stipend_expense_account")
		elif self.payment_for == "OJT" or self.payment_for == "Production":
			payable_account = frappe.db.get_single_value("Desuup Settings", "ojt_payable_account")
			expense_account = frappe.db.get_single_value("Desuup Settings", "ojt_expense_account")

		bank_account = frappe.db.get_value("Company", self.company, "default_bank_account")
		if not bank_account:
			frappe.throw("Default bank account not set for company.")

		# get training center party
		if self.payment_for == "Trainee":
			party = frappe.db.get_value("Training Center", self.training_center, "party")
			party_name = frappe.db.get_value("Employee", party, "employee_name")
			if not party:
				frappe.throw("Please set part in Training Center {}".format(frappe.bold(self.training_center)))
		else:
			party = frappe.db.get_value("Desuup Deploument Entry", self.desuup_deployment, "party")
			party_name = frappe.db.get_value("Desuup Deploument Entry", self.desuup_deployment, "party_name")
			if not party:
				frappe.throw("Please set part in {}".format(frappe.get_desk_link("Desuup Deployment Entry", self.desuup_deployment)))

		# Initialize dictionaries for grouping
		aggregated_values = {}

		# Group data by cost center
		for item in self.items:
			cost_center = item.get('cost_center')

			if not cost_center:
				frappe.throw("Cost center is missing in one of the items.")

			if cost_center not in aggregated_values:
				aggregated_values[cost_center] = {
					'stipend_expense': 0,
					'mess_advance_refundable': 0,
					'mess_advance_amount': 0,
					'deduction': 0,
					'arrear_account': 0,
					'stipend_payable': 0,
					'net_amount': 0,
					'total_refundable': 0,
					'ojt_expense': 0,
					'ojt_payable': 0
				}

			aggregated_values[cost_center]['stipend_expense'] += item.get('stipend_amount', 0) + item.get('mess_advance_used', 0)
			aggregated_values[cost_center]['mess_advance_refundable'] += item.get('refundable_amount', 0)
			aggregated_values[cost_center]['mess_advance_amount'] += item.get('mess_advance_amount', 0)
			aggregated_values[cost_center]['deduction'] += item.get('total_deduction_amount', 0)
			aggregated_values[cost_center]['arrear_account'] += item.get('total_arrear_amount', 0)
			aggregated_values[cost_center]['stipend_payable'] += item.get('net_amount', 0)
			aggregated_values[cost_center]['total_refundable'] += item.get('refundable_amount', 0)
			aggregated_values[cost_center]['net_amount'] += item.get('net_amount', 0)

			# FOR OJT
			# aggregated_values[cost_center]['ojt_expense'] += item.get('total_amount', 0)
			# aggregated_values[cost_center]['ojt_payable'] += item.get('net_amount', 0)

		# Journal entry templates
		journal_templates = [
			{
				"type": "payable",
				"entry_type": "Journal Entry",
				"series": "Journal Voucher",
				"title": "payables",
				"is_submitable": 1,
			},
			{
				"type": "payment",
				"entry_type": "Bank Entry",
				"series": "Bank Payment Voucher",
				"title": "To Bank",
				"is_submitable": 0,
			},
			{
				"type": "receivable",
				"entry_type": "Bank Entry",
				"series": "Bank Receipt Voucher",
				"title": "Mess Advance Refund",
				"is_submitable": 0,
			},
		]

		# Create the journal entries
		for journal in journal_templates:
			je = frappe.new_doc("Journal Entry")
			je.flags.ignore_permissions = 1

			je.update({
				"doctype": "Journal Entry",
				"voucher_type": journal["entry_type"],
				"naming_series": journal["series"],
				"title": journal["title"],
				"posting_date": frappe.utils.nowdate(),
				"company": self.company,
				"branch": self.branch,
				"reference_doctype": self.doctype,
				"reference_name": self.name,
			})

			accounts = []

			if journal["type"] == "payable":
				for cost_center, values in aggregated_values.items():
					if values['stipend_expense'] > 0:
						accounts.append({
							'account': expense_account,
							'debit_in_account_currency': values['stipend_expense'],
							'cost_center': cost_center,
							"reference_type": self.doctype,
							"reference_name": self.name,
						})
					if values['mess_advance_refundable'] > 0:
						accounts.append({
							'account': refundable_account,
							'debit_in_account_currency': values['mess_advance_refundable'],
							'cost_center': cost_center,
							'party_type': 'Employee',
							'party': party,
							'party_name': party_name,
							"reference_type": self.doctype,
							"reference_name": self.name,
						})
					if values['arrear_account'] > 0:
						accounts.append({
							'account': arrear_account,
							'debit_in_account_currency': values['arrear_account'],
							'cost_center': cost_center,
							"reference_type": self.doctype,
							"reference_name": self.name,
						})
					if values['mess_advance_amount'] > 0:
						accounts.append({
							'account': adv_account,
							'credit_in_account_currency': values['mess_advance_amount'],
							'cost_center': cost_center,
							"reference_type": self.doctype,
							"reference_name": self.name,
						})
					if values['deduction'] > 0:
						accounts.append({
							'account': deduction_account,
							'credit_in_account_currency': values['deduction'],
							'cost_center': cost_center,
							"reference_type": self.doctype,
							"reference_name": self.name,
						})
					if values['stipend_payable'] > 0:
						accounts.append({
							'account': payable_account,
							'credit_in_account_currency': values['stipend_payable'],
							'cost_center': cost_center,
							"reference_type": self.doctype,
							"reference_name": self.name,
						})

			elif journal["type"] == "payment":
				for cost_center, values in aggregated_values.items():
					if values['net_amount'] > 0:
						accounts.append({
							'account': payable_account,
							'debit_in_account_currency': values['net_amount'],
							'cost_center': cost_center,
							"reference_type": self.doctype,
							"reference_name": self.name,
						})
						accounts.append({
							'account': bank_account,
							'credit_in_account_currency': values['net_amount'],
							'cost_center': cost_center,
							"reference_type": self.doctype,
							"reference_name": self.name,
						})

			elif journal["type"] == "receivable":
				for cost_center, values in aggregated_values.items():
					if values['total_refundable'] > 0:
						accounts.append({
							'account': bank_account,
							'debit_in_account_currency': values['total_refundable'],
							'cost_center': cost_center,
							"reference_type": self.doctype,
							"reference_name": self.name,
						})
						accounts.append({
							'account': refundable_account,
							'credit_in_account_currency': values['total_refundable'],
							'cost_center': cost_center,
							'party_type': 'Employee',
							'party': party,
							'party_name': party_name,
							'reference_type': self.doctype,
							'reference_name': self.name,
						})

			if accounts:
				total_debit = sum(account.get('debit_in_account_currency', 0) for account in accounts)
				total_credit = sum(account.get('credit_in_account_currency', 0) for account in accounts)

				# Adjust for rounding or discrepancies
				if abs(total_debit - total_credit) > 0.005:  # Adjust tolerance as needed
					frappe.throw(f"Total Debit ({total_debit}) does not equal Total Credit ({total_credit}). Difference is {abs(total_debit - total_credit)}")

				for account in accounts:
					je.append('accounts', account)

				je.insert()
				if journal["is_submitable"]:
					je.submit()

# ePayment Begins
@frappe.whitelist()
def make_bank_payment(source_name, target_doc=None):
	def set_missing_values(obj, target, source_parent):
		# target.payment_type = "One-One Payment"
		target.transaction_type = "Desuup Payout Entry"
		target.posting_date = get_datetime()
		target.from_date = None
		target.to_date = None
		target.month = ""
		target.remarks = 'Desuup payment'
		target.paid_from = frappe.db.get_value("Branch", target.branch,"expense_bank_account")
		target.get_entries()

	doc = get_mapped_doc("Desuup Payout Entry", source_name, {
			"Desuup Payout Entry": {
				"doctype": "Bank Payment",
				"field_map": {
					"name": "transaction_no",
				},
				"postprocess": set_missing_values,
			},
	}, target_doc, ignore_permissions=True)
	return doc
# ePayment Ends

	# @frappe.whitelist()
	# def make_accounting_entry(self):
	# 	# Retrieve accounts from settings
	# 	adv_account = frappe.db.get_single_value("Desuup Settings", "mess_advance_account")
	# 	deduction_account = frappe.db.get_single_value("Desuup Settings", "deduction_account")
	# 	arrear_account = frappe.db.get_single_value("Desuup Settings", "arrear_account")
	# 	refundable_account = frappe.db.get_single_value("Desuup Settings", "refundable_mess_account")

	# 	if self.payment_for == "Trainee":
	# 		payable_account = frappe.db.get_single_value("Desuup Settings", "stipend_payable_account")
	# 		expense_account = frappe.db.get_single_value("Desuup Settings", "stipend_expense_account")
	# 	elif self.payment_for == "OJT":
	# 		payable_account = frappe.db.get_single_value("Desuup Settings", "ojt_payable_account")
	# 		expense_account = frappe.db.get_single_value("Desuup Settings", "ojt_expense_account")

	# 	bank_account = frappe.db.get_value("Company", self.company, "default_bank_account")
	# 	if not bank_account:
	# 		frappe.throw("Default bank account not set for company.")

	# 	# Initialize dictionaries for grouping
	# 	cost_center_wise = {}

	# 	# Group data by cost center
	# 	items_dict = [item.as_dict() for item in self.items]
	# 	for item in self.items:
	# 		cost_center = item.get('cost_center')

	# 		if not cost_center:
	# 			frappe.throw("Cost center is missing in one of the items.")

	# 		if cost_center not in cost_center_wise:
	# 			cost_center_wise[cost_center] = {
	# 				'stipend_expense': 0,
	# 				'mess_advance_refundable': 0,
	# 				'mess_advance_amount': 0,
	# 				'deduction': 0,
	# 				'arrear_account': 0,
	# 				'stipend_payable': 0,
	# 				'net_amount': 0,
	# 				'total_refundable': 0
	# 			}

	# 		cost_center_wise[cost_center]['stipend_expense'] += item.get('stipend_amount', 0) + item.get('mess_advance_used', 0)
	# 		cost_center_wise[cost_center]['mess_advance_refundable'] += item.get('refundable_amount', 0)
	# 		cost_center_wise[cost_center]['mess_advance_amount'] += item.get('mess_advance_amount', 0)
	# 		cost_center_wise[cost_center]['deduction'] += item.get('total_deduction_amount', 0)
	# 		cost_center_wise[cost_center]['arrear_account'] += item.get('total_arrear_amount', 0)
	# 		cost_center_wise[cost_center]['stipend_payable'] += item.get('net_amount', 0)
	# 		cost_center_wise[cost_center]['net_amount'] += item.get('net_amount', 0)
	# 		cost_center_wise[cost_center]['total_refundable'] += item.get('refundable_amount', 0)

	# 	# Journal entry templates
	# 	journal_templates = [
	# 		{
	# 			"type": "payable",
	# 			"entry_type": "Journal Entry",
	# 			"series": "Journal Voucher",
	# 			"title": "payables",
	# 			"is_submitable": 1,
	# 		},
	# 		{
	# 			"type": "payment",
	# 			"entry_type": "Bank Entry",
	# 			"series": "Bank Payment Voucher",
	# 			"title": "To Bank",
	# 			"is_submitable": 0,
	# 		},
	# 		{
	# 			"type": "receivable",
	# 			"entry_type": "Bank Entry",
	# 			"series": "Bank Receipt Voucher",
	# 			"title": "Mess Advance Refund",
	# 			"is_submitable": 0,
	# 		},
	# 	]

	# 	# Create the journal entries
	# 	for journal in journal_templates:
	# 		for cost_center, values in cost_center_wise.items():
	# 			if journal["type"] == "receivable" and values['total_refundable'] <= 0:
	# 				continue

	# 			je = frappe.new_doc("Journal Entry")
	# 			je.flags.ignore_permissions = 1

	# 			je.update({
	# 				"doctype": "Journal Entry",
	# 				"voucher_type": journal["entry_type"],
	# 				"naming_series": journal["series"],
	# 				"title": journal["title"],
	# 				"posting_date": frappe.utils.nowdate(),
	# 				"company": self.company,
	# 				"branch": self.branch,
	# 				"reference_doctype": self.doctype,
	# 				"reference_name": self.name,
	# 			})

	# 			accounts = []

	# 			if journal["type"] == "payable":
	# 				if values['stipend_expense'] > 0:
	# 					accounts.append({
	# 						'account': expense_account,
	# 						'debit_in_account_currency': values['stipend_expense'],
	# 						'cost_center': cost_center,
	# 						"reference_type": self.doctype,
	# 						"reference_name": self.name,
	# 					})
	# 				if values['mess_advance_refundable'] > 0:
	# 					accounts.append({
	# 						'account': refundable_account,
	# 						'debit_in_account_currency': values['mess_advance_refundable'],
	# 						'cost_center': cost_center,
	# 						"reference_type": self.doctype,
	# 						"reference_name": self.name,
	# 					})
	# 				if values['arrear_account'] > 0:
	# 					accounts.append({
	# 						'account': arrear_account,
	# 						'debit_in_account_currency': values['arrear_account'],
	# 						'cost_center': cost_center,
	# 						"reference_type": self.doctype,
	# 						"reference_name": self.name,
	# 					})
	# 				if values['mess_advance_amount'] > 0:
	# 					accounts.append({
	# 						'account': adv_account,
	# 						'credit_in_account_currency': values['mess_advance_amount'],
	# 						'cost_center': cost_center,
	# 						"reference_type": self.doctype,
	# 						"reference_name": self.name,
	# 					})
	# 				if values['deduction'] > 0:
	# 					accounts.append({
	# 						'account': deduction_account,
	# 						'credit_in_account_currency': values['deduction'],
	# 						'cost_center': cost_center,
	# 						"reference_type": self.doctype,
	# 						"reference_name": self.name,
	# 					})
	# 				if values['stipend_payable'] > 0:
	# 					accounts.append({
	# 						'account': payable_account,
	# 						'credit_in_account_currency': values['stipend_payable'],
	# 						'cost_center': cost_center,
	# 						"reference_type": self.doctype,
	# 						"reference_name": self.name,
	# 					})

	# 			elif journal["type"] == "payment":
	# 				if values['net_amount'] > 0:
	# 					accounts.append({
	# 						'account': payable_account,
	# 						'debit_in_account_currency': values['net_amount'],
	# 						'cost_center': cost_center,
	# 						"reference_type": self.doctype,
	# 						"reference_name": self.name,
	# 					})
	# 					accounts.append({
	# 						'account': bank_account,
	# 						'credit_in_account_currency': values['net_amount'],
	# 						'cost_center': cost_center,
	# 						"reference_type": self.doctype,
	# 						"reference_name": self.name,
	# 					})

	# 			elif journal["type"] == "receivable":
	# 				if values['total_refundable'] > 0:
	# 					accounts.append({
	# 						'account': bank_account,
	# 						'debit_in_account_currency': values['total_refundable'],
	# 						'cost_center': cost_center,
	# 						"reference_type": self.doctype,
	# 						"reference_name": self.name,
	# 					})
	# 					accounts.append({
	# 						'account': refundable_account,
	# 						'credit_in_account_currency': values['total_refundable'],
	# 						'cost_center': cost_center,
	# 						"reference_type": self.doctype,
	# 						"reference_name": self.name,
	# 					})

	# 			if accounts:
	# 				total_debit = sum(account.get('debit_in_account_currency', 0) for account in accounts)
	# 				total_credit = sum(account.get('credit_in_account_currency', 0) for account in accounts)

	# 				# Adjust for rounding or discrepancies
	# 				if abs(total_debit - total_credit) > 0.005:  # Adjust tolerance as needed
	# 					frappe.throw(f"Total Debit ({total_debit}) does not equal Total Credit ({total_credit}). Difference is {abs(total_debit - total_credit)}")

	# 				for account in accounts:
	# 					je.append('accounts', account)

	# 				je.insert()
	# 				if journal["is_submitable"]:
	# 					je.submit()
