from frappe import _


def get_data():
	return {
		"fieldname": "reference_name",
		"transactions": [
			{"label": _("Payment"), "items": ["Journal Entry"]},
		],
	}
