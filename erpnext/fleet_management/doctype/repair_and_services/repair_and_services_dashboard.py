from frappe import _

def get_data():
	return {
        "fieldname": "reference_name",
		"non_standard_fieldnames": {
			"Repair And Service Invoice": "repair_and_services",
		},
		"transactions": [
			# {"label": _("Related Transaction"), "items": ["Journal Entry", "Repair And Service Invoice"]},
			{"label": _("Related Transaction"), "items": ["Repair And Service Invoice"]},
		],
	}
