'''
--------------------------------------------------------------------------------------------------------------------------
Version		 	Author		  				CreatedOn		 	ModifiedOn		  	Remarks
------------ --------------- ------------------ -------------------  -----------------------------------------------------
1.0		      	Dawa Nyuehtyue Tshering		2024/11/21			2025/01/07			Original Version
--------------------------------------------------------------------------------------------------------------------------			
'''

import frappe
from frappe import _
from frappe.utils import flt, getdate, cint, today, add_years, date_diff, nowdate

def execute(filters=None):
	if filters.show_overall == 1:
		columns = get_overall_columns(filters)
		data = get_overall_data(filters)
	else:
		data = get_data(filters)
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
			{"label": _("Total Earning"), "fieldname": "total_earning", "fieldtype": "Currency", "width": 150},
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
	if filters.cost_center:
		cond += "AND mre.cost_center='{0}'".format(filters.cost_center)
	if filters.project:
		cond += "AND mre.project='{0}'".format(filters.project)

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
		if filters.project:
			cond = "AND t1.project='{0}'".format(filters.project)
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
		if filters.project:
			cond += "AND sed.project='{0}'".format(filters.project)
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
		if filters.project:
			cond += "AND t1.project='{0}'".format(filters.project)
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
		if filters.project:
			cond = "AND t1.project='{0}'".format(filters.project)
		query = """
					SELECT 
						t1.employee,
						t1.employee_name,
						t1.cost_center,
						t1.designation,
						t2.total_earning / 30 AS daily_rate,
						t2.total_earning as total_earning,
						t1.date_of_joining
					FROM 
						`tabEmployee` t1
					JOIN 
						`tabSalary Structure` t2 ON t1.name = t2.employee
					WHERE 
						t1.status = 'Active'
						{}
				""".format(cond)
		data = frappe.db.sql(query, as_dict=True)
	return data

def get_overall_columns(filters):
	return [
		{"fieldtype": "Link", "fieldname": "cost_center", "label": _("Cost Center"), "options": "Cost Center", "width": 200},
		{"fieldtype": "Link", "fieldname": "project", "label": _("Project"), "options": "Project", "width": 200},
		{"fieldtype": "Float", "fieldname": "equipment_machinary", "label": _("Equipment (Nu.)"), "width": 150},
		{"fieldtype": "Float", "fieldname": "hsd", "label": _("HSD (Nu.)"), "width": 150},
		{"fieldtype": "Float", "fieldname": "piu", "label": _("PIU (Nu.)"), "width": 150},
		{"fieldtype": "Float", "fieldname": "mess", "label": _("Mess (Nu.)"), "width": 150},
		{"fieldtype": "Float", "fieldname": "material", "label": _("Material (Nu.)"), "width": 150},
		{"fieldtype": "Data", "fieldname": "total_mr", "label": _("Total MR"), "width": 100},
		{"fieldtype": "Float", "fieldname": "labour_cost", "label": _("Labour (Nu.)"), "width": 150},
		{"fieldtype": "Float", "fieldname": "income", "label": _("Income (Nu.)"), "width": 150},    
		{"fieldtype": "Float", "fieldname": "expense", "label": _("Expense (Nu.)"), "width": 150},    
		{"fieldtype": "Float", "fieldname": "profit", "label": _("Profit (Nu.)"), "width": 150},    
	]

def get_overall_data(filters):
	data = []
	conditions, params = get_conditions(filters)

	project_list = fetch_query(
		f"""
		SELECT name, project_name, cost_center 
		FROM `tabProject` {conditions}
		""",
		params
	)

	for project in project_list:
		cost_center, project_name = project['cost_center'], project['name']

		equipment_machinary = get_equipment_machinary(cost_center, project_name, filters.date)
		hsd = get_hsd_details(cost_center, project_name, filters.date)
		piu = get_piu_details(cost_center, project_name)
		mess = get_mess_details(cost_center, project_name, filters.date)
		material = get_material_details(cost_center, project_name, filters.date)
		total_mr, labour_cost = get_labour_details(cost_center, project_name, filters.date)

		expense = sum([
			flt(equipment_machinary),
			flt(hsd),
			flt(mess),
			flt(piu),
			flt(material),
			flt(labour_cost)
		])
		income = flt(get_rom_details(cost_center, project_name, filters.date))
		profit = income - expense

		data.append({
			"project": project['name'],
			"project_name": project['project_name'],
			"cost_center": cost_center,
			"equipment_machinary": flt(equipment_machinary),
			"hsd": flt(hsd),
			"piu": flt(piu),
			"mess": flt(mess),
			"material": flt(material),
			"total_mr": total_mr,
			"labour_cost": flt(labour_cost),
			"income": income,
			"expense": expense,
			"profit": profit,
		})

	data.append(get_totals_row(data))
	return data


def get_conditions(filters):
	conditions = []
	params = {}

	if filters.get('project'):
		conditions.append("name = %(project)s")
		params["project"] = filters['project']
	if filters.get('cost_center'):
		conditions.append("cost_center = %(cost_center)s")
		params["cost_center"] = filters['cost_center']

	return ("WHERE " + " AND ".join(conditions)) if conditions else "", params

def fetch_query(query, params):
	try:
		return frappe.db.sql(query, params, as_dict=True)
	except Exception as e:
		frappe.log_error(message=str(e), title=_("Query Execution Failed"))
		return []

def get_totals_row(data):
	totals = {key: 0 for key in data[0].keys() if isinstance(data[0][key], (int, float))}
	for row in data:
		for key in totals.keys():
			totals[key] += flt(row[key])
	totals.update({
		"project": _("Total"),
		"cost_center": ""
	})
	return totals

def get_equipment_machinary(cost_center, project, date):
	return execute_query("""
		SELECT SUM(t2.amount) as total_amount
		FROM `tabProject Equipment Engagement` t1, `tabProject Equipment Engagement Item` t2
		WHERE t1.name = t2.parent AND t1.docstatus = 1 AND t1.cost_center = %s AND t1.project = %s AND t1.posting_date = %s
	""", (cost_center, project, date))

def get_hsd_details(cost_center, project, date):
	return execute_query("""
		SELECT SUM(t2.amount) as total_amount
		FROM `tabPOL Issue` t1, `tabPOL Issue Items` t2
		WHERE t1.name = t2.parent AND t1.docstatus = 1 AND t1.cost_center = %s AND t1.project = %s AND t1.posting_date = %s
	""", (cost_center, project, date))

def get_piu_details(cost_center, project):
	return execute_query("""
		SELECT SUM(t2.total_earning / 30) AS total_amount
		FROM `tabEmployee` t1
		JOIN `tabSalary Structure` t2 ON t1.name = t2.employee
		WHERE t1.status = 'Active' AND t2.is_active ='Yes' AND t1.cost_center = %s AND t1.project = %s
	""", (cost_center, project))

def get_mess_details(cost_center, project, date):
	return execute_query("""
		SELECT SUM(amount) as total_amount
		FROM `tabProject Mess Management`
		WHERE docstatus = 1 AND cost_center = %s AND project = %s AND posting_date = %s
	""", (cost_center, project, date))

def get_material_details(cost_center, project, date):
	return execute_query("""
		SELECT SUM(t2.amount) as total_amount
		FROM `tabStock Entry` t1, `tabStock Entry Detail` t2
		WHERE t1.name = t2.parent AND t1.stock_entry_type = "Material Issue" AND t1.docstatus = 1 AND t2.cost_center = %s AND t2.project = %s AND t1.posting_date = %s
	""", (cost_center, project, date))

def get_labour_details(cost_center, project, date):

	mr_total, labour_cost = frappe.db.sql(
		"""
		SELECT COUNT(t1.name) AS mr_total, SUM(t1.rate_per_day) AS total_amount
		FROM `tabMuster Roll Employee` t1
		INNER JOIN `tabMuster Roll Attendance` t2 ON t1.name = t2.mr_employee
		WHERE t1.status = 'Active'
		AND t1.cost_center = %s
		AND t1.project = %s
		AND t2.date = %s
		""",
		(cost_center, project, date),
	)[0] or (0, 0.0)

	overtime_cost = frappe.db.sql(
		"""
		SELECT SUM(t2.number_of_hours * t1.rate_per_hour) AS total_amount
		FROM `tabMuster Roll Employee` t1
		INNER JOIN `tabMuster Roll Overtime Entry` t2 ON t1.name = t2.mr_employee
		WHERE t1.status = 'Active'
		AND t2.docstatus = 1
		AND t1.cost_center = %s
		AND t1.project = %s
		AND t2.date = %s
		""",
		(cost_center, project, date),
	)[0][0] or 0.0
	return mr_total, flt(labour_cost) + flt(overtime_cost)

def get_rom_details(cost_center, project, date):
	return execute_query("""
		SELECT SUM(t1.amount) as total_amount
		FROM `tabRecord Of Measurement` t1, `tabRecord Of Measurement Item` t2
		WHERE t2.parent = t1.name AND t1.docstatus = 1 AND t1.cost_center = %s AND t1.project = %s AND t1.posting_date = %s
	""", (cost_center, project, date))

def execute_query(query, params):
	result = fetch_query(query, params)
	return result[0].get('total_amount', 0) if result else 0
