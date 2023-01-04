from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import msgprint
from frappe.utils import flt, cint
from frappe.utils.data import get_first_day, get_last_day, add_years

def check_hire_end():
	all_doc = frappe.db.sql("select a.equipment, (select b.branch from `tabEquipment` b where b.name = a.equipment) as branch, a.equipment_number, c.customer, a.to_date from `tabHiring Approval Details` a, `tabEquipment Hiring Form` c where c.docstatus = 1 and c.name = a.parent and a.to_date = DATE_ADD(CURDATE(), INTERVAL 2 DAY)", as_dict=True)	
	all_data = {}
	for a in all_doc:
		if all_data.has_key(a.branch):
			row = "<tr><td>" + str(a.equipment) + "</td><td>" + str(a.equipment_number) + "</td><td>" + str(a.to_date) + "</td><td>" + str(a.customer) + "</td></tr>"  
			all_data[a.branch] += str(row)
		else:
			row = "<tr><td>" + str(a.equipment) + "</td><td>" + str(a.equipment_number) + "</td><td>" + str(a.to_date) + "</td><td>" + str(a.customer) + "</td></tr>"  
			all_data[a.branch] = row;

	for d in all_data:
		mails = frappe.db.sql("select email from `tabBranch Fleet Manager Item` where parent = %s", d, as_dict=True)
		for a in mails:
			message = "The following equipments hire date will end in 2 days: <br /><table><tr><td>Equipment</td><td>Equipment #</td><td>End Date</td><td>Customer</td></tr>"
			message += all_data[d]
			message += "</table>"
			try:
				frappe.sendmail(recipients=a.email, sender=None, subject="Hire End Notification", message=message)
			except:
				pass

def get_without_fuel_hire(equipment, posting_date, posting_time):
	records = frappe.db.sql("select a.customer_cost_center as cc, a.customer_branch as br from `tabHiring Approval Details` b, `tabEquipment Hiring Form` a where a.name = b.parent and a.private = 'Own Company' and b.equipment = %s and b.rate_type = 'Without Fuel' and %s between concat(b.from_date, ' ', b.from_time) and concat(b.to_date, ' ', b.to_time) and a.docstatus = 1", (equipment, str(posting_date) + " " + str(posting_time)), as_dict=True)
	return records 

def get_equipment_ba(equipment):
	doc = frappe.get_doc("Equipment", equipment)
	if not doc.business_activity:
		frappe.throw("Equipment is not assigned to any Business Activity")
	return doc.business_activity	

