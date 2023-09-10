# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _, _dict
from frappe.utils import cstr, getdate

TRANSLATIONS = frappe._dict()
def execute(filters=None):
	columns = get_columns()
	update_translations()

	data = get_data(filters)

	return columns, data

def get_data(filters):
	cond=""
	if filters.get("cost_center"):
		cond=" and cost_center='{}'".format(filters.get("cost_center"))
	gl_entries = frappe.db.sql("""Select * from `tabGL Entry` where account='{0}' and posting_date <= '{1}' {cond} and is_cancelled = 0
		""".format(filters.get("account"), filters.get("to_date"), cond=cond), as_dict=True)
	
	def update_value_in_dict(data, key, gle):
		data[key].debit += gle.debit
		data[key].credit += gle.credit

		data[key].debit_in_account_currency += gle.debit_in_account_currency
		data[key].credit_in_account_currency += gle.credit_in_account_currency
	
	totals = get_totals_dict()
	from_date, to_date = getdate(filters.from_date), getdate(filters.to_date)
	entries = []
	data = []
	for gle in gl_entries:
		if gle.posting_date < from_date or (cstr(gle.is_opening) == "Yes"):
			update_value_in_dict(totals, "opening", gle)
			update_value_in_dict(totals, "closing", gle)

		elif gle.posting_date <= to_date or (cstr(gle.is_opening) == "Yes"):
			update_value_in_dict(totals, "total", gle)
			update_value_in_dict(totals, "closing", gle)
			entries.append(gle)

	
	data.append(totals.opening)
	data += entries
	data.append(totals.total)
	data.append(totals.closing)
	
	return data

def update_translations():
	TRANSLATIONS.update(
		dict(OPENING=_("Opening"), TOTAL=_("Total"), CLOSING_TOTAL=_("Closing (Opening + Total)"))
	)

def get_totals_dict():
	def _get_debit_credit_dict(label):
		return _dict(
			account="'{0}'".format(label),
			debit=0.0,
			credit=0.0,
			debit_in_account_currency=0.0,
			credit_in_account_currency=0.0,
		)

	return _dict(
		opening=_get_debit_credit_dict(TRANSLATIONS.OPENING),
		total=_get_debit_credit_dict(TRANSLATIONS.TOTAL),
		closing=_get_debit_credit_dict(TRANSLATIONS.CLOSING_TOTAL),
	)

def get_columns():
	return [
		{
			"label": _("Posting Date"),
			"fieldname": "posting_date",
			"fieldtype": "Date",
			"width": 100,
		},
		{
			"label": _("Account"),
			"fieldname": "account",
			"fieldtype": "Link",
			"options": "Account",
			"width": 180,
		},
		{
			"label": _("Debit"),
			"fieldname": "debit",
			"fieldtype": "Float",
			"width": 100,
		},
		{
			"label": _("Credit"),
			"fieldname": "credit",
			"fieldtype": "Float",
			"width": 100,
		},
		{"label": _("Voucher Type"), "fieldname": "voucher_type", "width": 120},
		{
			"label": _("Voucher No"),
			"fieldname": "voucher_no",
			"fieldtype": "Dynamic Link",
			"options": "voucher_type",
			"width": 180,
		},
		{
			"label": _("Cost Center"),
			"fieldname": "cost_center",
			"fieldtype": "Data",
			"width": 180,
		}
	]