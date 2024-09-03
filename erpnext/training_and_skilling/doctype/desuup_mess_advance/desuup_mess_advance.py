# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
import calendar
import frappe.translate
from datetime import date, timedelta
from frappe import _
from frappe.utils import cint, flt, nowdate, add_days, getdate, fmt_money, add_to_date, DATE_FORMAT, date_diff, get_last_day
from frappe.model.document import Document


class DesuupMessAdvance(Document):
	def validate(self):
		# self.validate_month_entry()
		# self.validate_duplicate_desuup_entry()
		# self.validate_is_exists_in_training_management()
		# self.validate_duplicate_monthly_advance()
		self.calculate_mess_amount()

	def on_submit(self):
		self.db_set("payment_status", "Unpaid")
		self.post_journal_entry()

	def calculate_mess_amount(self):
		month_start_date, month_end_date = self.get_start_end_month_date()

		mess_amt = frappe.db.get_single_value("Desuup Settings", "mess_advance")
		total_adv = 0

		days_in_month = calendar.monthrange(month_end_date.year, month_end_date.month)[1]
	
		for adv in self.items:
			days = (getdate(adv.to_date) - getdate(adv.from_date)).days + 1
			if days != days_in_month:
				mess_adv_amt = flt(mess_amt) / flt(30)
				adv.amount = flt(mess_adv_amt * days, 2)
			else:
				adv.amount = flt(mess_amt, 2)
			total_adv += adv.amount
		self.total_advance = total_adv

	def validate_duplicate_desuup_entry(self):
		# validating duplicates entry in a table
		desuups = set()
		for child in self.get('items'):
			if child.desuup in desuups:
				frappe.throw(f"Duplicate entry for Desuup <strong>{child.desuup}</strong>")
			desuups.add(child.desuup)
	
	def validate_is_exists_in_training_management(self):
		for item in self.items:
			if not self.is_desuup_exists_in_tm(item.desuup):
				frappe.throw(f"Desuup {item.desuup} does not exist in the Training Management or is not a mess member")

	def is_desuup_exists_in_tm(self, desuup):
		existing_items = frappe.db.sql(f"""
			SELECT desuup_id as desuup, is_mess_member
			FROM `tabTrainee Details`
			WHERE parenttype = %s
			AND parent = %s
		""", (self.reference_doctype, self.reference_name), as_dict=True)

		# Check if the item_code exists in the fetched items
		for d in existing_items:
			if d['desuup'] == desuup and d['is_mess_member']:
				return True
		return False
	
	def validate_duplicate_monthly_advance(self):
		for child in self.get('items'):
			existing_advance = frappe.db.sql("""
									SELECT t1.name
									FROM `tabDesuup Mess Advance` t1, `tabDesuup Mess Advance Item` t2
									WHERE t1.name = t2.parent
									AND t1.docstatus < 2
									AND t2.desuup = %s
									AND t1.month = %s
									AND t1.reference_name = %s
									AND t2.parent != %s
								""", (child.desuup, self.month, self.reference_name, self.name))
			if existing_advance:
				frappe.throw(f"Desuup <strong>{child.desuup}</strong> has already claimed an advance for month <strong>{self.month}</strong>.")

	def get_conditions(self):
		cond = ''
		if self.training_management:
			cond += " and t1.name = '{}'".format(self.training_management)
		if self.training_center:
			cond += " and t1.training_center = '{}'".format(self.training_center)
		return cond
	
	def get_desuup_list(self):
		# Validate necessary fields
		if self.advance_for == "Trainee":
			if not self.training_center:
				frappe.throw("Please set Training Center")
		else:
			if not self.desuup_deployment_entry:
				frappe.throw("Please set Desuup Deployment Entry")

		# Define the base query for desuup_list
		conditions = self.get_conditions()
		base_query = """
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
				AND t2.is_mess_member = 1 
				AND (
					t1.training_start_date BETWEEN %(from_date)s AND %(to_date)s 
					OR t1.training_end_date BETWEEN %(from_date)s AND %(to_date)s
					OR %(from_date)s BETWEEN t1.training_start_date AND t1.training_end_date
					OR %(to_date)s BETWEEN t1.training_start_date AND t1.training_end_date
				)
				AND (
					t2.exit_date IS NULL 
					OR t2.exit_date > %(from_date)s
				)
				{}
			ORDER BY 
				t2.desuup_name
		""".format(conditions)

		# Parameters for the base query
		params = {
			'from_date': getdate(self.from_date),
			'to_date': getdate(self.to_date),
		}

		# Add parameters if conditions include them
		if self.training_management:
			params['training_management'] = self.training_management
		if self.training_center:
			params['training_center'] = self.training_center

		# Fetch desuup_list
		desuup_list = frappe.db.sql(base_query, params, as_dict=True)

		# Determine reference name for the next query
		reference_name = self.training_management if self.advance_for == "Trainee" else self.desuup_deployment

		# Define the query for previous advances
		query = """
			SELECT t2.desuup, t2.from_date, t2.to_date 
			FROM `tabDesuup Mess Advance` t1
			JOIN `tabDesuup Mess Advance Item` t2 ON t1.name = t2.parent
			WHERE t1.training_center = %s
			AND t1.from_date = %s
			AND t1.to_date = %s
			AND t2.reference_name = %s
		"""

		# Fetch previous advances
		previous_adv = frappe.db.sql(query, (self.training_center, self.from_date, self.to_date, reference_name), as_dict=True)

		# Convert previous_adv to a dictionary for faster lookup
		prev_adv_dict = {p['desuup']: p for p in previous_adv}

		# Process and adjust desuup_list based on previous advances
		filtered_desuup_list = []
		for desuup in desuup_list:
			# Check if desuup is in previous_adv
			prev = prev_adv_dict.get(desuup['desuup'])
			if prev:
				if getdate(desuup['to_date']) > getdate(self.to_date):
					desuup['to_date'] = self.to_date

				if getdate(desuup['from_date']) < getdate(prev['to_date']) + timedelta(days=1):
					desuup['from_date'] = getdate(prev['to_date']) + timedelta(days=1)
					
				if desuup.get('exit_date'):
					exit_date = getdate(desuup['exit_date'])
					end_date = getdate(desuup['to_date'])
					if exit_date.month == end_date.month and exit_date.year == end_date.year:
						desuup['to_date'] = exit_date
			else:
				# If not in previous_adv, adjust dates
				if getdate(desuup['from_date']) < getdate(self.from_date):
					desuup['from_date'] = self.from_date
				if getdate(desuup['to_date']) > getdate(self.to_date):
					desuup['to_date'] = self.to_date

				if desuup.get('reporting_date'):
					reporting_date = getdate(desuup['reporting_date'])
					start_date = getdate(desuup['from_date'])
					if reporting_date.month == start_date.month and reporting_date.year == start_date.year:
						desuup['from_date'] = reporting_date

				if desuup.get('exit_date'):
					exit_date = getdate(desuup['exit_date'])
					end_date = getdate(desuup['to_date'])
					if exit_date.month == end_date.month and exit_date.year == end_date.year:
						desuup['to_date'] = exit_date

			# Check if exit_date is less than from_date
			if desuup.get('exit_date'):
				exit_date = getdate(desuup['exit_date'])
				if exit_date < getdate(desuup['from_date']):
					continue  # Skip this desuup if the condition is met

			filtered_desuup_list.append(desuup)

		return filtered_desuup_list


	
	@frappe.whitelist()
	def get_desuup_details(self):
		self.set('items', [])
		desuups = self.get_desuup_list()
		if not desuups:
			frappe.throw(_("No desuups for the mentioned criteria"))

		for d in desuups:
			self.append('items', d)

		self.number_of_desuups = len(desuups)
		self.calculate_mess_amount()
		return self.number_of_desuups

	def post_journal_entry(self):
		accounts = []
		bank_account = frappe.db.get_value("Company", self.company, "default_bank_account")
		debit_account = frappe.db.get_single_value("Desuup Settings", "mess_advance_account")
		if not bank_account:
			frappe.throw("Set default bank account in company {}".format(frappe.bold(self.company)))

		# Dictionary to hold aggregated amounts by cost center
		cost_center_amounts = {}
		for d in self.items:
			if d.cost_center not in cost_center_amounts:
				cost_center_amounts[d.cost_center] = 0
			cost_center_amounts[d.cost_center] += flt(d.amount, 2)

		# Create journal entry lines for each cost center
		for cost_center, amount in cost_center_amounts.items():
			accounts.append({
				"account": debit_account,
				"debit_in_account_currency": amount,
				"cost_center": cost_center,
				"party_check": 1,
				"party_type": "Employee",
				"party": self.paid_to,
				"party_name": frappe.db.get_value("Employee", self.paid_to, "employee_name"),
				"reference_type": self.doctype,
				"reference_name": self.name,
			})

		accounts.append({
			"account": bank_account,
			"credit_in_account_currency": flt(self.total_advance, 2),
			"cost_center": self.cost_center,
		})

		je = frappe.new_doc("Journal Entry")
		je.flags.ignore_permission = 1
		je.update({
			"doctype": "Journal Entry",
			"branch": self.branch,
			"posting_date": self.posting_date,
			"voucher_type": "Bank Entry",
			"naming_series": "Bank Payment Voucher",
			"company": self.company,
			"reference_doctype": self.doctype,
			"reference_name": self.name,
			"accounts": accounts
		})
		je.insert()
		self.db_set('journal_entry', je.name)
		frappe.msgprint(_('Journal Entry {0} posted to accounts').format(frappe.get_desk_link("Journal Entry", je.name)))


	@frappe.whitelist()
	def set_dates(self):
		# self.validate_month_entry()
		month_start_date, month_end_date = self.get_start_end_month_date()

		self.from_date = month_start_date
		self.to_date = month_end_date

	def get_start_end_month_date(self):
		month_start_date = "-".join([str(date.today().year), self.month, "01"])
		month_end_date   = get_last_day(month_start_date)

		return month_start_date, month_end_date
	
	def validate_month_entry(self):
		from_date, to_date = self.get_training_start_end_date()

		start_month = from_date.month
		end_month = to_date.month

		try:
			validate_month = int(self.month)
		except ValueError:
			frappe.throw("Month must be a valid number in 'MM' format.")
		
		# Check if the month_to_validate is within the training period
		if start_month <= end_month:
			# Period within the same year
			if not (start_month <= validate_month <= end_month):
				frappe.throw("The month does not fall within the training period. i.e. from {} to {}".format(frappe.bold(from_date), frappe.bold(to_date)))
		else:
			# Period spans across two years
			if not (validate_month >= start_month or validate_month <= end_month):
				frappe.throw("The month does not fall within the training period. i.e. from {} to {}".format(frappe.bold(from_date), frappe.bold(to_date)))

	def get_training_start_end_date(self):
		if self.reference_doctype == "Training Management" and self.reference_name:
			from_date, to_date = frappe.db.get_value("Training Management", self.reference_name, ['training_start_date', 'training_end_date'])

			if not from_date or not to_date:
				frappe.throw("Training start date or end date is not set for the reference name.")
			
			from_date = getdate(from_date)
			to_date = getdate(to_date)

			return from_date, to_date
		else:
			frappe.throw("Reference doctype or reference name is not set.")


	@frappe.whitelist()
	def set_advance_party(self):
		self.paid_to = frappe.db.get_value("Training Center", self.training_center, "party")
		if not self.paid_to:
			frappe.throw("Please set party in training center '{}'".format(frappe.get_desk_link("Training Center", self.training_center)))

	