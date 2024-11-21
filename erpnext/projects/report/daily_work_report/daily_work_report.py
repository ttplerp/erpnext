# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, getdate, cint, today, add_years, date_diff, nowdate

def execute(filters=None):
	today = nowdate()
	if filters.date:
		if getdate(filters.date) != getdate(today):
			frappe.throw(_("You cannot enter a date in the past or future. Please select the current date."))

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
	elif filters.report_type == "Machinery and Equipment":
		columns = [
			_("Project") + ":Link/Project:250",
			_("Cost Center") + ":Link/Cost Center:250",
			_("Equipment") + ":Link/Equipment:120",
			_("Hours") + ":Data:80",  
			_("Rate") 	+ "::100", 
			_("Amount") + ":Currency:120",
			_("Description") + ":Data:250",
		]
	elif filters.report_type == "Material Consumption":
		columns = [
			{"label": _("Material Code"), "fieldname": "item_code", "fieldtype": "Link", "options":"Item", "width": 150},
			{"label": _("Material Name"), "fieldname": "item_name", "fieldtype": "Data", "width": 150},
			{"label": _("Material Group"), "fieldname": "item_group", "fieldtype": "Link", "options":"Item Group", "width": 150},
			{"label": _("Quantity"), "fieldname": "qty", "fieldtype": "Data", "width": 80},
			{"label": _("UOM"), "fieldname": "uom", "fieldtype": "Data", "width": 80},
			{"label": _("Rate"), "fieldname": "rate", "fieldtype": "Currency", "width": 80},
			{"label": _("Amount"), "fieldname": "amount", "fieldtype": "Currency", "width": 120},
		]
	elif filters.report_type == "Expenditure of Project Implementation Unit":
		columns = [
			{"label": _("Employee"), "fieldname": "employee", "fieldtype": "Link", "options":"Employee", "width": 250},
			{"label": _("Employee Name"), "fieldname": "employee_name", "fieldtype": "Data", "width": 150},
			{"label": _("Designation"), "fieldname": "designation", "fieldtype": "Link", "options":"Designation", "width": 200},
			{"label": _("Cost Center"), "fieldname": "cost_center", "fieldtype": "Link", "options":"Cost Center", "width": 150},
			{"label": _("Daily Rate"), "fieldname": "daily_rate", "fieldtype": "Currency", "width": 150},
			{"label": _("Basic Pay"), "fieldname": "basic_pay", "fieldtype": "Currency", "width": 150},
			{"label": _("Date of joining"), "fieldname": "date_of_joining", "fieldtype": "Date", "width": 150},
		]
	elif filters.report_type == "Expenditure for Mess":
		columns = [
			{"label": _("Project"), "fieldname": "project", "fieldtype": "Link", "options":"Project", "width": 250},
			{"label": _("Cost Center"), "fieldname": "cost_center", "fieldtype": "Link", "options":"Cost Center", "width": 250},
			{"label": _("Head Count (Day)"), "fieldname": "head_count", "fieldtype": "Data", "width": 150},
			{"label": _("Rate"), "fieldname": "rate_per_head", "fieldtype": "Currency", "width": 120},
			{"label": _("Amount"), "fieldname": "amount", "fieldtype": "Currency", "width": 150},
		]
	elif filters.report_type == "HSD Issued Details":
		columns = [
			_("Project") + ":Link/Project:250",
			_("Cost Center") + ":Link/Cost Center:250",
			_("Equipment") + ":Link/Equipment:120",
			_("Material Code") + ":Link/Item:120",
			_("Material Name") + ":Data:250",
			_("Quantity") 	+ ":Float:100", 
			_("Uom") 	+ "::100", 
			_("Rate") 	+ "::100", 
			_("Amount") + ":Currency:150"
		]
	return columns

def get_data(filters):
	data = []
	cond = ""
	if filters.project:
		cond += "AND mre.project='{0}'".format(filters.project)
	if filters.cost_center:
		cond += "AND mre.cost_center='{0}'".format(filters.cost_center)
	if filters.mr_type:
		cond += "AND mre.muster_roll_type='{0}'".format(filters.mr_type)

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

	if filters.report_type == "Machinery and Equipment":
		cond = ""
		if filters.cost_center:
			cond = "AND t1.cost_center='{0}'".format(filters.cost_center)
		equipments = """
			SELECT
				t1.project,
				t1.cost_center,
				t2.equipment,
				sum(t2.hours) as hours,
				t2.rate, 
				sum(t2.amount) as amount
			FROM `tabProject Equipment Engagement` t1, `tabProject Equipment Engagement Item` t2
			WHERE t1.docstatus = 1
				and t1.name = t2.parent
				and t1.posting_date = '{}' {}
			GROUP BY t1.cost_center, t2.equipment, t2.rate
			""".format(filters.date, cond)
		data = frappe.db.sql(equipments, as_dict=1)

	if filters.report_type == "Material Consumption":
		cond = ""
		if filters.cost_center:
			cond += "AND sed.cost_center='{0}'".format(filters.cost_center)
		equipment = """
			SELECT
				sed.item_code,
				sed.item_name, 
				se.item_group, 
				sed.qty,
				sed.uom,
				sed.basic_rate as rate,
				sed.amount
			FROM `tabStock Entry` se,
				`tabStock Entry Detail` sed
			WHERE  se.name=sed.parent and
				se.docstatus = 1
				and se.posting_date = '{}' {}
			""".format(filters.date, cond)
		data = frappe.db.sql(equipment, as_dict=True)
	
	if filters.report_type == "Expenditure for Mess":
		cond = ""
		if filters.project:
			cond += " and project = '{}'".format(filters.project)
		if filters.cost_center:
			cond += " and cost_center = '{}'".format(filters.cost_center)
		query = """
				select 
					project,
					cost_center,
					head_count,
					rate_per_head,
					amount
				from
					`tabProject Mess Management`
				where docstatus = 1
				and posting_date = '{}' {}
				""".format(filters.date, cond)
		data = frappe.db.sql(query, as_dict=True)

	if filters.report_type == "HSD Issued Details":
		cond = ""
		if filters.cost_center:
			cond = "AND t1.cost_center='{0}'".format(filters.cost_center)
		query = """
				select 
					t1.project,
					t1.cost_center,
					t2.equipment,
					t1.pol_type as material_code,
					t1.item_name as material_name,
					t2.qty as quantity,
					t1.stock_uom as uom,
					t2.rate,
					t2.amount
				from `tabPOL Issue` t1, `tabPOL Issue Items` t2
				where t1.name = t2.parent
				and t1.docstatus = 1
				and t1.posting_date = '{}' {}
			""".format(filters.date, cond)
		data = frappe.db.sql(query, as_dict=True)

	if filters.report_type == "Expenditure of Project Implementation Unit":
		cond = ""
		if filters.cost_center:
			cond = "AND t1.cost_center='{0}'".format(filters.cost_center)
		query = """
					SELECT 
						t1.employee,
						t1.employee_name,
						t1.cost_center,
						t1.designation,
						t3.amount / 30 AS daily_rate,
						t3.amount as basic_pay,
						t1.date_of_joining
					FROM 
						`tabEmployee` t1
					JOIN 
						`tabSalary Structure` t2 ON t1.employee = t2.employee
					JOIN 
						`tabSalary Detail` t3 ON t2.name = t3.parent
					WHERE 
						t1.status = 'Active'
						AND t3.salary_component = 'Basic Pay' {}
				""".format(cond)
		data = frappe.db.sql(query, as_dict=True)
	return data