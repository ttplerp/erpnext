from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
import logging
import csv
from datetime import datetime
import traceback

class BankStatementFiles(Document):
	pass

def is_date(string):
	try:
		datetime.strptime(string, '%Y-%m-%d')
		return True
	except ValueError:
		return False

@frappe.whitelist()
def update_brs():
	bank_statement_files = frappe.db.sql("""
		SELECT name, bank_statement_file
		FROM `tabBank Statement Files`
		WHERE update_brs = 0
		ORDER BY download_date
	""", as_dict=True)
	for file in bank_statement_files:
		try:
			with open(file.bank_statement_file, 'r') as f:
				reader = csv.reader(f)
				next(reader)  # Skip header row
				for row in reader:
					print(str(row))
					# k = 0 if is_date(str(row[0])) else 1
					k=0 if "-" in str(row[0]) else 1
					date_string = str(row[0 + k])
					date_str = date_string.split("-")
					try:
						if len(date_str[2]) == 4:
							datetime_obj = datetime.strptime(date_string, '%d-%b-%Y')
						else:
							datetime_obj = datetime.strptime(date_string, '%d-%b-%y')
						correct_date_format = datetime_obj.strftime('%Y-%m-%d')
					except ValueError as e:
						logging.warning(f"Date parsing error in row: {row} - {e}")
						continue

					try:
						doc = frappe.get_doc({
							'doctype': "BRS Entries",
							'clearing_date': correct_date_format,
							'jrnl_no': row[1 + k],
							'clearing_time': row[2 + k],
							'account_no': row[3 + k],
							'amount': row[4 + k],
							'ref_no': row[5 + k],
							'narration': row[6 + k],
							'cheque_no': row[1 + k],
						})
						doc.submit()
					except Exception as e:
						logging.warning(f"Error creating BRS Entries for row: {row} - {e}")
						continue

				frappe.db.sql("UPDATE `tabBank Statement Files` SET update_brs = 1 WHERE name = %s", (file.name,))
		except Exception as e:
			logging.critical(f"Failure to process file {file.bank_statement_file}: {e}")
			logging.critical(traceback.format_exc())

	frappe.db.commit()
