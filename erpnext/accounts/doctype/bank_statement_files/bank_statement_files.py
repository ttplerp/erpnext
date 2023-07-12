# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
import sys, hashlib, os, signal, errno, logging, traceback
import csv

class BankStatementFiles(Document):
	pass

@frappe.whitelist()
def update_brs():
	from datetime import datetime
	for a in frappe.db.sql("""
						SELECT name, bank_statement_file
						FROM `tabBank Statement Files`
						WHERE update_brs = 0
						ORDER BY download_date
					""",as_dict=True):
		if os.path.exists(a.bank_statement_file):
			with open(a.bank_statement_file,'r') as f:
				reader = csv.reader(f)
				row=1
				for i in reader:
					if row > 1:
						date_string = str(i[0])
						datetime_obj = datetime.strptime(date_string,'%d-%b-%Y')
						correct_date_format = datetime_obj.strftime('%Y-%m-%d')
						doc = frappe.get_doc({
								'doctype' : "BRS Entries",
								'clearing_date': correct_date_format,
								'jrnl_no' : i[1],
								'clearing_time' : i[2],
								'account_no' : i[3],
								'amount' : i[4],
								'ref_no' : i[5],
								'narration' : i[6],
								'cheque_no' : i[1],
						})
						doc.submit()
					row += 1
		frappe.db.sql("update `tabBank Statement Files` set update_brs=1 where name='{}'".format(a.name))
	frappe.db.commit()