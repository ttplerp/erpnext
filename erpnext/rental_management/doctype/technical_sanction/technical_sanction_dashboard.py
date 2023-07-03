from frappe import _


def get_data():
	return {
		"fieldname": "technical_sanction",
		# "non_standard_fieldnames": {
		# 	"Stock Entry": "technical_sanction",
		# 	"Technical Sanction Bill": "technical_sanction",
		# },
		"transactions": [
			{"label": _("Related"), "items": ["Stock Entry", "Technical Sanction Bill"]},
		],
	}