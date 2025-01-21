from frappe import _

def get_data():
	return {
        "fieldname": "reference_name",
		"non_standard_fieldnames": {
			"Repair And Services": "repair_and_services",
		},
		"transactions": [
			# {"label": _("Related Transaction"), "items": ["Payment Entry","Journal Entry","Repair And Services"]},
			{"label": _("Related Transaction"), "items": ["Payment Entry"]},
		],
	}
