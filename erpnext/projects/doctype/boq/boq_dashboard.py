from frappe import _


def get_data():
	return {
		"fieldname": "boq",
		"transactions": [
			{"label": _("Related Transaction"), "items": ["BOQ Adjustment", "BOQ Substitution", "BOQ Addition"]},
			{"label": _("Other Transaction"), "items": ["MB Entry", "Subcontract", "Project Invoice"]},
		],
	}
