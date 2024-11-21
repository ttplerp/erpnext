from frappe import _


def get_data():
	return {
		"fieldname": "boq",
		"transactions": [
			{"label": _("Related Transaction"), "items": ["BOQ Adjustment", "Subcontract","BOQ Addition"]},
			{"label": _("Other Transaction"), "items": ["MB Entry", "Project Invoice"]},
		],
	}
