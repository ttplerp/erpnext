# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import cint, flt, today, get_datetime
from frappe.model.document import Document
from frappe.model.naming import make_autoname

class TDSReceiptUpdate(Document):
	def validate(self):
		self.validate_filters()
		self.validate_employees()
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

	def on_cancel(self):
		if self.purpose in ("Employee Salary", "Bulk Leave Encashment"):
			self.update_tds_receipt_number(cancel=True)
		else:
			frappe.db.sql("delete from `tabTDS Receipt Entry` where tds_receipt_update = '{}'".format(self.name))

	def validate_employees(self):
		if not self.employees:
			return
		self.number_of_employees = len(self.employees)
		
		total_salary_tax = total_health_contribution = gross_salary = 0.0

		for sd in self.employees:
			salary_tax = health_contribution = 0.0
			doc = frappe.get_doc("Salary Slip", sd.salary_slip)
			
			for detail in doc.get("earnings") + doc.get("deductions"):
				if detail.salary_component in ["Salary Tax", "Health Contribution"]:
					if detail.salary_component == "Salary Tax":
						salary_tax += flt(detail.amount)
						total_salary_tax += flt(detail.amount)
					elif detail.salary_component == "Health Contribution":
						health_contribution += flt(detail.amount)
						total_health_contribution += flt(detail.amount)
			
			sd.salary_tax = flt(salary_tax)
			sd.health_contribution = flt(health_contribution)
			sd.gross_salary = flt(doc.gross_pay)
			gross_salary += flt(doc.gross_pay)

		self.total_gross_salary = gross_salary
		self.total_salary_tax = total_salary_tax
		self.total_health_contribution = total_health_contribution

	def make_filters(self):
		filters = frappe._dict(
			company=self.company,
			fiscal_year=self.fiscal_year,
			month=self.month
		)
		return filters
	
	def update_tds_receipt_number(self, cancel=False):
		if self.purpose == "Employee Salary":
			self.update_salary_slip(cancel)
		elif self.purpose == "Bulk Leave Encashment":
			self.update_bulk_leave_encashment(cancel)

	@frappe.whitelist()
	def fill_employee_details(self):
		filters = self.make_filters()
		employees = get_employee_list(filters=filters, as_dict=True)
		self.set("employees", [])

		if not employees:
			error_msg = _(
				"No employees found for the mentioned criteria:<br>Company: {0}"
			).format(
				frappe.bold(self.company),
			)
			if self.fiscal_year:
				error_msg += "<br>" + _("Fiscal Year: {0}").format(frappe.bold(self.fiscal_year))
			if self.month:
				error_msg += "<br>" + _("Month: {0}").format(frappe.bold(self.month))
			frappe.throw(error_msg, title=_("No employees found"))

		self.set("employees", employees)
		self.number_of_employees = len(self.employees)

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
			doc.tds_receipt_date = receipt_date  # Corrected assignment here
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

	def update_salary_slip(self, cancel):
		if not self.employees:
			frappe.throw("No employees found to update TDS receipt numbers.")
		if cancel:
			receipt_number = None
			receipt_date = None
		else:
			receipt_number = self.tds_receipt_number
			receipt_date = self.tds_receipt_date
		
		updates = []
		for emp in self.get("employees"):
			if emp.salary_slip:
				updates.append({
					"name": emp.salary_slip,
					"tds_receipt_number": receipt_number,
					"tds_receipt_date": receipt_date,
				})
		
		if updates:
			try:
				for update in updates:
					frappe.db.set_value(
						"Salary Slip",
						update["name"],
						{
							"tds_receipt_number": update["tds_receipt_number"],
							"tds_receipt_date": update["tds_receipt_date"],
						},
					)
				frappe.msgprint("TDS receipt numbers have been successfully updated.", alert=True)
			except Exception as e:
				frappe.log_error(
					title="Error Updating TDS Receipt Numbers",
					message=f"An error occurred while updating TDS receipt numbers: {str(e)}"
				)
				frappe.throw("An error occurred while updating TDS receipt numbers. Please check the error log.")
		else:
			frappe.throw("No valid Salary Slips found to update.")

	def check_duplicate_entries(self):
		if self.purpose in ["PBVA","Bonus"]:
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
				total_bill_amount 	+= flt(a.bill_amount)
				total_tds_amount 	+= flt(a.tds_amount)
		self.total_bill_amount 	= total_bill_amount
		self.total_tax_amount 	= total_tds_amount

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
					employee, employee_name = frappe.db.get_value("Leave Encashment", d.invoice_no, ["employee","employee_name"])
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
			query = """INSERT INTO `tabTDS Receipt Entry`(name, posting_date, branch, cost_center, 
				purpose, fiscal_year, month, pbva, region,  
				invoice_type, invoice_no, bill_no,
				receipt_date, receipt_number, cheque_no, cheque_date, 
				tds_receipt_update, tds_remittance, idx, docstatus, owner, creation, modified, modified_by)
				VALUES {}""".format(entries)
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
			elif self.purpose == "Employee Salary" and not self.month:
				frappe.throw("<b>Month</b> is mandatory")

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
				entries = frappe.db.sql(query,as_dict=1)
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
				""".format(name = self.name, accounts_cond = accounts_cond, cost_center= self.cost_center,\
					from_date = self.from_date, to_date = self.to_date),as_dict=True)

			if not len(entries):
				frappe.msgprint(_("No Records Found"))

			for d in entries:
				row = self.append('items', {})
				if self.purpose == "Leave Encashment":
					d.tpn = frappe.db.get_value("Employee", d.party, "tpn_number")
				d.bill_amount = flt(d.bill_amount, 2)
				d.tds_amount = flt(d.tds_amount, 2)
				row.update(d)
				total_bill_amount 	+= flt(d.bill_amount)
				total_tds_amount 	+= flt(d.tds_amount)

		return total_bill_amount, total_tds_amount

@frappe.whitelist()
def apply_pbva_filter(doctype, txt, searchfield, start, page_len, filters):
	return frappe.db.sql('''
		SELECT name
		FROM `tabPBVA` a
		WHERE docstatus = 1
		AND NOT EXISTS(select 1 from `tabRRCO Receipt Entry` where pbva = a.name)
		AND	(`{key}` LIKE %(txt)s OR name LIKE %(txt)s)
		LIMIT %(start)s, %(page_len)s
	'''.format(key=searchfield),{
		'txt': '%' + txt + '%',
		'start': start, 'page_len': page_len
	})

def get_employee_list(
	filters,
	as_dict=True,
) -> list:
	SalarySlip = frappe.qb.DocType("Salary Slip")
	Employee = frappe.qb.DocType("Employee")
	query = (
		frappe.qb.from_(Employee)
		.join(SalarySlip)
		.on(Employee.name == SalarySlip.employee)
		.where(
			(SalarySlip.docstatus == 1)
			& (SalarySlip.company == filters.company)
			& (SalarySlip.fiscal_year == filters.fiscal_year)
			& (SalarySlip.month == filters.month)
			& ((SalarySlip.tds_receipt_number == None) | (SalarySlip.tds_receipt_number.isnull()))
		)
		.select(
			Employee.name.as_("employee"),
			Employee.employee_name,
			SalarySlip.designation,
			SalarySlip.branch,
			SalarySlip.name.as_("salary_slip")
		)
	)
	return query.run(as_dict=as_dict)

def get_permission_query_conditions(user):
	if not user: user = frappe.session.user
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