# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import cint, flt, today, get_datetime
from frappe.model.document import Document
from frappe.model.naming import make_autoname


class MRTDSReceiptUpdate(Document):
	def validate(self):
		self.validate_filters()
		self.validate_employees()  # Calculate totals from employee rows
		self.calculate_total()

	def on_update(self):
		if self.purpose == "Employee Salary":
			return
		else:
			self.check_duplicate_entries()

	def on_submit(self):
		if self.purpose in ("Employee Salary", "Bulk Leave Encashment"):
			self.update_tds_receipt_number()
		else:
			self.make_tds_receipt_entries()

		# Create journal entry after successful submission (Draft status)
		self.post_journal_entry()

	def on_cancel(self):
		if self.purpose in ("Employee Salary", "Bulk Leave Encashment"):
			self.update_tds_receipt_number(cancel=True)
		else:
			frappe.db.sql(
				"delete from `tabTDS Receipt Entry` where tds_receipt_update = '{}'".format(self.name)
			)

		# Cancel or delete the journal entry
		self.cancel_journal_entry()

	def validate_employees(self):
		"""Calculate total gross salary and total salary tax from employee rows"""
		if not self.employees:
			self.total_gross_salary = 0
			self.total_salary_tax = 0
			return

		self.number_of_employees = len(self.employees)

		total_salary_tax = 0.0
		gross_salary = 0.0

		for sd in self.employees:
			# Get values from the employee row directly
			gross_salary += flt(sd.gross_salary or 0)
			total_salary_tax += flt(sd.salary_tax or 0)

		self.total_gross_salary = gross_salary
		self.total_salary_tax = total_salary_tax

	def make_filters(self):
		filters = frappe._dict(
			company=self.company,
			fiscal_year=self.fiscal_year,
			month=self.month,
			branch=self.branch
		)
		return filters

	def update_tds_receipt_number(self, cancel=False):
		if self.purpose == "Employee Salary":
			self.update_mr_invoice_entry_items(cancel)
		elif self.purpose == "Bulk Leave Encashment":
			self.update_bulk_leave_encashment(cancel)

	@frappe.whitelist()
	def fill_employee_details(self):
		filters = self.make_filters()

		# Debug: Log the filters being used
		frappe.log_error(
			title="MR TDS Receipt Update - Filters",
			message=f"Filters being used: Company={filters.company}, Fiscal Year={filters.fiscal_year}, Month={filters.month}, Branch={filters.branch}"
		)

		employees = self.get_mr_invoice_entry_employees(filters)
		self.set("employees", [])

		if not employees:
			error_msg = _(
				"No MR employees found for the mentioned criteria:<br>Company: {0}<br>Fiscal Year: {1}<br>Month: {2}<br>Branch: {3}"
			).format(
				frappe.bold(self.company),
				frappe.bold(self.fiscal_year),
				frappe.bold(self.month),
				frappe.bold(self.branch)
			)
			frappe.throw(error_msg, title=_("No MR employees found"))

		self.set("employees", employees)
		self.number_of_employees = len(self.employees)

		# Recalculate totals after filling employees
		self.validate_employees()

	def get_month_mapping(self, month_input):
		"""Convert month number to month name"""
		month_map = {
			'01': 'Jan',
			'02': 'Feb',
			'03': 'Mar',
			'04': 'Apr',
			'05': 'May',
			'06': 'Jun',
			'07': 'Jul',
			'08': 'Aug',
			'09': 'Sep',
			'10': 'Oct',
			'11': 'Nov',
			'12': 'Dec'
		}

		# If month is already a 3-letter abbreviation
		if month_input in ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']:
			return month_input

		# If month is a number with leading zero
		if month_input in month_map:
			return month_map[month_input]

		# If month is a number without leading zero
		if month_input.lstrip('0') in [str(i) for i in range(1, 13)]:
			month_num = month_input.lstrip('0')
			if len(month_num) == 1:
				month_num = '0' + month_num
			return month_map.get(month_num, month_input)

		return month_input

	def get_mr_invoice_entry_employees(self, filters):
		"""Fetch employees from MR Invoice Entry items based on parent MR Invoice Entry filters"""
		employees = []

		# Convert month to proper format
		month_value = self.get_month_mapping(filters.month)

		frappe.log_error(
			title="MR TDS Receipt Update - Month Mapping",
			message=f"Original month: {filters.month}, Mapped month: {month_value}"
		)

		# First, let's check what months exist in the system
		month_check_query = """
			SELECT DISTINCT month 
			FROM `tabMR Invoice Entry`
			WHERE docstatus = 1
			AND company = %(company)s
			AND fiscal_year = %(fiscal_year)s
			AND branch = %(branch)s
		"""

		available_months = frappe.db.sql(month_check_query, filters, as_dict=True)

		if available_months:
			month_list = [m.month for m in available_months]
			frappe.log_error(
				title="MR TDS Receipt Update - Available Months",
				message=f"Available months: {', '.join(month_list)}"
			)

		# First check if any MR Invoice Entry exists with these filters
		check_query = """
			SELECT COUNT(*) as count
			FROM `tabMR Invoice Entry`
			WHERE docstatus = 1
			AND company = %(company)s
			AND fiscal_year = %(fiscal_year)s
			AND branch = %(branch)s
		"""

		# Try with mapped month first
		check_query_with_month = check_query + " AND month = %(month)s"
		check_filters = filters.copy()
		check_filters.month = month_value

		check_result = frappe.db.sql(check_query_with_month, check_filters, as_dict=True)

		if check_result and check_result[0].count == 0:
			# If no results with mapped month, try with original month
			check_filters.month = filters.month
			check_result = frappe.db.sql(check_query_with_month, check_filters, as_dict=True)

			if check_result and check_result[0].count == 0:
				# If still no results, try without month filter to see if any data exists
				check_result_no_month = frappe.db.sql(check_query, filters, as_dict=True)
				if check_result_no_month and check_result_no_month[0].count > 0:
					# Data exists but with different month format
					available_months = frappe.db.sql("""
						SELECT DISTINCT month 
						FROM `tabMR Invoice Entry`
						WHERE docstatus = 1
						AND company = %(company)s
						AND fiscal_year = %(fiscal_year)s
						AND branch = %(branch)s
					""", filters, as_dict=True)

					month_list = [m.month for m in available_months]
					frappe.msgprint(
						_("Available months in the system: {0}").format(", ".join(month_list)),
						alert=True,
						indicator="orange"
					)

		# Build the main query to get MR Invoice Entry Items
		# CORRECTED: Using mr_employee and mr_employee_name
		query = """
			SELECT 
				mrie.mr_employee as employee,
				mrie.mr_employee_name as employee_name,
				mrie.name as mr_invoice_entry_item,
				mrie.grand_total as gross_salary,
				mrie.salary_tax as salary_tax,
				mrie.tds_amount as tds_amount,
				mrie.other_deduction as other_deduction,
				mrie.total_days_worked as total_days_worked,
				mrie.total_daily_wage_amount as total_daily_wage_amount,
				mrie.total_ot_hrs as total_ot_hrs,
				mrie.total_ot_amount as total_ot_amount,
				mrie.net_payable_amount as net_payable_amount,
				mrie.grand_total_after_advance as grand_total_after_advance,
				mrie.total_advance as total_advance,
				mri.branch as branch,
				mri.month as month,
				mri.fiscal_year as fiscal_year,
				mri.name as mr_invoice_entry,
				mri.company as company,
				mri.posting_date as posting_date,
				mri.cost_center as cost_center
			FROM 
				`tabMR Invoice Entry Item` mrie
			INNER JOIN 
				`tabMR Invoice Entry` mri ON mrie.parent = mri.name
			WHERE 
				mri.docstatus = 1 
				AND mri.company = %(company)s
				AND mri.fiscal_year = %(fiscal_year)s
				AND mri.branch = %(branch)s
				AND mrie.salary_tax > 0
				AND mrie.submission_status = 'Successful'
		"""

		# Try with mapped month first
		query_with_month = query + " AND mri.month = %(month)s"
		query_filters = filters.copy()
		query_filters.month = month_value

		results = frappe.db.sql(query_with_month, query_filters, as_dict=True)

		# If no results with mapped month, try with original month
		if not results:
			query_filters.month = filters.month
			results = frappe.db.sql(query_with_month, query_filters, as_dict=True)

		# If still no results, try with LIKE (case insensitive)
		if not results:
			query_like = query + " AND LOWER(mri.month) LIKE LOWER(%(month)s)"
			query_filters.month = '%' + filters.month + '%'
			results = frappe.db.sql(query_like, query_filters, as_dict=True)

		# Debug: Log the results
		frappe.log_error(
			title="MR TDS Receipt Update - Query Results",
			message=f"Found {len(results)} MR Invoice Entry Items"
		)

		for result in results:
			# Create employee record with all MR Invoice Entry Item data
			employee_record = frappe._dict({
				"employee": result.get('employee'),
				"employee_name": result.get('employee_name'),
				"branch": result.get('branch'),
				"mr_invoice_entry_item": result.get('mr_invoice_entry_item'),
				"mr_invoice_entry": result.get('mr_invoice_entry'),
				"gross_salary": result.get('gross_salary') or 0,
				"salary_tax": result.get('salary_tax') or 0,
				"tds_amount": result.get('tds_amount') or 0,
				"other_deduction": result.get('other_deduction') or 0,
				"total_days_worked": result.get('total_days_worked') or 0,
				"total_daily_wage_amount": result.get('total_daily_wage_amount') or 0,
				"total_ot_hrs": result.get('total_ot_hrs') or 0,
				"total_ot_amount": result.get('total_ot_amount') or 0,
				"net_payable_amount": result.get('net_payable_amount') or 0,
				"grand_total_after_advance": result.get('grand_total_after_advance') or 0,
				"total_advance": result.get('total_advance') or 0,
				"company": result.get('company'),
				"posting_date": result.get('posting_date'),
				"cost_center": result.get('cost_center'),
				"source": "MR Invoice Entry"
			})
			employees.append(employee_record)

		return employees

	def update_bulk_leave_encashment(self, cancel):
		if not self.bulk_leave_encashment:
			frappe.throw("No Bulk Leave Encashment document selected.")

		if cancel:
			receipt_number = None or ""
			receipt_date = None or ""
		else:
			receipt_number = self.tds_receipt_number
			receipt_date = self.tds_receipt_date

		try:
			doc = frappe.get_doc("Bulk Leave Encashment", self.bulk_leave_encashment)
			doc.tds_receipt_number = receipt_number
			doc.tds_receipt_date = receipt_date
			doc.save(ignore_permissions=True)
			frappe.msgprint(
				f"TDS receipt details updated for Bulk Leave Encashment: {doc.name}",
				alert=True
			)
		except frappe.DoesNotExistError:
			frappe.throw(f"Bulk Leave Encashment document {self.bulk_leave_encashment} does not exist.")
		except Exception as e:
			frappe.log_error(
				title="Error Updating Bulk Leave Encashment",
				message=f"Error updating TDS receipt details for Bulk Leave Encashment {self.bulk_leave_encashment}: {str(e)}"
			)
			frappe.throw("An error occurred while updating the Bulk Leave Encashment. Please check the error log.")

	def update_mr_invoice_entry_items(self, cancel):
		if not self.employees:
			frappe.throw("No MR employees found to update TDS receipt numbers.")

		if cancel:
			message = "TDS receipt cancelled for MR employees."
		else:
			message = "TDS receipt processed successfully for MR employees."

		frappe.msgprint(_(message), alert=True)

		# Log the transaction for tracking
		frappe.log_error(
			title="MR TDS Receipt Update",
			message=f"TDS Receipt {self.name} processed for {len(self.employees)} MR employees. Receipt Number: {self.tds_receipt_number if not cancel else 'Cancelled'}"
		)

	def check_duplicate_entries(self):
		if self.purpose in ["PBVA", "Bonus"]:
			filters = {"purpose": self.purpose, "fiscal_year": self.fiscal_year}

			for t in frappe.db.get_all("TDS Receipt Entry", filters, "tds_receipt_update"):
				frappe.throw(_("Receipt details for <b>{}</b> already updated via {}")\
					.format(self.purpose, frappe.get_desk_link("TDS Receipt Update", t.tds_receipt_update)))
		else:
			for t in frappe.db.sql("""select t1.tds_receipt_update, t1.invoice_type, t1.invoice_no 
					from `tabTDS Receipt Entry` t1
					where exists(select 1
						from `tabTDS Remittance Item` t2
						where t2.parent = "{parent}"
						and t2.invoice_type = t1.invoice_type
						and t2.invoice_no = t1.invoice_no)
				""".format(parent=self.name), as_dict=True):
				frappe.throw(_("Receipt details for {} already updated via {}")\
					.format(frappe.get_desk_link(t.invoice_type, t.invoice_no), frappe.get_desk_link("TDS Receipt Update", t.tds_receipt_update)))

	def calculate_total(self):
		total_bill_amount = total_tds_amount = 0
		if self.purpose == "Bulk Leave Encashment":
			doc = frappe.get_doc("Bulk Leave Encashment", self.bulk_leave_encashment)
			total_bill_amount = sum(d.encashment_amount for d in doc.get("items"))
			total_tds_amount = sum(d.encashment_tax for d in doc.get("items"))
		else:
			for a in self.items:
				total_bill_amount += flt(a.bill_amount)
				total_tds_amount += flt(a.tds_amount)
		self.total_bill_amount = total_bill_amount
		self.total_tax_amount = total_tds_amount

	def get_entries(self):
		entries = []
		if self.purpose in ["PBVA", "Bonus"]:
			name = make_autoname('TDSRE.YYYY.MM.#######')
			entries.append((name, str(today()), self.branch, self.cost_center,
				self.purpose, self.fiscal_year, self.month or "", self.pbva or "" if self.purpose == "PBVA" else "", "",
				"", "", "",
				self.tds_receipt_date, self.tds_receipt_number, self.cheque_no, self.cheque_date,
				self.name, "", 0, 0, frappe.session.user, str(get_datetime()), str(get_datetime()), frappe.session.user))
		else:
			for d in self.items:
				name = make_autoname('TDSRE.YYYY.MM.#######')
				bill_no = None
				if d.invoice_type == "Leave Encashment":
					employee, employee_name = frappe.db.get_value("Leave Encashment", d.invoice_no, ["muster roll employee", "person_name"])
					bill_no = str(employee_name + "(" + d.invoice_no + ")")
				else:
					bill_no = d.invoice_no
				if d.tds_remittance == None:
					d.tds_remittance = ''
				entries.append((name, d.posting_date, self.branch, self.cost_center,
					self.purpose, self.fiscal_year or "", self.month or "", "", self.region or "",
					d.invoice_type, d.invoice_no, bill_no,
					self.tds_receipt_date, self.tds_receipt_number, self.cheque_no, self.cheque_date,
					self.name, d.tds_remittance, 0, 0, frappe.session.user, str(get_datetime()), str(get_datetime()), frappe.session.user))
		return entries

	def make_tds_receipt_entries(self):
		entries = self.get_entries()
		if len(entries):
			entries = ', '.join(map(str, entries))
			frappe.db.sql("""INSERT INTO `tabTDS Receipt Entry`(name, posting_date, branch, cost_center, 
				purpose, fiscal_year, month, pbva, region,  
				invoice_type, invoice_no, bill_no, 
				receipt_date, receipt_number, cheque_no, cheque_date, 
				tds_receipt_update, tds_remittance, idx, docstatus, owner, creation, modified, modified_by)
				VALUES {}""".format(entries))

	def validate_filters(self):
		if self.purpose in ("Employee Salary", "PBVA", "Bonus"):
			if not self.fiscal_year:
				frappe.throw("<b>Fiscal Year</b> is mandatory")
			elif self.purpose == "Employee Salary":
				if not self.month:
					frappe.throw("<b>Month</b> is mandatory")
				if not self.branch:
					frappe.throw("<b>Branch</b> is mandatory for MR employees")
		else:
			if not self.branch:
				frappe.throw("Branch is required")

	@frappe.whitelist()
	def get_invoices(self):
		cond = accounts_cond = ""
		total_bill_amount = total_tds_amount = 0
		entries = []
		self.set('items', [])

		accounts = [i.account for i in frappe.db.get_all("Tax Withholding Account", \
			{"parent": self.tax_withholding_category}, "account")]

		if not len(accounts) and self.purpose != "Leave Encashment":
			return total_tds_amount, total_bill_amount
		elif len(accounts) == 1:
			accounts_cond = 'and t1.tax_account = "{}"'.format(accounts[0])
		else:
			accounts_cond = 'and t1.tax_account in ({})'.format('"' + '","'.join(accounts) + '"')

		if self.purpose in ["Leave Encashment", "Other Invoice", "Overtime"]:
			if self.purpose == 'Leave Encashment':
				query = """
					SELECT 
						"Leave Encashment" as invoice_type, 
						name as invoice_no, 
						encashment_date as posting_date, 
						encashment_amount as bill_amount,
						cost_center, 
						encashment_tax as tds_amount, 
						employee as party,
						'Employee' as party_type,
						employee_name as party_name
					FROM `tabLeave Encashment` AS t 
						WHERE t.docstatus = 1 
						AND t.encashment_date BETWEEN '{0}' AND '{1}' 
						AND t.encashment_tax > 0 
						AND NOT EXISTS (SELECT 1 
					FROM `tabTDS Receipt Entry` AS b 
						WHERE b.invoice_no = t.name)
						""".format(self.from_date, self.to_date)
				query += """
					UNION SELECT 
						"Employee Benefit Claim" as invoice_type, 
						t.name as invoice_no, 
						t.posting_date, 
						t1.amount as bill_amount,
						t.cost_center as cost_center, 
						t1.tax_amount as tds_amount, 
						t.employee as party, 
						'Employee' as party_type,
						t.employee_name as party_name
					FROM `tabEmployee Benefit Claim` AS t, `tabSeparation Item` t1 
						WHERE t.docstatus = 1 
						AND t1.parent = t.name
						AND t.posting_date BETWEEN '{0}' 
						AND '{1}'
						AND t1.tax_amount > 0
						AND NOT EXISTS (SELECT 1 
					FROM `tabTDS Receipt Entry` AS b 
						WHERE b.invoice_no = t.name)
						""".format(self.from_date, self.to_date)
				entries = frappe.db.sql(query, as_dict=1)
			else:
				if not self.branch:
					frappe.throw("Branch is required")
				entries = frappe.db.sql("""SELECT posting_date, party_type, party, invoice_type, invoice_no, bill_amount, 
						tax_account, tds_amount, party_name, tpn, cost_center, business_activity, parent as tds_remittance
					FROM `tabTDS Remittance Item` t1
					WHERE t1.posting_date BETWEEN '{from_date}' AND '{to_date}'
					AND t1.docstatus = 1
					{accounts_cond}
					AND t1.cost_center = '{cost_center}'
					AND t1.parenttype = 'TDS Remittance'
					AND NOT EXISTS(SELECT 1
						FROM `tabTDS Receipt Entry` t2
						WHERE t2.invoice_no = t1.invoice_no)
					AND NOT EXISTS(SELECT 1
						FROM `tabTDS Remittance Item` t3
						WHERE t3.invoice_no = t1.invoice_no
						AND t3.parenttype = 'TDS Receipt Update'
						AND t3.parent != "{name}"
						AND t3.docstatus != 2)
				""".format(name=self.name, accounts_cond=accounts_cond, cost_center=self.cost_center,\
					from_date=self.from_date, to_date=self.to_date), as_dict=True)

			if not len(entries):
				frappe.msgprint(_("No Records Found"))

			for d in entries:
				row = self.append('items', {})
				if self.purpose == "Leave Encashment":
					d.tpn = frappe.db.get_value("Employee", d.party, "tpn_number")
				d.bill_amount = flt(d.bill_amount, 2)
				d.tds_amount = flt(d.tds_amount, 2)
				row.update(d)
				total_bill_amount += flt(d.bill_amount)
				total_tds_amount += flt(d.tds_amount)

		return total_bill_amount, total_tds_amount

	# =========================================================================
	# JOURNAL ENTRY METHODS
	# =========================================================================

	def post_journal_entry(self):
		"""
		Create Journal Entry for TDS Receipt (Draft Status)
		Debit: Bank Account (total_salary_tax)
		Credit: Tax Payable Account (total_salary_tax)
		Party: Supplier - RRCO
		"""
		# Check if journal entry already exists
		if self.journal_entry:
			frappe.msgprint(
				_("Journal Entry already exists: {0}").format(self.journal_entry),
				alert=True
			)
			return

		# Get accounts
		debit_account = self.get_debit_account()
		credit_account = self.get_credit_account()

		if not debit_account or not credit_account:
			frappe.throw(_("Please configure Debit and Credit accounts in the system"))

		# Validate accounts exist
		if not frappe.db.exists("Account", debit_account):
			frappe.throw(_("Debit Account {0} does not exist").format(debit_account))
		if not frappe.db.exists("Account", credit_account):
			frappe.throw(_("Credit Account {0} does not exist").format(credit_account))

		# Determine journal amount based on purpose
		if self.purpose == "Employee Salary":
			journal_amount = flt(self.total_salary_tax)
		else:
			journal_amount = flt(self.total_tax_amount)

		# Skip if amount is zero
		if journal_amount <= 0:
			frappe.msgprint(_("Amount is zero. No journal entry created."), alert=True)
			return

		# Get branch
		branch = self.branch or frappe.db.get_value("Company", self.company, "default_branch")
		if not branch:
			branch = frappe.db.get_value("Branch", {"company": self.company}, "name")

		# Get cost center
		cost_center = self.cost_center or frappe.db.get_value("Company", self.company, "cost_center")

		# Build remarks
		remarks = _("TDS Receipt - {0} - {1}").format(self.purpose, self.name)

		# Create Journal Entry document
		je = frappe.new_doc("Journal Entry")
		je.flags.ignore_permissions = 1
		je.update({
			"doctype": "Journal Entry",
			"voucher_type": "Journal Entry",
			"naming_series": "Journal Voucher",
			"title": _("TDS Receipt - {0}").format(self.name),
			"user_remark": remarks,
			"posting_date": self.tds_receipt_date or self.posting_date or today(),
			"company": self.company,
			"branch": branch,
			"cheque_no": self.cheque_no or "",
			"cheque_date": self.cheque_date or None,
		})

		# Debit row - Bank Account (Debited)
		je.append("accounts", {
			"account": debit_account,
			"debit_in_account_currency": journal_amount,
			"debit": journal_amount,
			"cost_center": cost_center,
			"reference_type": self.doctype,
			"reference_name": self.name,
		})

		# Credit row - Tax Payable Account (Credited)
		# Party: Supplier - RRCO
		je.append("accounts", {
			"account": credit_account,
			"credit_in_account_currency": journal_amount,
			"credit": journal_amount,
			"cost_center": cost_center,
			"party_type": "Supplier",
			"party": "RRCO",
			"reference_type": self.doctype,
			"reference_name": self.name,
		})

		# Insert the journal entry (Draft status)
		je.insert()

		# Update the TDS Receipt Update document with the journal entry reference
		self.db_set("journal_entry", je.name)
		self.db_set("journal_entry_status", "Draft")

		frappe.msgprint(
			_("Journal Entry {0} created in Draft status. Amount: {1}").format(
				frappe.bold(je.name), frappe.bold(journal_amount)
			),
			indicator='orange',
			alert=True
		)

		return je

	def cancel_journal_entry(self):
		"""Cancel or delete the associated Journal Entry"""
		if not self.journal_entry:
			return

		try:
			je = frappe.get_doc("Journal Entry", self.journal_entry)
			if je.docstatus == 1:
				# If submitted, cancel it
				je.cancel()
				self.db_set("journal_entry_status", "Cancelled")
				frappe.msgprint(
					_("Journal Entry {0} cancelled successfully").format(frappe.bold(je.name)),
					alert=True
				)
			elif je.docstatus == 0:
				# If in draft, just delete it
				je.delete()
				self.db_set("journal_entry", None)
				self.db_set("journal_entry_status", None)
				frappe.msgprint(
					_("Draft Journal Entry {0} deleted").format(frappe.bold(je.name)),
					alert=True
				)
			else:
				frappe.msgprint(
					_("Journal Entry {0} is already cancelled").format(frappe.bold(je.name)),
					alert=True
				)

		except Exception as e:
			frappe.log_error(
				title="TDS Receipt Update - Journal Entry Cancel Error",
				message=f"Error cancelling journal entry {self.journal_entry}: {str(e)}"
			)
			frappe.throw(_("Failed to cancel Journal Entry: {0}").format(str(e)))

	def get_debit_account(self):
		"""
		Get the debit account (Bank Account)
		This account will be DEBITED with the TDS amount
		"""
		# Option 1: From Company settings
		company = frappe.get_doc("Company", self.company)
		if company.default_bank_account:
			return company.default_bank_account

		# Option 2: From custom TDS Settings
		# tds_settings = frappe.get_single("TDS Settings")
		# if tds_settings.default_debit_account:
		#     return tds_settings.default_debit_account

		# Option 3: Hardcoded fallback (not recommended for production)
		return "11.2.001 - BOB - 100896320 - CD"

	def get_credit_account(self):
		"""
		Get the credit account (Tax Payable account)
		This account will be CREDITED with the TDS amount
		"""
		# Option 1: From Tax Withholding Category
		if self.tax_withholding_category:
			tds_category = frappe.get_doc("Tax Withholding Category", self.tax_withholding_category)
			if tds_category.default_payable_account:
				return tds_category.default_payable_account

		# Option 2: From custom TDS Settings
		# tds_settings = frappe.get_single("TDS Settings")
		# if tds_settings.default_credit_account:
		#     return tds_settings.default_credit_account

		# Option 3: Hardcoded fallback (not recommended for production)
		return "21.380 - Tax Payable to RRCO"

	@frappe.whitelist()
	def submit_journal_entry(self):
		"""Submit the associated Journal Entry (Button Action)"""
		# If no journal entry exists, create one first
		if not self.journal_entry:
			self.post_journal_entry()
			# Reload to get the updated journal_entry value
			self.reload()

		if not self.journal_entry:
			frappe.throw(_("No Journal Entry found to submit"))

		try:
			je = frappe.get_doc("Journal Entry", self.journal_entry)
			if je.docstatus == 0:
				je.submit()
				self.db_set("journal_entry_status", "Submitted")
				frappe.msgprint(
					_("Journal Entry {0} submitted successfully").format(frappe.bold(je.name)),
					indicator='green',
					alert=True
				)
			elif je.docstatus == 1:
				frappe.msgprint(
					_("Journal Entry {0} is already submitted").format(frappe.bold(je.name)),
					indicator='blue',
					alert=True
				)
			else:
				frappe.msgprint(
					_("Journal Entry {0} is cancelled").format(frappe.bold(je.name)),
					indicator='red',
					alert=True
				)
		except Exception as e:
			frappe.log_error(
				title="TDS Receipt Update - Submit Journal Entry Error",
				message=f"Error submitting journal entry {self.journal_entry}: {str(e)}"
			)
			frappe.throw(_("Failed to submit Journal Entry: {0}").format(str(e)))

	@frappe.whitelist()
	def create_and_submit_journal_entry(self):
		"""Create and immediately submit the Journal Entry"""
		try:
			# Create the journal entry
			self.post_journal_entry()
			# Reload to get the updated journal_entry value
			self.reload()

			if not self.journal_entry:
				frappe.throw(_("Failed to create Journal Entry"))

			# Submit the journal entry
			je = frappe.get_doc("Journal Entry", self.journal_entry)
			je.submit()

			self.db_set("journal_entry_status", "Submitted")

			frappe.msgprint(
				_("Journal Entry {0} created and submitted successfully").format(
					frappe.bold(je.name)
				),
				indicator='green',
				alert=True
			)

		except Exception as e:
			frappe.log_error(
				title="TDS Receipt Update - Create and Submit Journal Entry Error",
				message=f"Error: {str(e)}"
			)
			frappe.throw(_("Failed to create and submit Journal Entry: {0}").format(str(e)))


@frappe.whitelist()
def apply_pbva_filter(doctype, txt, searchfield, start, page_len, filters):
	return frappe.db.sql('''
		SELECT name
		FROM `tabPBVA` a
		WHERE docstatus = 1
		AND NOT EXISTS(select 1 from `tabRRCO Receipt Entry` where pbva = a.name)
		AND	(`{key}` LIKE %(txt)s OR name LIKE %(txt)s)
		LIMIT %(start)s, %(page_len)s
	'''.format(key=searchfield), {
		'txt': '%' + txt + '%',
		'start': start, 'page_len': page_len
	})


def get_permission_query_conditions(user):
	if not user:
		user = frappe.session.user
	user_roles = frappe.get_roles(user)

	if user == "Administrator" or "System Manager" in user_roles or "Accounts User" in user_roles:
		return

	return """(
		exists(select 1
			from `tabEmployee` as e
			where e.branch = `tabTDS Receipt Update`.branch
			and e.user_id = '{user}')
		or
		exists(select 1
			from `tabEmployee` e, `tabAssign Branch` ab, `tabBranch Item` bi
			where e.user_id = '{user}'
			and ab.employee = e.name
			and bi.parent = ab.name
			and bi.branch = `tabTDS Receipt Update`.branch)
	)""".format(user=user)