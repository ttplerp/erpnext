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
	bearer_token = doc.generate_bearer_token()
	headers = {
	'Authorization': 'Bearer {bearer_token}'
	}

	response = requests.request("GET", url, headers=headers, data=payload)
	return response
	
	'''
	print(response.text)
	data = {
			"citizendetails": {
				"citizendetail": [
					{
						"cidNumber": "10808003482",
						"firstissueDate": "16/11/2022",
						"gender": "F",
						"dob": "31/05/2022",
						"fatherName": "Thukten  Dendup",
						"firstName": "Kinley ",
						"middleName": "",
						"lastName": "Choden",
						"mobileNumber": null,
						"motherName": "Tshering  Pelden",
						"occupationDesc": "Dependent",
						"dzongkhagSerialno": "8",
						"gewogSerialno": "81",
						"gewogName": "Shaba",
						"permanentHouseno": "Nya-8-Nil/45",
						"permanentThramno": "1423 (SHA-2933)",
						"permanentVillageserialno": "1958",
						"permanentVillagename": "Shungkarna",
						"palceOfbirth": "H",
						"countryName": null,
						"firstNamebh": "ཀུན་ལེགས་ ཆོས་སྒྲོན།",
						"middleNamebh": null,
						"lastNamebh": null,
						"householdNo": "080800237",
						"dzongkhagName": "Paro"
					}
				]
			}
		}
	return data
	'''

