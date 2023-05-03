from frappe import _

def get_data():
	return {
        "fieldname": "equipment",
		"transactions": [
			{"label": _("POL Transaction"), "items": ["POL Receive", "POL Expense", "POL Issue","Fleet Engagement"]},
			{"label": _("Hiring Transaction"), "items": ["Transporter Invoice", "EME Invoice", "Equipment Hiring Form", "Logbook"]},
			{"label": _("Repair & Services"), "items": ["Repair And Services", "Repair And Service Invoice", "Equipment Modifier Tool", "Insurance and Registration"]},
		],
	}