def get_data():
	return {
		"fieldname": "desuup_payroll_entry",
		"non_standard_fieldnames": {
			"Journal Entry": "reference_name",
			"Payment Entry": "reference_name",
		},
		"transactions": [{"items": ["Desuup Pay Slip", "Journal Entry"]}],
	}
