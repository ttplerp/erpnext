# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import (
	flt,
	money_in_words,
)

class HireChargeEntry(Document):
	def validate(self):
		self.calculate_tds()
		self.validate_advance_allocated_amount()

	def calculate_tds(self):
		for a in self.items:
			a.tds_amount = flt(a.tds_percent)/100 * a.amount

	def on_submit(self):
		self.submit_hire_charge_invoice()
		self.update_advance_balance
	
	def on_cancel(self):
		self.update_advance_balance()

	def validate_advance_allocated_amount(self):
		for a in self.advances:
			if a.allocated_amount <= 0:
				frappe.throw("Allocated amount at ROW #{} cannot have {}, must be greater than 0".format(a.idx, a.allocated_amount))

	def update_advance_balance(self):
		for advance in self.advances:
			allocated_amount = 0.0
			if flt(advance.allocated_amount) > 0:
				balance_amount = frappe.db.get_value("Hire Charge Advance", advance.reference_name, "balance_amount")
				if flt(balance_amount) < flt(advance.allocated_amount) and self.docstatus < 2:
					frappe.throw(_("Advance#{0} : Allocated amount Nu. {1}/- cannot be more than Advance Balance Nu. {2}/-").format(advance.reference_name, "{:,.2f}".format(flt(advance.allocated_amount)),"{:,.2f}".format(flt(balance_amount))))
				else:
					allocated_amount = -1*flt(advance.allocated_amount) if self.docstatus == 2 else flt(advance.allocated_amount)

					adv_doc = frappe.get_doc("Hire Charge Advance", advance.reference_name)
					adv_doc.adjustment_amount = flt(adv_doc.adjustment_amount) + flt(allocated_amount)
					adv_doc.balance_amount    = flt(adv_doc.balance_amount) - flt(allocated_amount)
					adv_doc.save(ignore_permissions = True)

	def submit_hire_charge_invoice(self):
		if self.hire_charge_invoice_created == 0:
			frappe.throw("Please create Hire Charge Invoice.")

		successful = failed = 0
		for invoice in self.items:
			error = None
			try:
				hire_charge_invocie = frappe.get_doc(
					"Hire Charge Invoice",
					{
						"branch": invoice.branch,
						"party_type": invoice.party_type,
						"party": invoice.party,
						"docstatus": 0,
						"hire_charge_entry": self.name,
					},
				)
				hire_charge_invocie.submit()
				successful += 1
			except Exception as e:
				error = e
				failed += 1
				
		if successful > failed:
			self.db_set("hire_charge_invoice_submitted", 1)

	@frappe.whitelist()
	def get_advance(self):
		self.set("advances", [])
		for item in self.items:
			res = self.get_advance_entries(item.party_type, item.party)

			for d in res:
				advance_row = {
					"doctype": self.doctype + " Advance",
					"reference_type": d.reference_type,
					"reference_name": d.reference_name,
					"party_type": d.party_type,
					"party": d.party,
					# "reference_row": d.reference_row,
					# "remarks": d.remarks,
					"cost_center": d.cost_center,
					"advance_amount": flt(d.advance_amount),
					"advance_account": d.account,
					# "allocated_amount": allocated_amount,
					# "ref_exchange_rate": flt(d.exchange_rate),  # exchange_rate of advance entry
				}
				self.append("advances", advance_row)

	def get_advance_entries(self, party_type, party):
		hire_charge_advance = frappe.db.sql("""
											select
									  			'Hire Charge Advance' as reference_type, name as reference_name, advance_account as account, balance_amount as advance_amount, cost_center, party_type, party
									  		from 
												`tabHire Charge Advance` 
									  		where
									  			docstatus = 1 and balance_amount > 0 and party_type = '{}' and party = '{}'
										""".format(party_type, party), as_dict=True)

		# journal_entries = frappe.db.sql("""
		# 									select 
		# 						   				'Journal Entry' as reference_type, t1.name as reference_name, t2.account, t2.debit_in_account_currency as advance_amount, t2.account, t2.cost_center, t2.party_type, t2.party
		# 						   			from 
		# 						   				`tabJournal Entry` t1, `tabJournal Entry Account` t2
		# 						   			where t1.name = t2.parent
		# 						   			and t2.party_type = '{}' and t2.party = '{}'
		# 						   			and t2.is_advance='Yes'
		# 						   			and t1.docstatus = 1
		# 									""".format(party_type, party), as_dict=True)
		# return journal_entries + hire_charge_advance
		return hire_charge_advance
		
	@frappe.whitelist()
	def create_hire_charge_invoice(self):
		self.check_permission("write")

		args = frappe._dict({
			'posting_date': self.posting_date,
		})

		failed = successful = 0
		for a in self.items:
			args.update({
				"hire_charge_entry": self.name,
				"doctype": "Hire Charge Invoice",
				'branch': a.branch,
				'cost_center': a.cost_center,
				'party_type': a.party_type,
				'party': a.party,
				'status': 'Draft',
				'tds_percent': a.tds_percent,
				'tds_amount': a.tds_amount,
				'tds_account': a.tds_account,
				'grand_total': a.amount,
				'equipment_type': a.equipment_type,
				'equipment_no': a.equipment_no,

			})

			error = None
			try:
				hire_charge_invoice = frappe.get_doc(args)
				hire_charge_invoice.set("deduct_items", [])

				for d in self.deductions:
					if d.party_type == a.party_type and d.party == a.party:
						hire_charge_invoice.append(
							'deduct_items',
							{
								"account": d.account,
								"amount": d.amount,
							},
						)
				
				
				hire_charge_invoice.set("advances", [])
				for d in self.advances:
					if d.party_type == a.party_type and d.party == a.party:
						hire_charge_invoice.append(
							'advances',
							{
								"account": d.advance_account,
								"amount": d.allocated_amount,
							},
						)
				hire_charge_invoice.insert()
				successful += 1

			except Exception as e:
				error = e
				failed += 1

		self.hire_charge_invoice_created = 1
		self.save()
		self.reload()

	@frappe.whitelist()
	def post_to_account(self):
		total_payable_amount = 0
		accounts = []
		if self.settle_imprest_advance_account == 1:
			bank_account = frappe.db.get_value("Company", self.company, "imprest_advance_account")
		else:
			bank_account = frappe.db.get_value("Company", self.company, "default_bank_account")
		hire_charge_payable_acc = frappe.db.get_single_value("Maintenance Settings", "hire_charge_payable_account")

		if not bank_account:
			frappe.throw('Set default bank account in company {}'.format(self.company))

		query = frappe.db.sql("""
						select name from `tabHire Charge Invoice`
						where docstatus = 1
						and hire_charge_entry = '{}'
						and outstanding_amount > 0	
					""".format(self.name, self.branch), as_dict=True)
		for a in query:
			hire_charge_invoice = frappe.get_doc("Hire Charge Invoice", a.name)
			total_payable_amount += flt(hire_charge_invoice.payable_amount, 2)
			accounts.append({
				"account": hire_charge_payable_acc,
				"debit_in_account_currency": flt(hire_charge_invoice.payable_amount,2),
				"cost_center": hire_charge_invoice.cost_center,
				"party_check": 1,
				"party_type": hire_charge_invoice.party_type,
				"party": hire_charge_invoice.party,
				"reference_type": hire_charge_invoice.doctype,
				"reference_name": hire_charge_invoice.name,
			})
		if self.settle_imprest_advance_account == 1:
			accounts.append({
				"account": bank_account,
				"credit_in_account_currency": flt(total_payable_amount, 2),
				"cost_center": self.cost_center,
				"party_type": "Employee",
				"party": self.imprest_party,
			})
		else:
			accounts.append({
				"account": bank_account,
				"credit_in_account_currency": flt(total_payable_amount, 2),
				"cost_center": self.cost_center,
			})
		je = frappe.new_doc("Journal Entry")
		je.flags.ignore_permission = 1
		je.update({
			"doctype": "Journal Entry",
			"voucher_type": "Journal Entry" if self.settle_imprest_advance_account == 1 else "Bank Entry",
			"naming_series": "Journal Voucher" if self.settle_imprest_advance_account == 1 else "Bank Payment Voucher",
			"title": "Hire Charge",
			"user_remark": "Note: Hire Charge Invoice Payment",
			"posting_date": self.posting_date,
			"company": self.company,
			"total_amount_in_words": money_in_words(total_payable_amount),
			"branch": self.branch,
			"reference_type":self.doctype,
			"reference_doctype":self.name,
			"accounts":accounts
		})
		je.insert()
		frappe.msgprint(_('Journal Entry {0} posted to accounts').format(frappe.get_desk_link("Journal Entry", je.name)))