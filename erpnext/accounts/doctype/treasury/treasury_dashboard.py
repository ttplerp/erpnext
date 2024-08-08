# Copyright (c) 2024,s Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from frappe import _

def get_data():
	return {
        "fieldname": "reference_name",
		'non_standard_fieldnames': {
			'Interest Accrual': 'treasury_id',
			'Maturity': 'treasury_id'
		},
		"transactions": [
			{"label": _("Related Transaction"), "items": ["Journal Entry", "Interest Accrual", "Maturity"]},
		],
	}