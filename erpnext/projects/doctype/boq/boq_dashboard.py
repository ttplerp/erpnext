from frappe import _


def get_data():
	return {
		"fieldname": "boq",
		"transactions": [
			{"label": _("Related Transaction"), "items": ["BOQ Adjustment", "Subcontract",]},
			{"label": _("Other Transaction"), "items": ["MB Entry", "Project Invoice"]},
		],
	}
