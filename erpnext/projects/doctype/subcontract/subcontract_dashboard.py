from frappe import _

def get_data():
	return {
		# "non_standard_fieldnames": {
        #     "Project Advance": "reference_name",
        # },
		"fieldname": "subcontract",
		"transactions": [
			{"label": _("Related Transaction"), "items": ["Subcontract Adjustment", "MB Entry"]},
		],
	}
