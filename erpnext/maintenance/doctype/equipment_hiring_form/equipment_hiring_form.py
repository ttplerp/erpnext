# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cstr, flt, fmt_money, formatdate, getdate, get_datetime
from frappe.desk.reportview import get_match_cond
from erpnext.custom_utils import check_uncancelled_linked_doc, check_future_date

class EquipmentHiringForm(Document):
	def validate(self):
		self.validate_date()
		self.validate_amount()
		self.validate_supplier()
		#self.fetch_reading()

	def validate_date(self):
		if self.start_date > self.end_date:
			frappe.throw("Start Date cannot be greater than End Date")

	def validate_amount(self):
		if not self.rate > 0:
			frappe.throw("Hiring Rate should be greater than zero")
	
	def validate_supplier(self):
		if not self.supplier:
			frappe.throw("Setup supplier in Equipment Master")

	def fetch_reading(self):
		self.reading_based_on = frappe.db.get_value("Equipment Model", self.equipment_model, "reading_based_on")
		if not self.reading_based_on:
			frappe.throw("Set Reading Based On in Equipment Model")	


"""		check_future_date(self.request_date)
		self.check_date_approval()
		self.check_duplicate()
		self.calculate_totals()
		self.validate_advance_balance()

	def validate_advance_balance(self):
		if len(self.balance_advance_details) < 1:
			query = "select count(*) as count from `tabJournal Entry` as e inner join \
				`tabJournal Entry Account` as ea on e.name = ea.parent inner join \
				`tabEquipment Hiring Form` as eq on ea.reference_name = eq.name where \
				e.branch = \'" + str(self.branch) + "\' and ea.party = \'" + str(self.customer) + "\' \
				and eq.payment_completed = 1 and eq.docstatus= 1"
			dtl = frappe.db.sql(query, as_dict=True)
			if dtl[0]['count'] > 0:
				frappe.throw("There are previous advance balance. Please fetch those advances");

	def validate_date(self, a):
		from_date = get_datetime(str(a.from_date) + ' ' + str(a.from_time))
		to_date = get_datetime(str(a.to_date) + ' ' + str(a.to_time))
		if to_date < from_date:
			frappe.throw("From Date/Time cannot be greater than To Date/Time")

	def before_submit(self):
		if self.private == "Private" and self.advance_amount <= 0:
			frappe.throw("For Private Customers, Advance Amount is Required!")

		if not self.approved_items:
			frappe.throw("Cannot submit hiring form without Approved Items")

		self.check_equipment_free()

	def on_submit(self):
		self.assign_hire_form_to_equipment()
		if self.advance_amount > 0:
			self.post_journal_entry()
		self.update_equipment_request(1)
		self.update_journal()

	def before_cancel(self):		
		check_uncancelled_linked_doc(self.doctype, self.name)
		cl_status = frappe.db.get_value("Journal Entry", self.advance_journal, "docstatus")
		if cl_status and cl_status != 2:
			frappe.throw("You need to cancel the journal entry related to this job card first!")
	
		frappe.db.sql("delete from `tabEquipment Reservation Entry` where ehf_name = \'"+ str(self.name) +"\'")	
		self.db_set("advance_journal", '')
		for a in self.balance_advance_details:
			frappe.db.sql("UPDATE `tabJournal Entry Account` SET `reference_name` = \'" + str(a.reference_name) + "\' WHERE name = \'" + str(a.reference_row) + "\'")


	def on_cancel(self):
		self.update_equipment_request(0)
	
	def update_journal(self):
		for a in self.balance_advance_details:
			frappe.db.sql("UPDATE `tabJournal Entry Account` SET `reference_name` = \'" + str(self.name) + "\' WHERE name = \'" + str(a.reference_row) + "\'")


	def update_equipment_request(self, status):
		total_percent = 0
		er = None
		for a in self.approved_items:
			if a.request_reference:
				doc = frappe.get_doc("Equipment Request Item", a.request_reference)
				doc.db_set("approved", status)
				total_percent = flt(total_percent) + flt(doc.percent_share)
				if a.equipment_request:
					er = a.equipment_request
		if er:
			er = frappe.get_doc("Equipment Request", er)
			if status:
				total = flt(total_percent) + flt(er.percent_completed)
			else:
				total = flt(er.percent_completed) - flt(total_percent) 
			er.db_set("percent_completed", round(total))

	def check_date_approval(self):
		for a in self.approved_items:
			self.validate_date(a)

	def check_duplicate(self):
		for a in self.approved_items:
			for b in self.approved_items:
				if a.equipment == b.equipment and a.idx != b.idx:
					frappe.throw("Duplicate entries for equipments in row " + str(a.idx) + " and " + str(b.idx))

	def calculate_totals(self):
		if self.approved_items:
			total = 0
			for a in self.approved_items:
				total += flt(a.grand_total)
			self.total_hiring_amount = total
			if self.private == "Private" and not self.advance_amount:
				self.advance_amount = total
		

	def assign_hire_form_to_equipment(self):
		for a in self.approved_items:
			doc = frappe.new_doc("Equipment Reservation Entry")
			doc.flags.ignore_permissions = 1 
			doc.equipment = a.equipment
			doc.reason = "Hire"
			doc.ehf_name = self.name
			doc.place = a.place
			doc.from_date = a.from_date
			doc.to_date = a.to_date
			doc.hours = a.total_hours
			doc.to_time = a.to_time
			doc.from_time = a.from_time
			doc.submit()

	def check_equipment_free(self):
		for a in self.approved_items:
			ec = frappe.db.get_value("Equipment Category", frappe.db.get_value("Equipment", a.equipment, "equipment_category"), "allow_hire")
			if ec:
				pass
			else:
                                '''
				result = frappe.db.sql("select ehf_name from `tabEquipment Reservation Entry` where equipment = \'" + str(a.equipment) + "\' and docstatus = 1 and (\'" + str(a.from_date) + "\' between from_date and to_date OR \'" + str(a.to_date) + "\' between from_date and to_date)", as_dict=True)
				if result:
					if a.from_time and a.to_time:
						res = frappe.db.sql("select name from `tabEquipment Reservation Entry` where docstatus = 1 and equipment = %s and ( %s between to_time and from_time or %s between to_time and from_time )", (str(a.equipment), str(a.from_time), str(a.to_time)))
						if res:
							frappe.throw("The equipment " + str(a.equipment) + " is already in use from by " + str(result[0].ehf_name))
				'''
				from_datetime = str(get_datetime(str(a.from_date) + ' ' + str(a.from_time)))
                                to_datetime = str(get_datetime(str(a.to_date) + ' ' + str(a.to_time)))

                                result = frappe.db.sql("""
"""                                        select ehf_name
                                        from `tabEquipment Reservation Entry`
                                        where equipment = '{0}'
                                        and docstatus = 1
                                        and ('{1}' between concat(from_date,' ',from_time) and concat(to_date,' ',to_time)
                                                or
                                                '{2}' between concat(from_date,' ',from_time) and concat(to_date,' ',to_time)
                                                or
                                                ('{3}' <= concat(from_date,' ',from_time) and '{4}' >= concat(to_date,' ',to_time))
                                        )
"""                                """.format(a.equipment, from_datetime, to_datetime, from_datetime, to_datetime), as_dict=True)

				for r in result:
                                        frappe.throw(_("The equipment {0} is already in use from by {1}").format(a.equipment, r.ehf_name))
		
	##
	# make necessary journal entry
	##
	def post_journal_entry(self):
		advance_account = frappe.db.get_single_value("Maintenance Accounts Settings", "default_advance_account")
		revenue_bank = frappe.db.get_value("Branch", self.branch, "revenue_bank_account")

		if revenue_bank and advance_account:
			je = frappe.new_doc("Journal Entry")
			je.flags.ignore_permissions = 1 
			je.title = "Advance for Equipment Hire (" + self.name + ")"
			je.voucher_type = 'Bank Entry'
			je.naming_series = 'Bank Receipt Voucher'
			je.remark = 'Advance payment against : ' + self.name;
			je.posting_date = frappe.utils.nowdate()
			je.branch = self.branch

			je.append("accounts", {
					"account": advance_account,
					"party_type": "Customer",
					"party": self.customer,
					"reference_type": "Equipment Hiring Form",
					"reference_name": self.name,
					"cost_center": self.cost_center,
					"credit_in_account_currency": flt(self.advance_amount),
					"credit": flt(self.advance_amount),
					"is_advance": 'Yes'
				})

			je.append("accounts", {
					"account": revenue_bank,
					"cost_center": self.cost_center,
					"debit_in_account_currency": flt(self.advance_amount),
					"debit": flt(self.advance_amount),
				})
			je.insert()
			self.db_set("advance_journal", je.name)

@frappe.whitelist()
def get_hire_rates(e, from_date):
	e = frappe.get_doc("Equipment", e)
	#query = "select with_fuel, without_fuel, idle from `tabHire Charge Parameter` where equipment_type = \"" + str(e.equipment_type) + "\" and equipment_model =\"" + str(e.equipment_model) + "\""
	db_query = "select a.rate_fuel as with_fuel, a.rate_wofuel as without_fuel, a.idle_rate as idle, a.cft_rate_bf, a.cft_rate_co from `tabHire Charge Item` a, `tabHire Charge Parameter` b where a.parent = b.name and b.equipment_type = '{0}' and b.equipment_model = '{1}' and '{2}' between a.from_date and ifnull(a.to_date, now()) LIMIT 1"

	data = frappe.db.sql(db_query.format(e.equipment_type, e.equipment_model, from_date), as_dict=True)
	#data = frappe.db.sql(query, as_dict=True)
	if not data:
                frappe.throw(_("No Hire Rates has been assigned for equipment type {0} and model {1}").format(e.equipment_type, e.equipment_model), title="No Data Found!")
	return data	

@frappe.whitelist()
def get_diff_hire_rates(tr):
	query = "select with_fuel, without_fuel, idle_rate as idle, cft_rate_bf, cft_rate_co from `tabTender Hire Rate` where name = \"" + str(tr) + "\""
	data = frappe.db.sql(query, as_dict=True)
	if not data:
		frappe.throw("No Hire Rates has been assigned")
	return data	

@frappe.whitelist()
def get_rates(form, equipment):
	if form and equipment:
		return frappe.db.sql("select rate_type, rate, idle_rate, from_date, to_date, from_time, to_time, tender_hire_rate from `tabHiring Approval Details` where docstatus = 1 and parent = \'" + str(form) + "\' and equipment = \'" + str(equipment) + "\'", as_dict=True)

@frappe.whitelist()
def update_status(name):
	so = frappe.get_doc("Equipment Hiring Form", name)
	so.db_set("payment_completed", 1)

def equipment_query(doctype, txt, searchfield, start, page_len, filters):
        # Shiv, 20/12/2017
        # Following code temporarily replaced by the subsequent as per Payma's request for doing backlog entries, 20/12/2017
        # Needs to be set back later
        '''
	return frappe.db.sql("""
"""                        select
                                e.name,
                                e.equipment_type,
                                e.equipment_number
                        from `tabEquipment` e
                        where e.equipment_type = %s
                        and e.branch = %s
                        and e.is_disabled != 1
                        and e.not_cdcl = 0
                        and not exists (select 1
                                        from `tabEquipment Reservation Entry` a
                                        where (
                                                a.from_date != a.to_date
                                                and
                                                (a.from_date between %s and %s or a.to_date between %s and %s)
                                                )
                                        and a.equipment = e.name)
"""                        """, (filters['equipment_type'], filters['branch'], filters['from_date'], filters['to_date'], filters['from_date'], filters['to_date']))
        '''
        
        return frappe.db.sql("""
"""                        select
                                e.name,
                                e.equipment_type,
                                e.equipment_number
                        from `tabEquipment` e
                        where e.equipment_type = %(equipment_type)s
                        and e.branch = %(branch)s
                        and e.is_disabled != 1
                        and e.not_cdcl = 0
                        and (
                                {key} like %(txt)s
                                or
                                equipment_type like %(txt)s
                                or
                                equipment_number like %(txt)s
                        )
                        {mcond}
                        order by
                                if(locate(%(_txt)s, name), locate(%(_txt)s, name), 99999),
                                if(locate(%(_txt)s, equipment_type), locate(%(_txt)s, equipment_type), 99999),
                                if(locate(%(_txt)s, equipment_number), locate(%(_txt)s, equipment_number), 99999),
                                idx desc,
                                name, equipment_type, equipment_number
                        limit %(start)s, %(page_len)s
"""                        """.format(**{
                                'key': searchfield,
                                'mcond': get_match_cond(doctype)
                        }),
                        {
				"txt": "%%%s%%" % txt,
				"_txt": txt.replace("%", ""),
				"start": start,
				"page_len": page_len,
                                "equipment_type": filters['equipment_type'],
                                "branch": filters['branch']
			})

@frappe.whitelist()        
def get_advance_balance(branch, customer):	
	if branch and customer:
		data = []
		query = "select e.name as journal, a.name as name, a.credit as amount, a.party as party, \
		a.reference_type as ref_type, \
			a.reference_name as ref_name, a.cost_center as cc, e.posting_date as \
			posting_date from `tabJournal Entry` as e, `tabJournal Entry Account` as a \
			where e.name = a.parent and e.branch = \'" + str(branch) + "\' and e.docstatus = '1' and a.party = \'" + str(customer) + "\' \
			and a.reference_type='Equipment Hiring Form'"
		for a in frappe.db.sql(query, as_dict=True):
			# frappe.throw(_(" Test : {0}".format(a.amount)))
			# row = [a.name, a.amount, a.party, a.ref_type, a.ref_name, a.cc]
			ehform = frappe.db.sql("SELECT docstatus, payment_completed FROM `tabEquipment Hiring Form` \
				WHERE name = \'"+ str(a.ref_name) +"\'", as_dict=True)
			if ehform[0]['docstatus'] == 1 and ehform[0]['payment_completed'] == 1:
				invoicecharge = frappe.db.sql("SELECT  count(*) as count \
					FROM `tabHire Invoice Advance` as a \
					INNER JOIN `tabHire Charge Invoice` as c on a.parent=c.name \
					INNER JOIN `tabEquipment Hiring Form` as eq on c.ehf_name = eq.name \
					WHERE a.reference_row = \'" + str(a.name) + "\' \
					and eq.docstatus = '1' and eq.payment_completed = '1'", as_dict=True);
				if invoicecharge[0]['count'] < 1:
					data.append({"journal":a.journal, "name":a.name, "amount":a.amount, "party":a.party, "ref_type":a.ref_type, "ref_name":a.ref_name, "cost_center":a.cc, "posting_date":a.posting_date})
		return data
	else:
		frappe.throw("Select Equipment Hiring Form first!")
"""

