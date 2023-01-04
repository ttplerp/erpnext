# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe

def execute(filters=None):
	columns = get_columns(filters)
	data = get_data(filters)

	return columns, data

def get_columns(filters):
	if filters.uinput == "Occupied":
		cols = [
			("Equipment") + ":Link/Equipment:120",
			("Customer") + ":Data:120",
			("From Date")+ ":Data:100",
			("To Date") + ":Data:120",
			("Place") + ":Data:120"
		]
	else:
		cols = [
			("Equipment") + ":Link/Equipment:120",
			("Equipment Number") + ":Data:120"
		]

	return cols

def get_data(filters):
	branch = ''
	if filters.get("branch"):
                branch = " and eh.branch =  '{0}'".format(filters.get("branch"))
	else: 
		brach = " eh.branch = eh.branch"

        if filters.get("from_date") and filters.get("to_date"):
                eh_cond = " and (('{1}' between eh.from_date and ifnull(eh.to_date, now())) or ('{1}' between eh.from_date and ifnull(eh.to_date, now())))".format(filters.get("from_date"), filters.get("to_date"))


	if filters.uinput == "Occupied":
		query ="""select e.name, (select h.customer FROM `tabEquipment Hiring Form` h WHERE h.name = r.ehf_name) AS customer, r.from_date, r.to_date, r.place FROM tabEquipment AS e, `tabEquipment History` eh,  `tabEquipment Reservation Entry` AS r WHERE 
	e.name = eh.parent and e.name = r.equipment  %(cond)s  and (r.to_date BETWEEN  \'%(to_date)s\'  AND  \'%(from_date)s\' OR r.from_date BETWEEN \'%(from_date)s\' AND \'%(to_date)s\')""" % {"from_date": str(filters.from_date), "to_date": str(filters.to_date), "cond": eh_cond}

	if filters.uinput == "Free":
		query = "select distinct e.name, e.equipment_number from tabEquipment e, `tabEquipment History` eh where NOT EXISTS (" + """select r.equipment FROM `tabEquipment Reservation Entry` AS r WHERE e.name=r.equipment and e.name = eh.parent  %(cond)s  %(bran)s  and (r.to_date BETWEEN \'%(to_date)s\' AND \'%(from_date)s\' OR r.from_date BETWEEN \'%(from_date)s\' AND \'%(to_date)s\'))""" % {"from_date": str(filters.from_date), "to_date": str(filters.to_date), "cond": eh_cond, "bran": branch}

	if filters.get("branch"):
		query += " and eh.branch = \'" + str(filters.branch) + "\'"

	if filters.get("equipment_type"):
		query += " and e.equipment_type = \'" + str(filters.equipment_type) + "\'"
	return frappe.db.sql(query, debug =1)
