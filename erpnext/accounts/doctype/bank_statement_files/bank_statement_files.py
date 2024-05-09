# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
import sys, hashlib, os, signal, errno, logging, traceback
import csv
from frappe.utils import datetime

class BankStatementFiles(Document):
	pass

def is_date(string):
    try:
        # Attempt to parse the string as a date
        datetime.strptime(string, '%Y-%m-%d')
        return True
    except ValueError:
        return False

@frappe.whitelist()
def update_brs():
	for a in frappe.db.sql("""
						SELECT name, bank_statement_file
						FROM `tabBank Statement Files`
						WHERE update_brs = 0
						ORDER BY download_date
					""",as_dict=True):
		try:
			if os.path.exists(a.bank_statement_file):
				with open(a.bank_statement_file,'r') as f:
					reader = csv.reader(f)
					row=1
					for i in reader:
						if row > 1:
							k=0 if is_date(str(i[0])) else 1
							date_string = str(i[0+k])
							date_str = date_string.split("-")
							if len(date_str[2]) == 4:
								datetime_obj = datetime.strptime(date_string,'%d-%b-%Y')
							else:
								datetime_obj = datetime.strptime(date_string,'%d-%b-%y')
							correct_date_format = datetime_obj.strftime('%Y-%m-%d')
							doc = frappe.get_doc({
									'doctype' : "BRS Entries",
									'clearing_date': correct_date_format,
									'jrnl_no' : i[1+k],
									'clearing_time' : i[2+k],
									'account_no' : i[3+k],
									'amount' : i[4+k],
									'ref_no' : i[5+k],
									'narration' : i[6+k],
									'cheque_no' : i[1+k],
							})
							doc.submit()
						row += 1
			frappe.db.sql("update `tabBank Statement Files` set update_brs=1 where name='{}'".format(a.name))
		except Exception as e:
			logging.critical("FAILUER TO INSERT IN BRS Entries for file {}".format(a.bank_statement_file))
	frappe.db.commit()