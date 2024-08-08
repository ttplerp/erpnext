# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class TreasuryMapping(Document):
	def validate(self):
		self.check_for_duplicate_schedule_entries()
		self.check_duplicate_party_entries()

	def check_for_duplicate_schedule_entries(self):
		financial_schedules = set()
		for d in self.accounts_mapping:
			if d.financial_schedule in financial_schedules:
				frappe.throw('Duplicate entries found for financial schedule: <b>{}</b>'.format(d.financial_schedule))
			financial_schedules.add(d.financial_schedule)
	
	def check_duplicate_party_entries(self):
		if frappe.db.exists("Treasury Mapping", {"party_type": self.party_type, "party": self.party, "name": ["!=", self.name]}):
			frappe.throw('Duplicate entries found for party: <b>{0}</b> and party type: <b>{1}</b>'.format(self.party, self.party_type))
