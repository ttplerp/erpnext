# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import requests, json
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime
from erpnext.custom_utils import check_future_date
from erpnext.integrations.bank_api import fetch_balance
from erpnext.accounts.doctype.bank_payment.bank_payment import get_transaction_id

class TaxPayment(Document):
	def validate(self): 
		check_future_date(self.posting_date)
		self.validate_outstanding()
		self.get_bank_available_balance()
		self.update_status()

	def before_submit(self):
		self.update_status()

	def on_submit(self):
		self.pi_number = get_transaction_id()

	def on_cancel(self):
		self.update_status()

	def validate_outstanding(self):
		if self.outstanding_amount <= 0:
			frappe.throw("Payment cannot be processed as the outstanding amount is zero.")

	def update_status(self):
		status = {0: "Draft", 1: "Pending", 2: "Cancelled"}[self.docstatus]
		if self.docstatus == 2:
			self.db_set("status", "Cancelled")
			self.db_set("workflow_state", "Cancelled")
		self.status = status

	def get_bank_available_balance(self):
		if self.bank_account and frappe.db.get_value('Bank Payment Settings', "BOBL", 'enable_one_to_one'):
			try:
				result = fetch_balance(self.bank_account)
			except Exception as e:
				frappe.msgprint(_("Unable to fetch Bank Balance.\n  {}").format(str(e)))
			else:
				if result['status'] == "0":
					self.bank_balance = result['balance_amount']
				else:
					frappe.msgprint(_("Unable to fetch Bank Balance.\n  {}").format(result['error']))

	@frappe.whitelist()
	def process_payment(self):
		if self.status != "Pending":
			frappe.msgprint(_("Only transactions in Pending status can be processed"))
			return
		
		if self.outstanding_amount > 0 and not self.payment_status_code:
			api_name = "Utility Payment - Payments"
			url = "http://10.40.40.70:6969/mfmbs/paymentfromcorporate"
			service_id = '1215'
			service_type = "RRCOTax"
			consumer_field = "RRCOTaxCode"

			os = str(self.outstanding_amount)
			if os.count("."):
				os_nu = os.split(".",1)[0]
				os_ch = os.split(".",1)[1]
				os_ch = os_ch if len(os_ch) > 1 else str(os_ch)+"0"
				actual_os = str(os_nu)+"."+str(os_ch)
			else:
				actual_os = str(os)

			api_param = {
				'USERID': 'k/2hOY+lcyyteFTNISyXYg==', 
				'PWD': 'CCPztRtsxj5g8DjvV7bkKQ==', 
				'CORP_KEY': 'NH', 
				'serviceid': service_id, 
				'servicetype': service_type, 
				'FrmAcctNum': self.bank_ac_no,
				'Amt': str(actual_os),
				'pi': self.pi_number
			}

			api_param[consumer_field] = str(self.dv_number)
			payload = json.dumps(api_param)
			self.request = str(payload)
			headers = {
				'Content-Type': 'application/json'
			}

			response = requests.request("POST", url, headers=headers, data=payload)
			details = response.json()
			self.response = str(details)
			res_status = details['statusCode']
			self.payment_status_code = res_status

			status = None
			if res_status == "00":
				self.payment_response_msg = details['ResultMessage']
				self.payment_journal_no = details['jrnlno']
				status = "Payment Successful"
			else:
				self.payment_response_msg = details['ErrorMessage']
				status = "Payment Failed"

			# Update status
			if status:
				self.db_set("status", status)
				self.db_set("workflow_state", status)
				self.reload()

			if self.tds_remittance:
				doc = frappe.get_doc("TDS Remittance", self.tds_remittance)
				doc.payment_status = status
				doc.tax_payment = self.name
				doc.save(ignore_permissions=True)

	@frappe.whitelist()
	def get_outstanding_amount(self):
		api_name = "Utility Payment - Outstanding Fetch"
		url = "http://10.40.40.70:6969/mfmbs/amountfetchfromcorporate" 
		service_id = '1215'
		service_type = "RRCOTax"
		# consumer_field = "RRCOTaxCode"

		api_param = {
			'USERID': 'k/2hOY+lcyyteFTNISyXYg==', 
			'PWD': 'CCPztRtsxj5g8DjvV7bkKQ==', 
			'CORP_KEY': 'NH', 
			'SERVICEID': service_id, 
			'SERVICETYPE': service_type, 
			'RRCOTaxCode': self.dv_number
		}
			
		payload = json.dumps(api_param)
		headers = {
			'Content-Type': 'application/json'
		}

		response = requests.request("POST", url, headers=headers, data=payload)
		details = response.json()
		res_status = details['statusCode']
		if res_status == "00":
			self.outstanding_amount = details['ResultMessage']
			self.response_msg = "Success"
		elif res_status == "01":
			self.response_msg = details['ErrorMessage']
			self.outstanding_amount = 0
		self.outstanding_datetime = now_datetime()
		self.fetch_status_code = res_status