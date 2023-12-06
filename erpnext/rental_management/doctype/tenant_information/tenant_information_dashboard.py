from frappe import _


def get_data():
	return {
		"collapsible": True,
		"fieldname": "tenant",
		# "non_standard_fieldnames": {
		# 	"Stock Entry": "technical_sanction",
		# 	"Technical Sanction Bill": "technical_sanction",
		# },
		"transactions": [
			{
				"label": _("Related"), 
				"items": ["Rental Bill"]
			},
		],
	}