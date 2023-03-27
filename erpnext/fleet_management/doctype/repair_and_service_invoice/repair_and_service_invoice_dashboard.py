from frappe import _

def get_data():
	return {
        "fieldname": "reference_name",
		"non_standard_fieldnames": {
			"Repair And Service": "repair_and_services",
		},
		"transactions": [
			{"label": _("Related Transaction"), "items": ["Payment Entry","Repair And Service"]},
		],
	}
