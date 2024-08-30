# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
import json
from frappe.utils import getdate, get_datetime, now, cint, flt

class CBSEntry(Document):
	def validate(self):
		self.validate_dates()
		self.validate_workflow()
		self.load_data_file()

	def before_submit(self):
		self.title_final = (str(self.entry_title) if self.entry_type == "Upload" else " ") + " " + self.entry_time

	def on_submit(self):
		self.validate_data()
		self.process_data()

	def on_cancel_after_draft(self):
		self.remove_entries()

	def before_cancel(self):
		if self.upload_file and self.status and self.status not in ("Failed", "Draft"):
			frappe.throw(_("Cancellation of uploads in status <b>{}</b> not permitted").format(self.status), title="Not permitted")

	def on_cancel(self):
		self.remove_entries()

	def load_data_file(self):
		self.download_json = json.dumps([])
		if self.entry_type == "Download":
			if not self.process_type:
				frappe.msgprint(_("<b>Process Type</b> is mandatory"))
			else:
				if self.process_type == "Manual" and self.download_file:
					self.process_data_file()

	def process_data_file(self):
		headers = ["GL_CODE", "DESCRIPTION", "CUR"]
		header_found = 0
		transactions = get_transaction_entries(self.download_file)

		if transactions:
			for header in headers:
				if header not in transactions[0]:
					header_found = 0
					break
				else:
					header_found = 1

		if not transactions or (header_found and len(transactions) == 1):
			frappe.throw(_("No data found in <b>Data File</b>"))
		elif not header_found:
			frappe.throw(_("<b>Data File</b> must contain following headers <br>{}").format(headers))

		columns = transactions[0]
		data = []
		for r in transactions[1:]:
			data.append(frappe._dict(zip(columns, r)))
		self.download_json = json.dumps(data)

	def validate_workflow(self):
		#if self.get_db_value("workflow_state") == "Draft" and self.workflow_state == "Waiting Approval" \
		#		and not self.total_debit and not self.total_credit:
		if self.docstatus == 0 and not self.total_debit and not self.total_credit:
			frappe.throw(_("No data found. Please click on <b>Get Transactions</b> to fetch the details"))

	def validate_dates(self):
		self.entry_time = get_datetime().strftime("%Y-%m-%d %H:%M:%S")
		self.title_final= self.entry_title
		if self.entry_type == "Download":
			self.from_date = None
			if not self.to_date:
				frappe.throw(_("To Date is mandatory"))
			elif str(self.to_date) > str(getdate()):
				frappe.throw(_("To Date cannot be a future date"))
			for i in frappe.db.get_all('CBS Entry', filters={'name': ('!=', self.name), 'entry_type': self.entry_type,'to_date': ('>',self.to_date), 'docstatus':('!=',2)}, fields=["name", "to_date"], order_by="to_date desc"):
				frappe.throw(_("Download not permitted as the GL balances are already pulled till {} via {}").format(i.to_date, frappe.get_desk_link('CBS Entry', i.name)))
		elif self.entry_type == "Upload":
			if not self.from_date:
				frappe.throw(_("From Date is mandatory"))
			elif not self.to_date:
				frappe.throw(_("To Date is mandatory"))
			elif str(self.from_date) > str(getdate()):
				frappe.throw(_("From Date cannot be a future date"))
			elif str(self.to_date) > str(getdate()):
				frappe.throw(_("To Date cannot be a future date"))
			elif self.to_date < self.from_date:
					frappe.throw(_("To Date cannot be before From Date"))

	def validate_data(self):
		if self.entry_type == "Upload":
			if not frappe.db.exists('CBS Entry Upload', {'cbs_entry': self.name}):
				frappe.throw(_("No data found for uploading"))
			if self.error:
				frappe.throw(_("Please fix the following errors to proceed. <br>{}").format(self.error), title="Unable to process")
			self.validate_cancelled_transactions()

	def validate_cancelled_transactions(self):
		if self.entry_type != "Upload":
			return
		li = frappe.db.sql("""select voucher_type, voucher_no from `tabCBS Entry Upload` ceu
				where ceu.cbs_entry = "{}"
				and not exists(select 1
						from `tabGL Entry` gle
						where gle.name = ceu.gl_entry)
				order by reference_number""".format(self.name), as_dict=True)
		for i in li:
			frappe.throw(_("Transaction {} is cancelled. Please pull the transactions again.").format(frappe.get_desk_link(i.voucher_type, i.voucher_no)))

	def process_data(self):
		if self.entry_type == "Download":
			if self.process_type == "Manual":
				if not self.download_file:
					frappe.throw(_("<b>Data File</b> is mandatory for Manual Downloads"))
				self.create_gl_entries()
			else:
				frappe.enqueue(download, job_name='CBSDOWNLOAD', timeout=1500, cbs_entry=self, ason_date=self.to_date, publish_progress=True)
		else:
			self.submit_upload_entries()
			# frappe.enqueue(upload, timeout=1500, cbs_entry=self, publish_progress=True)
			upload(cbs_entry=self, publish_progress=True)

	def get_data_for_upload(self):
		data = []
		error = []
		upload_list = []
		if self.entry_type == "Upload":
			frappe.db.sql('delete from `tabCBS Entry Upload` where cbs_entry="{}"'.format(self.name))
			self.error = None
			self.total_debit, self.total_credit = 0, 0
			data = get_data(doctype=self.reference_type, docname=self.reference_name, \
						doclist=json.loads(self.reference_list) if self.reference_list else None, from_date=self.from_date, to_date=self.to_date)
			for i in data:
				reference_number = make_autoname('ER.YY.MM.DD.#######')
				upload_list.append((
					frappe.generate_hash(txt="", length=10), reference_number, self.name, 
					i.gl_entry, i.voucher_type, i.voucher_no, i.account, i.debit, i.credit, 
					i.gl_type_cd, i.branch_code, i.currency_code, i.account_number, i.segment_code,
					i.amount, i.remarks, i.processing_branch, i.posting_date, i.error, i.gl_type,
					0, 0, frappe.session.user, str(get_datetime()), 
					frappe.session.user, str(get_datetime())
				))
				self.total_debit = flt(self.total_debit) + flt(i.debit)
				self.total_credit= flt(self.total_credit) + flt(i.credit)
				if i.error:
					error.append(i.error)

		if error:
			self.error = "<ul><li>" + "</li><li>".join(list(set(error))) + "</li></ul>"
		else:
			self.error = None
		self.create_upload_entries(upload_list)

	def create_upload_entries(self, upload_list):
		if upload_list:
			values = ', '.join(map(str, upload_list))
			frappe.db.sql("""INSERT INTO `tabCBS Entry Upload`(name, reference_number, cbs_entry, 
						gl_entry, voucher_type, voucher_no, account, debit, credit,
						gl_type_cd, branch_code, currency_code, account_number, segment_code,
						amount, remarks, processing_branch, posting_date, error, gl_type,
						idx, docstatus, owner, creation, modified_by, modified)
					VALUES {}""".format(values))

	def submit_upload_entries(self):
		frappe.db.sql('update `tabCBS Entry Upload` set docstatus = 1 where cbs_entry="{}"'.format(self.name))

	def remove_entries(self):
		''' remove following entries on cancellation
				Download: GL Entry
				Upload: CBS Entry Upload '''
		if self.entry_type == "Download":
			if cint(self.is_period_closing_entry) and self.period_closing_voucher:
				doc = frappe.get_doc("Period Closing Voucher", self.period_closing_voucher)
				doc.flags.ignore_permissions=True
				doc.cancel()

			for i in frappe.db.get_all('CBS Entry', {'entry_type': 'Download', 'to_date': ('>=',self.to_date), 'entry_time': ('>', self.entry_time), 'docstatus': ('!=', 2)}):
				frappe.throw(_("Not permitted to cancel as gl balances are already adjusted via {}").format(frappe.get_desk_link('CBS Entry', i.name)))
			frappe.db.sql("delete from `tabGL Entry` where voucher_type='CBS Entry' and voucher_no='{}'".format(self.name))
		else:
			frappe.db.sql("delete from `tabCBS Entry Upload` where cbs_entry='{}'".format(self.name))
		#self.db_set('workflow_state', 'Cancelled')
		self.db_set('status', 'Cancelled')
		self.reload()

	def get_formatted_data(self, download_json):
		''' return data in the following format
			{"11000100 BTN": {"0999": {"LCY": 3000000000, "FCY": 0}}}'''
		if not download_json:
			return download_json

		formatted_json = frappe._dict()
		for d in json.loads(download_json):
			d = frappe._dict(d)
			for c in d:
				if str(d.GL_CODE).strip() and c.split('_')[-1].upper() in ('LCY','FCY'):
					key = (str(d.GL_CODE).strip() + " " + str(d.CUR).strip()).strip() if str(d.CUR).strip() else str(d.GL_CODE).strip()
					formatted_json.setdefault(key, frappe._dict()).setdefault(c.split('_')[0], frappe._dict()).setdefault(c.split('_')[-1].upper(), d.get(c))
		return formatted_json

	def create_gl_entries(self):
		''' make gl entry for the difference between previous and current balance '''
		def _prepare_log(log, log_type, log_title, det_key, det_amount):
			if log.get(log_title):
				log[log_title]['details'][det_key] = flt(log[log_title]['details'].get(det_key)) + flt(det_amount)
			else:
				log.setdefault(log_title, frappe._dict()).setdefault('log_type', log_type)
				log.setdefault(log_title, frappe._dict()).setdefault('details',frappe._dict()).setdefault(det_key, flt(det_amount))

		if not self.download_json:
			frappe.throw(_("No data found for processing"))

		# prev_download_json = self.get_previous_data()
		# prev_data= self.get_formatted_data(prev_download_json) if prev_download_json else {}
		prev_data = frappe._dict()
		cur_data = self.get_formatted_data(self.download_json) if self.download_json else {}

		accounts = self.get_accounts()
		fa_accounts = self.get_fixed_asset_accounts()
		branches = self.get_branches()

		log = frappe._dict()
		gl_list = []
		total_debit, total_credit = 0, 0

		if self.process_type == "Manual":
			remarks = 'Balances till {} uploaded manually on {}'.format(str(self.to_date), str(self.entry_time))
		else:
			remarks = 'Balances till {} pulled from CBS on {}'.format(str(self.to_date), str(self.entry_time))

		voucher_type, voucher_no = 'CBS Entry', self.name
		if cint(self.is_period_closing_entry) and str(self.to_date) == str(self.to_date)[0:4]+"-12-31":
			voucher_type = 'Period Closing Voucher'
			doc = frappe.new_doc('Period Closing Voucher')
			doc.transaction_date = str(self.to_date)
			doc.posting_date = str(self.to_date)
			doc.fiscal_year = str(self.to_date)[0:4]
			doc.closing_type = 'CBS Closing'
			doc.save(ignore_permissions=True)
			doc.submit()
			voucher_no = doc.name
			self.db_set('period_closing_voucher', voucher_no)

		for gl_code in cur_data:
			if str(gl_code)[:1] not in ('1','2','3','4'):
				_prepare_log(log, 'Info', 'GL Series ignored', gl_code, cur_data[gl_code]["ALL"]["LCY"])
				continue
			elif gl_code in set(fa_accounts):
				_prepare_log(log, 'Info', 'Balances for Fixed Asset GLs are ignored', gl_code, cur_data[gl_code]["ALL"]["LCY"])
				continue
			elif gl_code not in set(accounts):
				_prepare_log(log, 'Info', 'GLs missing in ERP', gl_code, cur_data[gl_code]["ALL"]["LCY"])
				continue
			else:
				prev_rec = prev_data.get(gl_code)
				if not prev_rec:
					gl_rec = self.get_gl_balance(accounts[gl_code].get('name'), self.to_date)
					prev_rec = gl_rec.get(gl_code) if gl_rec.get(gl_code) else {}
				for branch in set(cur_data[gl_code]):
					if branch not in set(branches):
						if branch in ('ALL', '8888', '9999'):
							if branch != "ALL":
								_prepare_log(log, 'Info', 'Branch Codes ignored', branch, cur_data[gl_code][branch]["LCY"])
							continue
						else:
							if flt(cur_data[gl_code][branch]['LCY']) or flt(cur_data[gl_code][branch]['FCY']):
								_prepare_log(log, 'Info', 'Branch Codes missing in ERP', branch, cur_data[gl_code][branch]["LCY"])
							continue

					if prev_rec.get(branch):
						prev_balance = flt(prev_rec[branch].get('LCY'),2)
						prev_balance_in_account_currency = flt(prev_rec[branch].get('FCY'),2)
					else:
						prev_balance = 0
						prev_balance_in_account_currency = 0

					cur_balance = flt(cur_data[gl_code][branch].get('LCY'),2)
					cur_balance_in_account_currency = flt(cur_data[gl_code][branch].get('FCY'),2)
	
					debit = 0
					credit = 0
					debit_in_account_currency = 0
					credit_in_account_currency = 0
					if prev_balance != cur_balance:
						if flt(cur_balance-prev_balance) < 0:
							debit = abs(flt(cur_balance-prev_balance))
							total_debit += debit
						else:
							credit = abs(flt(cur_balance-prev_balance))
							total_credit += credit
						if flt(cur_balance_in_account_currency-prev_balance_in_account_currency) < 0:
							debit_in_account_currency = abs(flt(cur_balance_in_account_currency-prev_balance_in_account_currency))
						else:
							credit_in_account_currency = flt(cur_balance_in_account_currency-prev_balance_in_account_currency)
					else:
						# _prepare_log(log, 'Info', 'No change in Balances', gl_code, cur_data[gl_code])
						continue

					gl_name = make_autoname('GLD.YY.MM.DD.######')
					
					gl_list.append((
						gl_name, str(self.to_date), accounts[gl_code].get('name'), branches[branch].get('cost_center'), 
						debit, credit, accounts[gl_code].get('account_currency'), debit_in_account_currency, credit_in_account_currency,
						voucher_type, voucher_no, remarks, self.company, 'Common',
						frappe.session.user, str(get_datetime()), frappe.session.user, str(get_datetime()), 1, 0, 'No', 'No',
						get_datetime(self.to_date).strftime('%Y'), 0
					))
					# _prepare_log(log, 'Info', 'GL Entries created', gl_code, credit-debit)

		self.db_set('total_debit', total_debit)
		self.db_set('total_credit', total_credit)
		self.make_gl_entries(gl_list)
		self.create_log(log)

	def make_gl_entries(self, gl_list):
		''' creating GL Entries in most optimized way '''
		if not gl_list:
			return
		values = ', '.join(map(str, gl_list))
		frappe.db.sql("""INSERT INTO `tabGL Entry`(name, posting_date, account, cost_center, 
					debit, credit, account_currency, debit_in_account_currency, credit_in_account_currency, 
					voucher_type, voucher_no, remarks, company, business_activity, 
					owner, creation, modified_by, modified, docstatus, idx, is_opening, is_advance, 
					fiscal_year, use_cheque_lot)
				VALUES {}""".format(values))

	def create_log(self, logs):
		''' create logs that occured during Download '''
		self.reload()
		for log_title, log in logs.items():
			total_debit, total_credit = 0, 0
			row = self.append('logs', {})
			row.log_type = log.log_type
			row.log_title= log_title
			row.log_count = len(set(log.details))

			if log.details:
				for i in log.details:
					if flt(log.details[i]) <= 0:
						total_debit  += flt(log.details[i])
					else:
						total_credit += flt(log.details[i])
			row.total_debit  = abs(total_debit)
			row.total_credit = abs(total_credit)
			row.details  = json.dumps(list(set(log.details)))
			row.save(ignore_permissions=True)

	def get_previous_data(self):
		''' get previous balance from CBS Entry for Download '''
		prev = frappe.db.sql("""select download_json
					from `tabCBS Entry`
					where entry_type = 'Download'
					and entry_time < '{}'
					and docstatus = 1
				order by entry_time desc limit 1""".format(self.entry_time), as_dict=True)
		return prev[0].download_json if prev else {}

	def get_branches(self):
		''' get branches for Download '''
		blist = frappe.db.sql("""select * from `tabBranch`
					where cost_center is not null and branch_code is not null
					and is_main_branch = 1""", as_dict=True)
		branches = frappe._dict()
		for i in blist:
			branches.setdefault(i.branch_code[:4], i)
		return branches

	def get_gl_balance(self, account, posting_date):
		''' get GL Balances from ERP for Download'''
		blist = frappe.db.sql("""SELECT a.account_number, a.account_currency, 
                        	substr(b.branch_code,1,4) branch_code,
							SUM((CASE WHEN a.report_type = "Profit and Loss"
								THEN (CASE WHEN YEAR(gl.posting_date) = YEAR("{posting_date}")
										THEN gl.credit-gl.debit ELSE 0 END)
								ELSE gl.credit-gl.debit
							END)) AS balance,
							SUM((CASE WHEN a.report_type = "Profit and Loss"
								THEN (CASE WHEN YEAR(gl.posting_date) = YEAR("{posting_date}")
										THEN gl.credit_in_account_currency-gl.debit_in_account_currency ELSE 0 END)
								ELSE gl.credit_in_account_currency-gl.debit_in_account_currency
							END)) AS balance_in_account_currency
						FROM `tabAccount` a, `tabGL Entry` gl, `tabBranch` b
						WHERE a.name = "{account}" 
						AND gl.account = a.name
						AND gl.posting_date <= "{posting_date}"
						AND b.cost_center = gl.cost_center
					GROUP BY a.account_number, a.account_currency, SUBSTR(b.branch_code,1,4)""".format(account=account, posting_date=posting_date), as_dict=True)

		bal = frappe._dict()
		for i in blist:
			bal.setdefault(str(i.account_number).strip(), frappe._dict()).setdefault(i.branch_code, frappe._dict()).setdefault('LCY', i.balance)
			bal.setdefault(str(i.account_number).strip(), frappe._dict()).setdefault(i.branch_code, frappe._dict()).setdefault('FCY', i.balance_in_account_currency)
		return bal

	def get_accounts(self):
		''' get accounts for Download '''
		ac_list = frappe.db.sql("""select * from `tabAccount` 
                          where ifnull(account_number,'') != ''
                          order by account_number""", as_dict=True)
		accounts = frappe._dict()
		for i in ac_list:
			accounts.setdefault(str(i.account_number).strip(), i)
		return accounts

	def get_fixed_asset_accounts(self):
		''' get Fixed Asset accounts from Asset Category Account for Download '''
		fa_list = frappe.db.sql("""select * from `tabAccount` a
					where ifnull(account_number,'') != ''
					and exists(select 1
						from `tabAsset Category Account` aca
						where aca.fixed_asset_account = a.name
						or aca.accumulated_depreciation_account = a.name
						or aca.depreciation_expense_account = a.name
						or aca.credit_account = a.name)
					order by a.account_number""", as_dict=True)
		accounts = frappe._dict()
		for i in fa_list:
			accounts.setdefault(str(i.account_number).strip(), i)
		return accounts

@frappe.whitelist()
def make_cbs_entry(entry_title, from_date, to_date, transaction_list):
	transaction_list = json.loads(transaction_list)
	final_list = frappe._dict()
	
	for i in set(transaction_list):
		voucher_type, voucher_no = i.split("||")
		final_list.setdefault(voucher_type, []).append(voucher_no)

	if final_list:
		doc = frappe.new_doc("CBS Entry")
		doc.entry_type = "Upload"
		doc.entry_title = entry_title
		doc.from_date = from_date
		doc.to_date = to_date
		doc.via_upload_report = 1
		doc.reference_list = json.dumps(final_list)
		doc.save(ignore_permissions=True)
		doc.reload()
		doc.get_data_for_upload()
		doc.save(ignore_permissions=True)
		doc.reload()
		return doc.name
	return

def get_rows_from_xls_file(filename):
	_file = frappe.get_doc("File", {"file_name": filename})
	filepath = _file.get_full_path()
	import xlrd
	book = xlrd.open_workbook(filepath)
	sheets = book.sheets()
	rows = []
	for row in range(1, sheets[0].nrows):
		row_values = []
		for col in range(1, sheets[0].ncols):
			row_values.append(sheets[0].cell_value(row, col))
		rows.append(row_values)
	return rows

def get_transaction_entries(file_url):
	rows = []

	if (file_url.lower().endswith("xlsx")):
		from frappe.utils.xlsxutils import read_xlsx_file_from_attached_file
		rows = read_xlsx_file_from_attached_file(file_url=file_url)
	elif (file_url.lower().endswith("csv")):
		from frappe.utils.csvutils import read_csv_content
		_file = frappe.get_doc("File", {"file_url": file_url})
		filepath = _file.get_full_path()
		with open(filepath,'rb') as csvfile:
			rows = read_csv_content(csvfile.read())
	elif (filename.lower().endswith("xls")):
		filename = file_url.split("/")[-1]
		rows = get_rows_from_xls_file(filename)
	else:
		frappe.throw(_("Only .csv and .xlsx files are supported currently"))

	return rows	

