# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt, nowdate, money_in_words
from frappe.model.mapper import get_mapped_doc
from frappe.utils.data import add_years
from erpnext.custom_utils import check_uncancelled_linked_doc, check_future_date

class BreakDownReport(Document):
	def validate(self):
		check_future_date(self.date)
		self.validate_equipment()
		# self.calculate_km_diff()
		self.calculate_total()

	def on_submit(self):
		self.assign_reservation()
		self.post_equipment_status_entry()

	def on_cancel(self):
		check_uncancelled_linked_doc(self.doctype, self.name)
		frappe.db.sql("delete from `tabEquipment Reservation Entry` where ehf_name = \'"+str(self.name)+"\'")
		frappe.db.sql("delete from `tabEquipment Status Entry` where ehf_name = \'"+str(self.name)+"\'")
	
	def validate_equipment(self):
		if self.owned_by in ['Own Company', 'Own Branch']:
			eb = frappe.db.get_value("Equipment", self.equipment, "branch")
			if self.owned_by == "Own Branch" and self.branch != eb:
				frappe.throw("Equipment <b>" + str(self.equipment) + "</b> doesn't belong to your branch")
		else:
			self.equipment = ""

	def assign_reservation(self):
		if self.owned_by in ['Own Company', 'Own Branch']:
			doc = frappe.new_doc("Equipment Reservation Entry")
			doc.flags.ignore_permissions = 1 
			doc.equipment = self.equipment
			doc.reason = "Maintenance"
			doc.ehf_name = self.name
			doc.hours = 100
			doc.place = self.branch
			doc.from_date = self.date
			doc.from_time = self.time
			doc.to_date = add_years(self.date, 1)
			doc.submit()

	def post_equipment_status_entry(self):
		if self.owned_by in ['Own Company', 'Own Branch']:
			ent = frappe.new_doc("Equipment Status Entry")
			ent.flags.ignore_permissions = 1 
			ent.equipment = self.equipment
			ent.reason = "Maintenance"
			ent.ehf_name = self.name
			ent.hours = 100
			ent.place = self.branch
			ent.from_date = self.date
			ent.from_time = self.time
			ent.to_date = add_years(self.date, 1)
			ent.submit()
		
	def calculate_km_diff(self):
		previous_km_reading = frappe.db.sql("""
			SELECT 
				current_km
			FROM `tabBreak Down Report` 
			WHERE 
				equipment = '{}'
			AND
				docstatus = 1
			ORDER BY date DESC, time DESC
			limit 1;
		""".format(self.equipment),as_dict=True)
		pv_km = 0
		if previous_km_reading:
			pv_km = flt(previous_km_reading[0].current_km)

		if flt(pv_km) >= flt(self.current_km):
			frappe.throw("Current KM Reading cannot be less than Previous KM Reading for Equipment Number <b>{}</b>".format(self.equipment_number))
		self.km_difference = flt(self.current_km) - flt(pv_km)
	
	def calculate_total(self):
		total = 0
		for item in self.items:
			total += flt(item.charge_amount)
		self.total_amount = total
		
@frappe.whitelist()
def make_job_card(source_name, target_doc=None): 
	def update_date(obj, target, source_parent):
		target.posting_date = nowdate()
	
	doc = get_mapped_doc("Break Down Report", source_name, {
			"Break Down Report": {
				"doctype": "Job Card",
				"field_map": {
					"name": "job_card",
					"date": "break_down_report_date",
					"owned_by":"owned_by"
				},
				"postprocess": update_date,
				"validation": {"docstatus": ["=", 1]}
			},
		}, target_doc)
	return doc

@frappe.whitelist()
def fetch_previous_date(equipment,item_code):
	data = frappe.db.sql("""
		select 
			c.recent_maintenance_date,b.current_km
		from 
			`tabBreak Down Report` b inner join `tabJob Card Item` c on c.parent = b.name
		where 
			b.equipment = '{}' and b.docstatus = 1 and c.job = '{}'
		order by b.date desc, b.time desc limit 1
	""".format(equipment,item_code),as_dict=1)
	
	return  data

#Added by Sonam Chophel to update the job card status on august 03/08/2021
@frappe.whitelist()
def get_job_card_entry(doc_name):
	""" To check if job card exist for a particular break down report"""
	job_card_entry = """
		SELECT job_card
		FROM `tabBreak Down Report`
		WHERE name = '{name}' and docstatus = 1
	""".format(name=doc_name)
	
	job_card_entry = frappe.db.sql(job_card_entry, as_dict=1)
	
	if job_card_entry[0].job_card == None or job_card_entry[0].job_card == "":
		frappe.db.set_value("Break Down Report", doc_name, "job_card_status", "Job Card Not Created")
		return ("Job Card Not Created")
	else:
		frappe.db.set_value("Break Down Report", doc_name, "job_card_status", "Job Card Created")
		return ("Job Card Created")
