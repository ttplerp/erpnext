# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, cstr, formatdate, get_datetime, get_link_to_form, getdate, nowdate, add_days, get_last_day, get_first_day

class DuplicateAttendanceError(frappe.ValidationError):
	pass

class DesuupAttendance(Document):
	def validate(self):
		from erpnext.controllers.status_updater import validate_status

		validate_status(self.status, ["Present", "Absent", "On Leave", "Half Day"])
		self.validate_active_desuup()
		self.validate_attendance_date()
		self.validate_duplicate_record()

	def validate_active_desuup(self):
		if self.attendance_for == "Trainee":
			pass
		# filters = {"parent": holiday_list, "holiday_date": ("between", [start_date, end_date])}
		pass
	
	def validate_attendance_date(self):
		today = getdate(nowdate())

		# Calculate the first and last days of the current month
		first_day_of_month = get_first_day(today)
		last_day_of_month = get_last_day(today)

		# Calculate the date two days before the end of the month
		two_days_before_end_of_month = add_days(last_day_of_month, -2)

		# Check if the attendance date is within the allowed range
		attendance_date = getdate(self.attendance_date)

		# Allow attendance if the date is within the month
		if first_day_of_month <= attendance_date <= today:
			pass  # Allow marking attendance
		# Allow attendance if today is within the last two days of the month and the attendance date is until the end of the month
		elif today >= two_days_before_end_of_month and attendance_date <= last_day_of_month:
			pass  # Allow marking attendance
		else:
			frappe.throw(_("Attendance can only be marked for today or any past date within the current month."))

	def validate_duplicate_record(self):
		duplicate = get_duplicate_attendance_record(self.desuup, self.attendance_date, self.name)

		if duplicate:
			frappe.throw(
				_("Attendance for desuup {0} is already marked for the date {1}: {2}").format(
					frappe.bold(self.desuup),
					frappe.bold(self.attendance_date),
					get_link_to_form("Desuup Attendance", duplicate[0].name),
				),
				title=_("Duplicate Attendance"),
				exc=DuplicateAttendanceError,
			)

def get_duplicate_attendance_record(desuup, attendance_date, name=None):
	attendance = frappe.qb.DocType("Desuup Attendance")
	query = (
		frappe.qb.from_(attendance)
		.select(attendance.name)
		.where((attendance.desuup == desuup) & (attendance.docstatus < 2))
	)

	query = query.where((attendance.attendance_date == attendance_date))

	if name:
		query = query.where(attendance.name != name)

	return query.run(as_dict=True)