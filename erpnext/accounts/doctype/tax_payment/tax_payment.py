# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import requests, json
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, cint, getdate, get_datetime, get_url, nowdate, now_datetime, money_in_words
from erpnext.custom_utils import check_future_date
from erpnext.integrations.bank_api import fetch_balance
from erpnext.accounts.doctype.bank_payment.bank_payment import get_transaction_id

class TaxPayment(Document):
	def validate(self): 
		check_future_date(self.posting_date)
		self.get_bank_available_balance()

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