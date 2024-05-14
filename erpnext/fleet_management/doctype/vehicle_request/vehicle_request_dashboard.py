from frappe import _

def get_data():
	return {
        "fieldname": "vehicle_request",
		"transactions": [
			{"label": _("Related Transaction"), "items": ["Vehicle Request Extension"]},
		],
	}