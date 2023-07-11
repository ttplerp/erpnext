from frappe import _


def get_data():
	return {
		"fieldname": "asset_issue_details",
		"transactions": [
			{"label": _("Related"), "items": ["Asset"]},
		],
	}