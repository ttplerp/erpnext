# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class RentalFocalandAgency(Document):
	def validate(self):
		self.validate_active_focal()
		""" duplicate agency assignmet """
		for d in self.get('items'):
			rfa_name = frappe.get_value("Rental Focal and Agency Item", {"dzongkhag": d.dzongkhag, "ministry_and_agency": d.ministry_and_agency, "parent": ('!=', self.name)}, "parent")
			if rfa_name and frappe.get_value("Rental Focal and Agency", rfa_name, "is_active"):
				frappe.throw("Row# {}, <b>{}</b> - <b>{}</b> is already assigned through {}".format(d.idx, d.dzongkhag, d.ministry_and_agency, frappe.get_desk_link("Rental Focal and Agency", rfa_name)))
	
	def validate_active_focal(self):
		if not self.is_active:
			return
		
		for d in frappe.db.get_all("Rental Focal and Agency", {"rental_focal": self.rental_focal, "is_active": 1, "name": ("!=", self.name)}):
			frappe.throw("There is another {}, active with Rental Focal {}".format(frappe.get_desk_link("Rental Focal and Agency", d.name), self.rental_focal))