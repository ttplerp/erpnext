# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt

class Locations(Document):
	def autoname(self):
		""" generate id """
		if not self.dzongkhag:
			frappe.throw("Dzongkhag name is missing")
		if not frappe.db.get_value("Dzongkhag", self.dzongkhag, "rental_dzo_abbr"):
			frappe.throw("Dzongkhag Abbr is missing in Dzongkhag master")
		# dz = self.dzongkhag
		# dzo_prefix = dz[:3]
		abbr = frappe.db.get_value("Dzongkhag", self.dzongkhag, "rental_dzo_abbr")
		prefix = abbr.upper()
		
		self.name = "/".join([prefix, self.plot_no])
	
	def validate(self):
		# self.make_location_id()
		if not self.description:
			self.description = self.location
		""" Validate duplicate entry """
		# self.validate_luc_duplicate()
		self.validate_duplicate_item_entry()
		self.calc_total_prop_amount()
	
	def make_location_id(self):
		""" generate id """
		if not self.dzongkhag:
			frappe.throw("Dzongkhag name is missing")
		dz = self.dzongkhag
		dzo_prefix = dz[:3]
		prefix = dzo_prefix.upper()
		self.location_id = "/".join([prefix, self.luc_no])

	def calc_total_prop_amount(self):
		prop_mgt_amt = 0
		for a in self.get('property_management_item'):
			if a.is_percent == 1:
				a.amount = 0
			else:
				a.percent = 0
			
			prop_mgt_amt += flt(a.amount)
		self.total_property_management_amount = prop_mgt_amt

	def validate_duplicate_item_entry(self):
		data=[]
		for d in self.get('property_management_item'):
			if d.property_management_type not in data:
				data.append(d.property_management_type)
			else:
				frappe.throw("Duplicate data entry at #Row. {}".format(d.idx))

	# def validate_luc_duplicate(self):
	# 	for loc in frappe.db.get_all("Locations", {"luc_no": self.luc_no, "name": ("!=", self.name)}):
	# 		frappe.throw("Locaton {} already exist with LUC {}".format(frappe.get_desk_link("Locations", loc.name), self.luc_no))
