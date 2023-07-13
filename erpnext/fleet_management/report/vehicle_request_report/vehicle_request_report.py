# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _


def execute(filters=None):
	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data

def get_columns(filters):
	return [
		_("Branch")+":Link/Branch:150",
		_("Equipment Number")+":Data:140",
		_("Equipment Model")+":Data:140",
		_("Equipment Type")+":Link/Equipment Type:120",
		_("Avaliability")+":Data:120",
	]

def get_data(filters):
	if filters.from_date > filters.to_date :
		frappe.throw("From Date cannot be before than To Date")
	cond = ''
	# if filters.vehicle_type :
	# 	cond += " AND vehicle_type = '{}'".format(filters.vehicle_type)
	if filters.branch:
		cond += "and branch='{}'".format(filters.branch)
	
	return frappe.db.sql("""
		SELECT 
			e.branch,
			e.name,
			e.equipment_model,
			e.equipment_type,
			e.status
		FROM `tabEquipment` e 
		WHERE NOT EXISTS (
			select vr.vehicle 
			from `tabVehicle Request` vr
			where 
			e.name = vr.vehicle_number
			AND
			(vr.from_date BETWEEN '{0}' AND '{1}'
				OR vr.to_date BETWEEN '{0}' AND '{1}'
				OR '{0}' BETWEEN vr.from_date AND vr.to_date
				OR '{1}' BETWEEN vr.from_date AND vr.to_date
			))
			{2}
		""".format(filters.from_date, filters.to_date,cond))
