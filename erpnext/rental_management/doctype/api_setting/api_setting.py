# Copyright (c) 2023, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import requests, json
import base64

class APISetting(Document):
	def validate(self):
		pass

	@frappe.whitelist()
	def generate_token(self):
		bearer_token = self.generate_bearer_token()
		if bearer_token:
			self.db_set("bearer_token", bearer_token)
	
	def generate_bearer_token(self):
		url = self.url
		username=self.username
		password=self.get_password()
		
		credentials = f'{username}:{password}'
		encoded_credentials = credentials.encode('utf-8')
		base64_credentials = base64.b64encode(encoded_credentials).decode('utf-8')

		headers = {
			'Authorization': f'Basic {base64_credentials}',
			'Content-Type': 'application/x-www-form-urlencoded',
		}

		data = {
			'grant_type': 'client_credentials',
		}

		response = requests.post(url, headers=headers, data=data)

		if response.status_code == 200:
			token = response.json().get('access_token')
			return token
		else:
			frappe.throw(f"Failed to generate bearer token. Status code: {response.status_code}")
			return None

@frappe.whitelist(allow_guest=True)
def get_cid_detail(cid=None):
	data=None
	doc = frappe.get_doc("API Setting Item", {"parent":"API-2023-313", "api_name":"Citizen Detail"})
	url = doc.api_url + str(cid)
	payload={}
	doc = frappe.get_doc("API Setting", "API-2023-313")
	bearer_token = 'Bearer ' + doc.generate_bearer_token()
	headers = {
	'Authorization': str(bearer_token)
	}
	response = requests.request("GET", url, headers=headers, data=payload)
	data = response.json()
	data = data['citizendetails']['citizendetail'][0] if data['citizendetails'] else data['citizendetails']
	return data


@frappe.whitelist(allow_guest=True)
def get_civil_servant_detail(cid=None):
	data=None
	dtl={}

	doc = frappe.get_doc("API Setting", "API-2023-313")
	bearer_token = 'Bearer ' + doc.generate_bearer_token()
	headers = {
	'Authorization': str(bearer_token)
	}
	payload={}
	
	#Civil Servant Detail
	doc = frappe.get_doc("API Setting Item", {"parent":"API-2023-313", "api_name":"Civil Servant Detail"})
	url = doc.api_url + str(cid)
	response = requests.request("GET", url, headers=headers, data=payload)
	data = response.json()
	data = data['employeedetails']['employeedetail'][0] if data['employeedetails'] else data['employeedetails']

	#Salary Detail of the Civil Servant
	doc1 = frappe.get_doc("API Setting Item", {"parent":"API-2023-313", "api_name":"ePEMS"})
	url = doc1.api_url + str(cid)
	response = requests.request("GET", url, headers=headers, data=payload)
	data1 = response.json()
	data1 = data1['epemsEmployeeDetails']['epemsEmployeeDetail'][0] if data1['epemsEmployeeDetails'] else data1['epemsEmployeeDetails']

	#Merge Civil Servant detail and Salary Detail
	dtl = data | data1

	return dtl