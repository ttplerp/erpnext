from frappe import _

def get_data():
	return {
        "fieldname": "reference_name",
# 		"non_standard_fieldnames": {
# 			"POL Receive": "pol_receive",
# 		},
		"transactions": [
			{"label": _("Related Transaction"), "items": ["Payment Entry"]},
		],
	}
