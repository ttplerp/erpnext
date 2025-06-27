# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class MRPaymentItem(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		account_no: DF.ReadOnly | None
		amount_regular: DF.Currency
		amount_special: DF.Currency
		bank: DF.ReadOnly | None
		bank_payment: DF.Data | None
		daily_rate: DF.Currency
		designation: DF.ReadOnly | None
		employee: DF.DynamicLink
		employee_type: DF.Literal["", "Muster Roll Employee", "GEP Employee"]
		fiscal_year: DF.Link | None
		health: DF.Currency
		hourly_rate: DF.Currency
		hourly_rate_normal: DF.Currency
		id_card: DF.Data
		mess_deduction: DF.Currency
		month: DF.Literal["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
		number_of_days: DF.Float
		number_of_hours: DF.Float
		number_of_hours_special: DF.Float
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		payment_status: DF.Literal["", "Payment Under Process", "Payment Successful", "Payment Failed", "Partial Payment", "Payment Cancelled"]
		person_name: DF.Data
		qualification: DF.ReadOnly | None
		total_amount: DF.Currency
		total_ot_amount: DF.Currency
		total_payable: DF.Currency
		total_wage: DF.Currency
		wage_payable: DF.Currency
	# end: auto-generated types
	pass
