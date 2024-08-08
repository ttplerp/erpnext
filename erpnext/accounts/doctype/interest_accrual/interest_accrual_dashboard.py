# Copyright (c) 2024,s Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from frappe import _

def get_data():
	return {
        "fieldname": "reference_name",
		"transactions": [
			{"label": _("Related Transaction"), "items": ["Journal Entry"]},
		],
	}