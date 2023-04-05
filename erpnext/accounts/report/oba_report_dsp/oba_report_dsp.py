# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _, _dict
from frappe.utils import cstr, getdate

value_fields = ("opening_debit", "opening_credit", "debit", "credit", "closing_debit", "closing_credit")
def execute(filters=None):
	columns= get_columns(filters)
	data = get_data(filters)
	return columns, data

def get_data(filters):
	row = []
	data = frappe._dict()
	gl_entries = frappe.db.sql("""select posting_date,debit,credit,is_opening,party_type,party,cost_center,voucher_no from `tabGL Entry` where party_type='{0}' and cost_center='{1}' and posting_date <= '{2}'
		""".format(filters.get("party_type"), filters.get("cost_center"),filters.get("to_date")), as_dict=True)
	
	for gle in gl_entries:
		data.setdefault(gle.get("party"), []).append(gle)
	
	from_date, to_date = getdate(filters.from_date), getdate(filters.to_date)
	for key, value in data.items():
		# frappe.msgprint(str(key))
		# frappe.throw("<pre>{}</pre>".format(frappe.as_json(value)))
		if filters.get("party_type") == "Employee":
			filter_data = frappe._dict({
					"employee": key,
					"employee_name": frappe.db.get_value("Employee", key, "employee_name"),
				})
		else:
			filter_data = frappe._dict({
					"supplier": key,
					"tpn": frappe.db.get_value("Supplier", key, "vendor_tpn_no"),
				})
			
		filter_data.update({
			"opening_debit": 0.0,
			"opening_credit": 0.0,
			"debit": 0.0,
			"credit": 0.0,
			"closing_debit": 0.0,
			"closing_credit": 0.0
		})
		# frappe.throw(str(filter_data['employee_name']))
		# frappe.throw("<pre>{}</pre>".format(frappe.as_json(filter_data)))
		for d in value:
			if d.posting_date < from_date or (cstr(d.is_opening) == "Yes"):
				filter_data['opening_debit'] += d.debit
				filter_data['opening_credit'] += d.credit

				filter_data['closing_debit'] += d.debit
				filter_data['closing_credit'] += d.credit
			elif gle.posting_date <= to_date or (cstr(gle.is_opening) == "Yes"):
				filter_data['debit'] += d.debit
				filter_data['credit'] += d.credit

				filter_data['closing_debit'] += d.debit
				filter_data['closing_credit'] += d.credit

		if filter_data['closing_debit'] > filter_data['closing_credit']:
			filter_data['closing_debit'] = filter_data['closing_debit'] - filter_data['closing_credit']
			filter_data['closing_credit'] = 0
		else:
			filter_data['closing_debit'] = 0
			filter_data['closing_credit'] = filter_data['closing_credit'] - filter_data['closing_debit']
		
		# frappe.throw("<pre>{}</pre>".format(frappe.as_json(filter_data)))
		row.append(filter_data)

	return row

def get_columns(filters):
	if filters.get("party_type") == "Employee":
		columns = [
			{
				"label": _("Employee"),
				"fieldname": "employee",
				"fieldtype": "Data",
				"width": 120,
			},
			{
				"label": _("Employee Name"),
				"fieldname": "employee_name",
				"fieldtype": "Data",
				"width": 100,
			},
		]
	else:
		columns = [
			{
				"label": _("Supplier"),
				"fieldname": "supplier",
				"fieldtype": "Data",
				"width": 160,
			},
			{
				"label": _("TPN"),
				"fieldname": "tpn",
				"fieldtype": "Data",
				"width": 100,
			},
		]
	
	columns.extend(
		[
			{
				"label": _("Opening Debit"),
				"fieldname": "opening_debit",
				"fieldtype": "Data",
				"width": 120,
			},
			{
				"label": _("Opening Credit"),
				"fieldname": "opening_credit",
				"fieldtype": "Data",
				"width": 120,
			},
			{
				"label": _("Debit"),
				"fieldname": "debit",
				"fieldtype": "Data",
				"width": 120,
			},
			{
				"label": _("Credit"),
				"fieldname": "credit",
				"fieldtype": "Data",
				"width": 120,
			},
			{
				"label": _("Closing Debit"),
				"fieldname": "closing_debit",
				"fieldtype": "Data",
				"width": 120,
			},
			{
				"label": _("Closing Credit"),
				"fieldname": "closing_credit",
				"fieldtype": "Data",
				"width": 120,
			}
		]
	)

	return columns