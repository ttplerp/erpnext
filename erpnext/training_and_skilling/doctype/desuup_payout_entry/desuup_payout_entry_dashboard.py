def get_data():
	return {
		"fieldname": "desuup_payout_entry",
		"non_standard_fieldnames": {
			"Journal Entry": "reference_name",
			"Payment Entry": "reference_name",
		},
		"transactions": [{"items": ["Journal Entry"]}],
	}
