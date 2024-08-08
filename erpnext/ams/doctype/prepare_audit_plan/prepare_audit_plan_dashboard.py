# Copyright (c) 2024,s Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from frappe import _

def get_data():
	return {
        "fieldname": "reference_name",
		'non_standard_fieldnames': {
			'Audit Engagement Letter': 'prepare_audit_plan_no',
			'Execute Audit': 'prepare_audit_plan_no',
			'Audit Initial Report': 'prepare_audit_plan_no',
			'Follow Up': 'prepare_audit_plan_no',
			'Close Follow Up': 'prepare_audit_plan_no',
		},
		"transactions": [
			{"label": _("Related Transaction"), "items": ["Audit Engagement Letter", "Execute Audit", "Audit Initial Report", "Follow Up", "Close Follow Up"]},
		],
	}