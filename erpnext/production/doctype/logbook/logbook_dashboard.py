from frappe import _

def get_data():
	return {
        "fieldname": "logbook",
		"transactions": [
			{"label": _("Transaction"), "items": ["Transportation and Hire Charge Invoice"]},
		],
	}
