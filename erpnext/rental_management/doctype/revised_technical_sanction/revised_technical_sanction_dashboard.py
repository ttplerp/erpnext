from frappe import _


def get_data():
	return {
		"fieldname": "revised_technical_sanction",
		"non_standard_fieldnames": {
			"Stock Entry": "technical_sanction",
		},
		"transactions": [
			{"label": _("Related"), "items": ["Stock Entry", "Technical Sanction Bill"]},
		],
	}