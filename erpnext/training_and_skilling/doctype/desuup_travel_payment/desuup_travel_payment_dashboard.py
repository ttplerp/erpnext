def get_data():
	return {
		"fieldname": "reference_name",
		"non_standard_fieldnames": {
			"Journal Entry": "reference_name",
			"Payment Entry": "reference_name",
		},
		"transactions": [{"items": ["Journal Entry"]}],
	}
