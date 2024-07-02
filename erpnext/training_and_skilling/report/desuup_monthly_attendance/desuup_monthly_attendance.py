# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from itertools import groupby
from frappe import _
from frappe.query_builder.functions import Count, Extract, Sum
from frappe.utils import cint, cstr, getdate
from typing import Dict, List, Optional, Tuple
from calendar import monthrange

Filters = frappe._dict

status_map = {
	"Present": "P",
	"Absent": "A",
	"Half Day": "HD",
	"Holiday": "H",
	"Weekly Off": "WO",
}

day_abbr = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

def execute(filters: Optional[Filters] = None) -> Tuple:
	filters = frappe._dict(filters or {})

	if not (filters.month and filters.year):
		frappe.throw(_("Please select month and year."))

	attendance_map = get_attendance_map(filters)
	# frappe.throw(str(attendance_map))
	if not attendance_map:
		frappe.msgprint(_("No attendance records found."), alert=True, indicator="orange")
		return [], [], None, None

	columns = get_columns(filters)
	data = get_data(filters, attendance_map)

	if not data:
		frappe.msgprint(
			_("No attendance records found for this criteria."), alert=True, indicator="orange"
		)
		return columns, [], None, None
	
	# message = get_message() if not filters.summarized_view else ""
	# chart = get_chart_data(attendance_map, filters)

	return columns, data


def get_columns(filters: Filters) -> List[Dict]:
	columns = []

	# if filters.group_by:
	# 	columns.append(
	# 		{
	# 			"label": _(filters.group_by),
	# 			"fieldname": frappe.scrub(filters.group_by),
	# 			"fieldtype": "Link",
	# 			"options": "Branch",
	# 			"width": 120,
	# 		}
	# 	)

	columns.extend(
		[
			{"label": _("Desuup"),"fieldname": "desuup","fieldtype": "Link","options": "Desuup","width": 135,},
			{"label": _("Desuup Name"), "fieldname": "desuup_name", "fieldtype": "Data", "width": 140},
		]
	)

	# if filters.summarized_view:
	# 	columns.extend(
	# 		[
	# 			{
	# 				"label": _("Total Present"),
	# 				"fieldname": "total_present",
	# 				"fieldtype": "Float",
	# 				"width": 110,
	# 			},
	# 			{"label": _("Total Leaves"), "fieldname": "total_leaves", "fieldtype": "Float", "width": 110},
	# 			{"label": _("Total Absent"), "fieldname": "total_absent", "fieldtype": "Float", "width": 110},
	# 			{
	# 				"label": _("Total Holidays"),
	# 				"fieldname": "total_holidays",
	# 				"fieldtype": "Float",
	# 				"width": 120,
	# 			},
	# 			{
	# 				"label": _("Unmarked Days"),
	# 				"fieldname": "unmarked_days",
	# 				"fieldtype": "Float",
	# 				"width": 130,
	# 			},
	# 		]
	# 	)
	# 	columns.extend(get_columns_for_leave_types())
	# 	columns.extend(
	# 		[
	# 			{
	# 				"label": _("Total Late Entries"),
	# 				"fieldname": "total_late_entries",
	# 				"fieldtype": "Float",
	# 				"width": 140,
	# 			},
	# 			{
	# 				"label": _("Total Early Exits"),
	# 				"fieldname": "total_early_exits",
	# 				"fieldtype": "Float",
	# 				"width": 140,
	# 			},
	# 		]
	# 	)
	# else:
	# columns.append({"label": _("Shift"), "fieldname": "shift", "fieldtype": "Data", "width": 120})
	columns.extend(get_columns_for_days(filters))

	return columns

def get_data(filters: Filters, attendance_map: Dict) -> List[Dict]:
	desuup_details, group_by_param_values = get_desuup_related_details(
		filters.group_by
	)
	holiday_map = get_holiday_map(filters)

	data = []

	if filters.group_by:
		group_by_column = frappe.scrub(filters.group_by)

		for value in group_by_param_values:
			if not value:
				continue

			records = get_rows(desuup_details[value], filters, holiday_map, attendance_map)

			if records:
				data.append({group_by_column: frappe.bold(value)})
				data.extend(records)
	else:
		data = get_rows(desuup_details, filters, holiday_map, attendance_map)

	return data


def get_attendance_map(filters: Filters) -> Dict:
	Attendance = frappe.qb.DocType("Desuup Attendance")
	query = (
		frappe.qb.from_(Attendance)
		.select(
			Attendance.desuup,
			Extract("day", Attendance.attendance_date).as_("day_of_month"),
			Attendance.status,
			Attendance.shift,
		)
		.where(
			(Attendance.docstatus == 1)
			# & (Attendance.company == filters.company)
			& (Extract("month", Attendance.attendance_date) == filters.month)
			& (Extract("year", Attendance.attendance_date) == filters.year)
		)
	)
	if filters.desuup:
		query = query.where(Attendance.desuup == filters.desuup)
	if filters.report_for:
		query = query.where(Attendance.attendance_for == filters.report_for)
	query = query.orderby(Attendance.desuup, Attendance.attendance_date)

	attendance_list = query.run(as_dict=True)

	attendance_map = {}

	for d in attendance_list:
		attendance_map.setdefault(d.desuup, frappe._dict()).setdefault(d.shift, frappe._dict())
		attendance_map[d.desuup][d.shift][d.day_of_month] = d.status

	return attendance_map


def get_desuup_related_details(group_by: str) -> Tuple[Dict, List]:
	"""Returns
	1. nested dict for Desuup details
	2. list of values for the group by filter
	"""
	Desuup = frappe.qb.DocType("Desuup")
	query = (
		frappe.qb.from_(Desuup)
		.select(
			Desuup.name,
			Desuup.desuup_name,
			Desuup.cid_number,
			# Desuup.date_of_birth,
			# Desuup.department,
			# Desuup.branch,
			# Desuup.company,
			# Desuup.holiday_list,
		)
		# .where(Desuup.company == company)
	)

	if group_by:
		group_by = group_by.lower()
		query = query.orderby(group_by)

	Desuup_details = query.run(as_dict=True)
	# frappe.throw(str(Desuup_details))

	group_by_param_values = []
	dsp_map = {}

	if group_by:
		for parameter, Desuups in groupby(Desuup_details, key=lambda d: d[group_by]):
			group_by_param_values.append(parameter)
			dsp_map.setdefault(parameter, frappe._dict())

			for emp in Desuups:
				dsp_map[parameter][emp.name] = emp
	else:
		for emp in Desuup_details:
			dsp_map[emp.name] = emp

	return dsp_map, group_by_param_values

def get_holiday_map(filters: Filters) -> Dict[str, List[Dict]]:
	"""
	Returns a dict of holidays falling in the filter month and year
	with list name as key and list of holidays as values like
	{
	        'Holiday List 1': [
	                {'day_of_month': '0' , 'weekly_off': 1},
	                {'day_of_month': '1', 'weekly_off': 0}
	        ],
	        'Holiday List 2': [
	                {'day_of_month': '0' , 'weekly_off': 1},
	                {'day_of_month': '1', 'weekly_off': 0}
	        ]
	}
	"""
	# add default holiday list too
	holiday_lists = frappe.db.get_all("Holiday List", pluck="name")
	default_holiday_list = frappe.get_cached_value("Company", filters.company, "default_holiday_list")
	holiday_lists.append(default_holiday_list)

	holiday_map = frappe._dict()
	Holiday = frappe.qb.DocType("Holiday")

	for d in holiday_lists:
		if not d:
			continue

		holidays = (
			frappe.qb.from_(Holiday)
			.select(Extract("day", Holiday.holiday_date).as_("day_of_month"), Holiday.weekly_off)
			.where(
				(Holiday.parent == d)
				& (Extract("month", Holiday.holiday_date) == filters.month)
				& (Extract("year", Holiday.holiday_date) == filters.year)
			)
		).run(as_dict=True)

		holiday_map.setdefault(d, holidays)

	return holiday_map

def get_rows(
	desuup_details: Dict, filters: Filters, holiday_map: Dict, attendance_map: Dict
) -> List[Dict]:
	records = []
	default_holiday_list = frappe.get_cached_value("Company", filters.company, "default_holiday_list")

	for desuup, details in desuup_details.items():
		dsp_holiday_list = details.holiday_list or default_holiday_list
		holidays = holiday_map.get(dsp_holiday_list)

		if filters.summarized_view:
			# attendance = get_attendance_status_for_summarized_view(desuup, filters, holidays)
			# if not attendance:
			# 	continue

			# leave_summary = get_leave_summary(desuup, filters)
			# entry_exits_summary = get_entry_exits_summary(desuup, filters)

			# row = {"desuup": desuup, "desuup_name": details.desuup_name}
			# set_defaults_for_summarized_view(filters, row)
			# row.update(attendance)
			# row.update(leave_summary)
			# row.update(entry_exits_summary)

			# records.append(row)
			pass
		else:
			desuup_attendance = attendance_map.get(desuup)
			if not desuup_attendance:
				continue

			attendance_for_desuup = get_attendance_status_for_detailed_view(
				desuup, filters, desuup_attendance, holidays
			)
			# set desuup details in the first row
			attendance_for_desuup[0].update(
				{"desuup": desuup, "desuup_name": details.desuup_name}
			)

			records.extend(attendance_for_desuup)

	return records

def get_attendance_status_for_detailed_view(
	desuup: str, filters: Filters, desuup_attendance: Dict, holidays: List
) -> List[Dict]:
	"""Returns list of shift-wise attendance status for desuup
	[
	        {'shift': 'Morning Shift', 1: 'A', 2: 'P', 3: 'A'....},
	        {'shift': 'Evening Shift', 1: 'P', 2: 'A', 3: 'P'....}
	]
	"""
	total_days = get_total_days_in_month(filters)
	attendance_values = []

	for shift, status_dict in desuup_attendance.items():
		row = {"shift": shift}

		for day in range(1, total_days + 1):
			status = status_dict.get(day)
			if status is None and holidays:
				status = get_holiday_status(day, holidays)

			abbr = status_map.get(status, "")
			row[day] = abbr

		attendance_values.append(row)

	return attendance_values

def get_total_days_in_month(filters: Filters) -> int:
	return monthrange(cint(filters.year), cint(filters.month))[1]

def get_columns_for_days(filters: Filters) -> List[Dict]:
	total_days = get_total_days_in_month(filters)
	days = []

	for day in range(1, total_days + 1):
		# forms the dates from selected year and month from filters
		date = "{}-{}-{}".format(cstr(filters.year), cstr(filters.month), cstr(day))
		# gets abbr from weekday number
		weekday = day_abbr[getdate(date).weekday()]
		# sets days as 1 Mon, 2 Tue, 3 Wed
		label = "{} {}".format(cstr(day), weekday)
		days.append({"label": label, "fieldtype": "Data", "fieldname": day, "width": 80})

	return days

def get_holiday_status(day: int, holidays: List) -> str:
	status = None
	for holiday in holidays:
		if day == holiday.get("day_of_month"):
			if holiday.get("weekly_off"):
				status = "Weekly Off"
			else:
				status = "Holiday"
			break
	return status

@frappe.whitelist()
def get_attendance_years() -> str:
	"""Returns all the years for which attendance records exist"""
	Attendance = frappe.qb.DocType("Desuup Attendance")
	year_list = (
		frappe.qb.from_(Attendance)
		.select(Extract("year", Attendance.attendance_date).as_("year"))
		.distinct()
	).run(as_dict=True)

	if year_list:
		year_list.sort(key=lambda d: d.year, reverse=True)
	else:
		year_list = [getdate().year]

	return "\n".join(cstr(entry.year) for entry in year_list)
