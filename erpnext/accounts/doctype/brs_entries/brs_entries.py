# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt
from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt, get_bench_path, get_datetime, get_site_path, add_days, nowdate, getdate, formatdate

class BRSEntries(Document):
	pass

@frappe.whitelist()
def update_bank_clearance_date():
	for a in frappe.db.sql("""
						SELECT name, cheque_no, clearing_date, account_no, amount, jrnl_no, ref_no, narration
						FROM `tabBRS Entries`
						WHERE docstatus = 1
						AND reconciled = 0
						AND amount < 0
						ORDER BY clearing_date
					""",as_dict=True):
		# Outgoing Payment (Credit to Bank Account)
		if a.ref_no:
			transaction_ids = []
			for c in frappe.db.sql("""
								select i.transaction_type, i.transaction_id, i.amount, i.bank_account_no
								from `tabBank Payment` b, `tabBank Payment Item` i
								where b.name = i.parent
								and b.docstatus = 1
								and (i.pi_number='{0}' 
										or 
								i.bank_journal_no='{1}')
								group by i.pi_number
								Union 
								select "Direct Payment" as transaction_type, b.direct_payment as transaction_id, i.net_amount as amount, 
							 	i.payment_journal_no as bank_journal_no
								from `tabUtility Bill` b, `tabUtility Bill Item` i
								where b.name = i.parent
								and b.docstatus = 1
								and (i.pi_number='{0}' 
										or 
								i.payment_journal_no='{1}')
								group by i.pi_number
							""".format(a.ref_no, a.jrnl_no), as_dict=True):
				if c.transaction_id not in transaction_ids:
					transaction_ids.append(c.transaction_id)
					if c.transaction_type in ["Direct Payment","Journal Entry","Payment Entry"]:
						frappe.db.sql("""
									Update `tab{0}` 
									set clearance_date = '{1}'
									where name = '{2}'
								""".format(c.transaction_type, a.clearing_date, c.transaction_id))
						frappe.db.sql("""
								Update `tabBRS Entries` set reconciled = 1 where name = '{}'
						""".format(a.name))
	frappe.db.commit()