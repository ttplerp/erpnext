'''
--------------------------------------------------------------------------------------------------------------------------
Version		  Author		  				CreatedOn		  ModifiedOn		  Remarks
------------ --------------- ------------------ -------------------  -----------------------------------------------------
1.0		      Dawa Nyuehtyue Tshering		2024/11/15							   Original Version
--------------------------------------------------------------------------------------------------------------------------			
'''

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, time_diff_in_hours, get_datetime, getdate, cint, get_datetime_str
from erpnext.controllers.accounts_controller import AccountsController
from erpnext.accounts.party import get_party_account
from erpnext.accounts.utils import get_tds_account, get_account_type
from erpnext.accounts.general_ledger import (
	get_round_off_account_and_cost_center,
	make_gl_entries,
	make_reverse_gl_entries,
	merge_similar_entries,
)

class ProjectInvoice(AccountsController):
	def validate(self):
		self.set_status()
		self.set_defaults()
		self.validate_mb_entries()
		self.validate_items()
		self.load_invoice_boq()
				
	def on_submit(self):
		self.update_boq_item()
		self.update_boq()
		self.update_mb_entries()
		self.make_gl_entry()
		self.project_invoice_item_entry()
		self.update_advance_balance()

	def on_cancel(self):
		self.ignore_linked_doctypes = ("GL Entry", "Stock Ledger Entry", "Payment Ledger Entry")
		self.update_boq_item(cancel=True)
		self.update_boq(cancel=True)
		self.update_mb_entries(cancel=True)
		self.make_gl_entry()
		self.project_invoice_item_entry(cancel=True)
		self.update_advance_balance(cancel=True)

	def set_status(self, update=False, status=None, update_modified=True):
		if self.is_new():
			self.payment_status = "Draft"
			return

		outstanding_amount = flt(self.outstanding_amount, 2)
		if not status:
			if self.docstatus == 2:
				status = "Cancelled"
			elif self.docstatus == 1:
				if outstanding_amount > 0 and flt(self.total_amount) > outstanding_amount:
					self.payment_status = "Partly Paid"
				elif outstanding_amount > 0 :
					self.payment_status = "Unpaid"
				elif outstanding_amount <= 0:
					self.payment_status = "Paid"
				else:
					self.payment_status = "Submitted"
			else:
				self.payment_status = "Draft"

		if update:
			self.db_set("payment_status", self.payment_status, update_modified=update_modified)

	def on_update_after_submit(self):
		self.project_invoice_item_entry()

	def project_invoice_item_entry(self, cancel=False):
		if cancel:
			frappe.db.sql("delete from `tabProject Invoice Item` where parent='{project}' and invoice_name = '{invoice_name}'".format(project=self.project, invoice_name=self.name))
		else:
			if not frappe.db.exists("Project Invoice Item", {"parent": self.project, "invoice_name": self.name}):
				doc = frappe.get_doc("Project", self.project)
				row = doc.append("project_invoice_item", {})
				row.invoice_name            = self.name
				row.invoice_date            = self.invoice_date
				row.boq                     = self.boq
				row.subcontract             = self.subcontract
				row.total_amount            = flt(self.total_amount)
				# row.price_adjustment_amount = flt(self.price_adjustment_amount)
				row.net_invoice_amount      = flt(self.net_amount)
				# row.total_received_amount   = flt(self.total_received_amount)
				# row.total_paid_amount       = flt(self.total_paid_amount)
				row.total_balance_amount    = flt(self.outstanding_amount)
				row.save(ignore_permissions=True)
			else:
				row = frappe.get_doc("Project Invoice Item", {"parent": self.project, "invoice_name": self.name})
				row.invoice_date            = self.invoice_date
				row.boq                     = self.boq
				row.subcontract             = self.subcontract
				row.total_amount    = flt(self.total_amount)
				# row.price_adjustment_amount = flt(self.price_adjustment_amount)
				row.net_invoice_amount      = flt(self.net_amount)
				# row.total_received_amount   = flt(self.total_received_amount)
				# row.total_paid_amount       = flt(self.total_paid_amount)
				row.total_balance_amount    = flt(self.outstanding_amount)
				row.save(ignore_permissions=True)

	def set_defaults(self):
		if self.project:
			base_project          = frappe.get_doc("Project", self.project)
			self.company          = base_project.company
			self.branch           = base_project.branch
			self.cost_center      = base_project.cost_center

			if not self.invoice_title:
				self.invoice_title = "Project Invoice ({0})".format(base_project.project_name)

			if base_project.status in ('Completed','Cancelled'):
				frappe.throw(_("Operation not permitted on already {0} Project.").format(base_project.status),title="Project Invoice: Invalid Operation")

		if self.boq:
			base_boq              = frappe.get_doc("BOQ", self.boq)
			self.cost_center      = base_boq.cost_center
			self.branch           = base_boq.branch
			self.boq_type         = base_boq.boq_type

	def validate_mb_entries(self):
		for i in self.get("project_invoice_mb"):
			for t in frappe.get_all("Project Invoice MB", ["parent"], {"entry_name": i.entry_name, "is_selected": 1, "docstatus": 1}, order_by="boq, subcontract, parent"):
				msg = '<b>Reference# : <a href="#Form/Project Invoice/{0}">{0}</a></b>'.format(t.parent)
				frappe.throw(_("Row#{0}: Measurement Book Entry {1} is already invoiced<br>{2}").format(i.idx,i.entry_name,msg))

	def get_name_list(self):
		name_list = frappe._dict()
		boq_list         = []
		subcontract_list = []
		mb_list          = []
		
		for i in self.get("project_invoice_mb"):
			if i.is_selected and i.subcontract:
				subcontract_list.append(i.subcontract)
			elif i.is_selected and not i.subcontract:
				boq_list.append(i.boq)

			if i.is_selected:
				mb_list.append(i.entry_name)
	
		# remove duplicate values
		boq_list = list(set(boq_list))
		subcontract_list = list(set(subcontract_list))
		mb_list = list(set(mb_list))

		# invoice can be either for BOQ or Subcontract only
		table_name = "Subcontract" if subcontract_list else "BOQ"

		name_list.setdefault('table_name', table_name)
		name_list.setdefault('boq_list',boq_list)
		name_list.setdefault('subcontract_list', subcontract_list)
		name_list.setdefault('mb_list', mb_list)

		return name_list

	# load project_invoice_boq for Running Account Bill print
	def load_invoice_boq(self):
		name_list = self.get_name_list()

		if not name_list.get("mb_list"):
			return

		mb_list          = "'"+"','".join(name_list.get("mb_list"))+"'"
		boq_list         = "'"+"','".join(name_list.get("boq_list"))+"'"
		subcontract_list = "'"+"','".join(name_list.get("subcontract_list"))+"'"

		mb_boq = frappe.db.sql("""
						select
								boq                              	as boq,
								subcontract                      	as subcontract,
								description							as description,
								max(bsr_code)                   	as bsr_code,
								max(uom)                         	as uom,
								max(ifnull(is_selected, 0))       	as is_selected,
								sum(ifnull(idx, 0))               	as idx,
								sum(ifnull(a.original_quantity, 0)) as original_quantity,
								max(ifnull(original_rate, 0))     	as original_rate,
								sum(ifnull(original_amount, 0))   	as original_amount,
								sum(ifnull(entry_quantity, 0))    	as entry_quantity,
								max(ifnull(entry_rate, 0))        	as entry_rate,
								sum(ifnull(entry_amount, 0))      	as entry_amount,
								max(creation)                    	as creation,
								sum(flag)                        	as flag
						from (
								select
										bi.parent         as boq,
										Null              as subcontract, 
										bi.bsr_code       as bsr_code,
										bi.description    as description,
										bi.uom            as uom,
										0                 as is_selected,
										bi.idx            as idx,
										bi.quantity       as original_quantity,
										bi.rate           as original_rate,
										bi.amount         as original_amount,
										0                 as entry_quantity,
										0                 as entry_rate,
										0                 as entry_amount,
										bi.creation       as creation,
										2                 as flag
								from `tabBOQ Item` as bi
								where parent in ({boq_list})
								union all
								select
										sc.boq            as boq,
										sc.name           as subcontract,
										sci.bsr_code      as bsr_code,
										sci.description   as description,
										sci.uom           as uom,
										0                 as is_selected,
										sci.idx           as idx,
										sci.quantity      as original_quantity,
										sci.rate          as original_rate,
										sci.amount        as original_amount,
										0                 as entry_quantity,
										0                 as entry_rate,
										0                 as entry_amount,
										sci.creation      as creation,
										2                 as flag
								from `tabSubcontract Item` as sci, `tabSubcontract` as sc
								where sc.name in ({subcontract_list}) 
								and sci.parent = sc.name 
								union all
								select
										me.boq            	as boq,
										me.subcontract    	as subcontract,
										mb.bsr_code  		as bsr_code,
										mb.description      as description,
										mb.uom            	as uom,
										mb.is_selected    	as is_selected,
										0                 	as idx,
										0                 	as original_quantity,
										0                 	as original_rate,
										0                 	as original_amount,
										(case
												when me.boq_type = 'Milestone Based' then 0
												else mb.entry_quantity
										end)              as entry_quantity,
										mb.entry_rate     as entry_rate,
										mb.entry_amount   as entry_amount,
										mb.creation       as creation,
										-2                as flag
								from `tabMB Entry BOQ` as mb, `tabMB Entry` me
								where mb.parent in ({mb_list})
								and   me.name = mb.parent
								and   mb.is_selected = 1
						) as a
						group by boq, subcontract, bsr_code
						order by ifnull(subcontract,boq), idx
						""".format(boq_list=boq_list, subcontract_list=subcontract_list, mb_list=mb_list), as_dict=1)

		self.project_invoice_boq = []
		for item in mb_boq:
			act_quantity = flt(item.original_quantity)
			act_rate     = flt(item.original_rate)
			act_amount   = flt(item.original_amount)

			uptodate_quantity = 0.0
			uptodate_rate     = 0.0
			uptodate_amount   = 0.0

			# Total Invoiced so far (excluding this Invoice)
			ti = frappe.db.sql("""
							select
									sum(ifnull(invoice_quantity,0)) as tot_invoice_quantity,
									max(ifnull(invoice_rate,0))     as tot_invoice_rate,
									sum(ifnull(invoice_amount,0))   as tot_invoice_amount
							from   `tabProject Invoice BOQ`
							where  bsr_code    = '{bsr_code}'
							and    is_selected      = 1
							and    docstatus        = 1
							and    parent           != '{parent}'
							""".format(bsr_code=item.bsr_code, parent=self.name), as_dict=1)[0]

			if ti:
					act_quantity = flt(item.original_quantity)-flt(ti.tot_invoice_quantity)
					act_rate     = flt(ti.tot_invoice_rate)
					act_amount   = flt(item.original_amount)-flt(ti.tot_invoice_amount)

					uptodate_quantity = flt(ti.tot_invoice_quantity)
					uptodate_rate     = flt(ti.tot_invoice_rate)
					uptodate_amount   = flt(ti.tot_invoice_amount)

			self.append("project_invoice_boq", {
					"boq": item.boq,
					"subcontract": item.subcontract,
					"bsr_code": item.bsr_code,
					"description": item.description,
					"uom": item.uom,
					"is_selected": item.is_selected,
					"original_quantity": item.original_quantity,
					"original_rate": item.original_rate,
					"original_amount": item.original_amount,
					"act_quantity": act_quantity,
					"act_rate": act_rate,
					"act_amount": act_amount,
					"invoice_quantity": item.entry_quantity,
					"invoice_rate": item.entry_rate,
					"invoice_amount": item.entry_amount,
					"uptodate_quantity": uptodate_quantity,
					"uptodate_rate": uptodate_rate,
					"uptodate_amount": uptodate_amount,
					"creation": self.creation,
					"modified": self.modified,
					"modified_by": self.modified_by,
					"owner": self.owner
			})
				
	def validate_items(self):
		total_amount    = 0

		for rec in self.project_invoice_mb:
			if rec.is_selected:
				total_amount += flt(rec.entry_amount)

		self.total_deduction_amount = self.calculate_total_deductions()

		self.total_amount 	= flt(total_amount)
		self.net_amount 	= self.outstanding_amount	= flt(self.total_amount) - flt(self.total_deduction_amount)
		
		if flt(self.total_amount) == 0:
			frappe.throw(_("Total Amount should be greater than zero"), title="Invalid Data")

	def calculate_total_deductions(self):
		total_deduction_amount = total_advance_amount = 0.0 
		if self.deductions:
			for item in self.deductions:
				total_deduction_amount += item.amount

		if self.advances:
			for item in self.advances:
				total_deduction_amount += flt(item.allocated_amount)
				total_advance_amount += flt(item.allocated_amount)
		self.total_advance_amount = flt(total_advance_amount)

		if self.tds_amount:
			total_deduction_amount += self.tds_amount
		
		if self.retention_amount:
			total_deduction_amount += self.retention_amount

		return total_deduction_amount

	def make_gl_entry(self):
		gl_entries = []
		self.make_party_gl_entry(gl_entries)
		self.make_advance_gl_entry(gl_entries)
		self.make_other_deduction_gl_entry(gl_entries)
		self.make_tds_gl_entry(gl_entries)
		self.make_retention_gl_entry(gl_entries)
		gl_entries = merge_similar_entries(gl_entries)
		make_gl_entries(gl_entries, update_outstanding="No", cancel=self.docstatus == 2)
						
	def make_party_gl_entry(self, gl_entries):
		if self.party_type == "Supplier":
			supplier_country = frappe.db.get_value('Supplier', self.party, 'country')
			income_expense_account = frappe.db.get_single_value("Projects Settings", "national_wage" if supplier_country == "Bhutan" else "foreign_wage")
		else:
			income_expense_account = frappe.db.get_single_value("Projects Settings", "income_account")
		if not income_expense_account:
			frappe.throw('Set accounts in Projects Settings')

		gl_entries.append(
			self.get_gl_dict({
				"account":  income_expense_account,
				"party_type": self.party_type,
				"party": self.party,
				"debit" if self.party_type == "Supplier" else "credit": self.total_amount,
				"debit_in_account_currency" if self.party_type == "Supplier" else "credit_in_account_currency": self.total_amount,
				"project": self.project,
				"cost_center": self.cost_center,
				"posting_date":self.invoice_date
			})
		)

		gl_entries.append(
			self.get_gl_dict({
					"account":  self.debit_credit_account,
					"party_type": self.party_type,
					"party": self.party,
					"against": self.debit_credit_account,
					"credit" if self.party_type == "Supplier" else "debit": self.net_amount,
					"credit_in_account_currency" if self.party_type == "Supplier" else "debit_in_account_currency": self.net_amount,
					"against_voucher": self.name,
					"against_voucher_type": self.doctype,
					"project": self.project,
					"cost_center": self.cost_center,
					"posting_date":self.invoice_date
			})
		)

	def make_advance_gl_entry(self, gl_entries):
		for adv in self.advances:
				advance_account_type = frappe.db.get_value(doctype="Account", filters=adv.advance_account, fieldname=["account_type"])

				gl_entries.append(
					self.get_gl_dict({"account": adv.advance_account,
						"credit" if self.party_type == "Supplier" else "debit": flt(adv.allocated_amount),
						"credit_in_account_currency" if self.party_type == "Supplier" else "debit_in_account_currency": flt(adv.allocated_amount),
						"cost_center": self.cost_center,
						"party_check": 1 if advance_account_type in ("Payable","Receivable") else 0,
						"party_type": self.party_type,
						"party": self.party,
						"account_type": advance_account_type,
						"is_advance": "No",
						"reference_type": self.doctype,
						"reference_name": self.name,
						"project": self.project,
						"posting_date":self.invoice_date
					})
				)
	def make_other_deduction_gl_entry(self, gl_entries):
		for ded in self.deductions:
			if flt(ded.amount) > 0:
				if not ded.account:
					frappe.throw(_("Row#{0}: Account cannot be blank under other deductions.").format(ded.idx))
						
				deduction_account_type = frappe.db.get_value(doctype="Account", filters=ded.account, fieldname=["account_type"])
				gl_entries.append(
					self.get_gl_dict({"account": ded.account,
							"credit" if self.party_type == "Supplier" else "debit": flt(ded.amount),
							"credit_in_account_currency" if self.party_type == "Supplier" else "debit_in_account_currency": flt(ded.amount),
							"cost_center": self.cost_center,
							"account_type": deduction_account_type,
							"is_advance": "No",
							"reference_type": self.doctype,
							"reference_name": self.name,
							"project": self.project,
							"party_check": 1 if deduction_account_type in ("Payable","Receivable") else 0,
							"party_type": self.party_type,
							"party": self.party,
							"posting_date":self.invoice_date
					})
				)
				
	def make_tds_gl_entry(self, gl_entries):
		if flt(self.tds_amount) > 0:
			if not self.tds_account:
				self.tds_account = get_tds_account(self.tds_percent, self.company, self.party_type)
					
			tds_account_type = frappe.db.get_value(doctype="Account", filters=self.tds_account, fieldname=["account_type"])

			gl_entries.append(
				self.get_gl_dict({"account": self.tds_account,
					"credit" if self.party_type == "Supplier" else "debit": flt(self.tds_amount),
					"credit_in_account_currency" if self.party_type == "Supplier" else "debit_in_account_currency": flt(self.tds_amount),
					"cost_center": self.cost_center,
					"account_type": tds_account_type,
					"is_advance": "No",
					"reference_type": self.doctype,
					"reference_name": self.name,
					"project": self.project,
					"posting_date":self.invoice_date
				})
			)

	def make_retention_gl_entry(self, gl_entries):
		if flt(self.retention_amount) > 0:
			if not self.retention_account:
				self.retention_account = get_tds_account(self.retrntion_percent, self.company, self.party_type)
					
			retwntion_account_type = frappe.db.get_value(doctype="Account", filters=self.tds_account, fieldname=["account_type"])

			gl_entries.append(
				self.get_gl_dict({
					"account": self.retention_account,
					"credit" if self.party_type == "Supplier" else "debit": flt(self.retention_amount),
					"credit_in_account_currency" if self.party_type == "Supplier" else "debit_in_account_currency": flt(self.retention_amount),
					"cost_center": self.cost_center,
					"account_type": retwntion_account_type,
					"is_advance": "No",
					"reference_type": self.doctype,
					"reference_name": self.name,
					"project": self.project,
					"posting_date":self.invoice_date
				})
			)

	def update_boq_item(self, cancel=False):
		boq_list = frappe.db.sql("""
							select
								t1.boq, t1.subcontract, t2.bsr_code,
								sum(ifnull(t2.entry_quantity, 0)) as entry_quantity,
								sum(ifnull(t2.entry_amount, 0)) as entry_amount
							from  
								`tabProject Invoice MB` as t1, `tabMB Entry BOQ` t2
							where t1.parent = '{parent}'
								and t1.is_selected = 1
								and t2.parent = t1.entry_name
								and t2.is_selected = 1
								group by t1.boq, t1.subcontract, t2.bsr_code
							""".format(parent = self.name), as_dict=True)

		for item in boq_list:
			table_name 	= "Subcontract" if item.subcontract else "BOQ"
			parent 		= item.subcontract if item.subcontract else item.boq
			bsr_code	= item.bsr_code

			claimed_quantity 	= -1*flt(item.entry_quantity) if cancel else flt(item.entry_quantity)
			claimed_amount 	    = -1*flt(item.entry_amount) if cancel else flt(item.entry_amount)

			query = """
				UPDATE `tab{table_name} Item`
				SET
					claimed_quantity = IFNULL(claimed_quantity, 0) + IFNULL(%s, 0),
					booked_quantity = IFNULL(booked_quantity, 0) - IFNULL(%s, 0),
					claimed_amount = IFNULL(claimed_amount, 0) + IFNULL(%s, 0),
					booked_amount = IFNULL(booked_amount, 0) - IFNULL(%s, 0)
				WHERE bsr_code = %s
				AND parent = %s
			""".format(table_name=table_name)

			frappe.db.sql(query, (claimed_quantity, claimed_quantity, claimed_amount, claimed_amount, bsr_code, parent))
				
	def update_boq(self, cancel=False):
		for i in self.project_invoice_mb:
			if i.is_selected:
				total_invoice_amount = -1*flt(i.entry_amount) if cancel else flt(i.entry_amount)

				if total_invoice_amount:
					doc = frappe.get_doc("Subcontract" if i.subcontract else "BOQ", i.subcontract if i.subcontract else i.boq)
					doc.claimed_amount  	    = flt(doc.claimed_amount) + flt(total_invoice_amount)
					doc.total_claimed_amount  	= flt(doc.claimed_amount) + flt(total_invoice_amount)
					doc.total_unclaimed_amount 	= flt(doc.total_unclaimed_amount) - flt(total_invoice_amount)
					doc.save(ignore_permissions = True)

	def update_mb_entries(self, cancel=False):
		for mb in self.project_invoice_mb:
			if flt(mb.entry_amount) > 0 and mb.is_selected:
				entry_amount      = -1*flt(mb.entry_amount) if cancel else flt(mb.entry_amount)

				mb_doc = frappe.get_doc("MB Entry", mb.entry_name)
				mb_doc.total_invoice_amount   	= flt(mb_doc.total_invoice_amount) + flt(entry_amount)
				mb_doc.total_balance_amount 	= flt(mb_doc.total_balance_amount) - flt(entry_amount)
				# mb_doc.status                 = 'Uninvoiced' if flt(balance_amount) > 0 else 'Invoiced'
				mb_doc.save(ignore_permissions = True)

	def update_advance_balance(self, cancel=False):
		for adv in self.advances:
			allocated_amount = 0.0
			if flt(adv.allocated_amount) > 0:
				if adv.reference_doctype == 'Project Advance':
					balance_amount = frappe.db.get_value("Project Advance", adv.reference_name, "balance_amount")
					if flt(balance_amount) < flt(adv.allocated_amount) and self.docstatus < 2:
						frappe.throw(_("Advance#{0} : Allocated amount Nu. {1}/- cannot be more than Advance Balance Nu. {2}/-").format(adv.reference_name, "{:,.2f}".format(flt(adv.allocated_amount)),"{:,.2f}".format(flt(balance_amount))))
					else:
						allocated_amount = -1 * flt(adv.allocated_amount) if self.docstatus == 2 else flt(adv.allocated_amount)

						adv_doc = frappe.get_doc("Project Advance", adv.reference_name)
						adv_doc.adjusted_amount = flt(adv_doc.adjusted_amount) + flt(allocated_amount)
						adv_doc.balance_amount    = flt(adv_doc.balance_amount) - flt(allocated_amount)
						adv_doc.save(ignore_permissions = True)

	@frappe.whitelist()
	def get_mb_list(self):
		row_data = self.get_mb_data()
		self.set("project_invoice_mb", [])

		if row_data:
			for a in row_data:
				entry = {
					'entry_name': a.name,
					'entry_date': a.entry_date,
					'entry_amount': a.total_balance_amount,
					'boq': a.boq,
					'subcontract': a.subcontract,
				}
				self.append("project_invoice_mb", entry)
		else:
			frappe.msgprint("There is no entries found")

	def get_mb_data(self):
		result = frappe.db.sql("""
			select *
			from `tabMB Entry`
			where project = '{project}'
			and docstatus = 1
			and party_type = '{party_type}'
			and party = '{party}'
			and boq = '{boq}'
			and total_balance_amount > 0
			""".format(project=self.project, party_type=self.party_type, party=self.party, boq=self.boq), as_dict=True)

		return result
			
@frappe.whitelist()
def get_project_party_type(doctype, txt, searchfield, start, page_len, filters):
	result = []
			
	if not filters.get("project"):
			return result

	result = frappe.db.sql("""
			select distinct party_type
			from `tabBOQ`
			where project = '{project}'
			union all
			select distinct party_type
			from `tabSubcontract`
			where project = '{project}'
	""".format(project=filters.get("project")))
			
	return result

@frappe.whitelist()
def get_project_party(doctype, txt, searchfield, start, page_len, filters):
	result = []
			
	if not filters.get("project") or not filters.get("party_type"):
			return result

	result = frappe.db.sql("""
			select distinct party
			from `tabBOQ`
			where project = '{project}'
			and party_type = '{party_type}'
			union all
			select distinct party
			from `tabSubcontract`
			where project = '{project}'
			and party_type = '{party_type}'
	""".format(project=filters.get("project"), party_type=filters.get("party_type")))
			
	return result
	
@frappe.whitelist()
def get_advance_list(project, party_type, party):
	query = frappe.db.sql("""
		select name, balance_amount, advance_account, 'Project Advance' as reference_doctype
		from `tabProject Advance`
		where project = '{project}'
		and party_type = '{party_type}'
		and party = '{party}'
		and docstatus = 1
		and balance_amount > 0
		""".format(project=project, party_type=party_type, party=party), as_dict=True)

	return query
