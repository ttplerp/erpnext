# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
	data = get_data(filters)
	# if filters.report_type == "Labour Cost Details":
	columns = get_columns(filters)
	return columns, data

def get_columns(filters):
	columns = []
	if filters.report_type == "Labour Cost Details":
		columns = [
			_("Project") + ":Data:250", 
			_("Labor Type") + ":Data:150",
			_("Type") 	+ ":Data:120", 
			_("Nos") 	+ ":Data:120",
			_("Hrs") 	+ ":Float:100", 
			_("Wages") 	+ ":Float:100", 
			_("Amount") + ":Currency:150", 
			_("Description of works") + ":Data:250" 
			
		]
	elif filters.report_type == "Machinaries and Equipment":
		columns = [
			_("Equipment Type") + ":Data:250",
			_("Equipment Name") + ":Data:250",  
			_("Hours") 	+ ":Float:100", 
			_("Rate") 	+ "::100", 
			_("Amount") + ":Currency:150"
		]
	elif filters.report_type == "Material Consumption":
		columns = [
			_("Material Code") + ":Link/Item:250",
			_("Material Name") + ":Data:250",  
			_("Quantity") 	+ ":Float:100", 
			_("Uom") 	+ "::100", 
			_("Rate") 	+ "::100", 
			_("Amount") + ":Currency:150"
		]
	return columns

def get_data(filters):
	cond = ""
	if filters.project:
		cond = "AND mre.project='{0}'".format(filters.project)
	if filters.report_type == "Labour Cost Details":
		reqular = """
			SELECT
				mre.project,
				mre.muster_roll_type as labor_type,
				"Regular Time" as type,
				count(mre.name) nos,
				8 as hrs, 
				(mre.rate_per_day / 8) as wages,
				(count(mre.name) * 8 * (mre.rate_per_day / 8)) as amount
			FROM 
				`tabMuster Roll Employee` mre, `tabMuster Roll Attendance` mra
			WHERE
				mre.status = 'Active' and
				mre.name = mra.mr_employee 
				AND mra.date = '{0}' {1}
				AND mra.status = 'Present'
				GROUP BY 
					mre.rate_per_hour 
				ORDER BY 
					mre.muster_roll_type
		""".format(filters.date, cond)
		data = frappe.db.sql(reqular, as_dict=1)
		ot = """
			SELECT 
				mre.project,
				mre.muster_roll_type as labor_type,
				"Over Time" as type,
				count(mre.name) nos,
				mroe.number_of_hours as hrs,
				mre.rate_per_hour as wages,
				(count(mre.name) * mroe.number_of_hours * mre.rate_per_hour) as amount
			FROM 
				`tabMuster Roll Employee` mre, 
				`tabMuster Roll Overtime Entry` mroe
			WHERE
				mre.status = 'Active' 
				AND mre.name = mroe.mr_employee 
				AND mroe.docstatus = 1 
				AND mroe.date = '{0}' {1}
				GROUP BY 
					mre.rate_per_hour, 
					mroe.number_of_hours
				ORDER BY 
					mre.muster_roll_type;
		""".format(filters.date, cond)
		ot_result = frappe.db.sql(ot, as_dict=1)
		if ot_result:
			for i in ot_result:
				data.append(i)

	if filters.report_type == "Machinaries and Equipment":
		equipment = """
			SELECT
				eq.equipment_type,
				eq.equipment_name, 
				lbi.hours,
				ehf.hiring_rate as rate,
				(lbi.hours * ehf.hiring_rate) as amount
			FROM `tabEquipment` eq,
				`tabLogbook` lb,
				`tabLogbook Item` lbi,
				`tabEHF Rate` ehf
			WHERE  eq.name=lb.equipment and
				lbi.equipment = lb.equipment
				and lb.equipment_hiring_form = ehf.parent 
				and lb.posting_date = '{}';
			""".format(filters.date)
		data = frappe.db.sql(equipment, as_dict=1)
	if filters.report_type == "Material Consumption":
		equipment = """
			SELECT
				eq.equipment_type,
				eq.equipment_name, 
				lbi.hours,
				ehf.hiring_rate as rate,
				(lbi.hours * ehf.hiring_rate) as amount
			FROM `tabStock Entry` se,
				`tabStock Entry Detail` sed
			WHERE  se.name=sed.parent and
				se.docstatus = 1
				and se.posting_date = '{}';
			""".format(filters.date)
		data = frappe.db.sql(equipment, as_dict=1)
	return data