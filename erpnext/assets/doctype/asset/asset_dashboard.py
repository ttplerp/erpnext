from frappe import _


def get_data():
	return {
		"fieldname": "reference_name",
		"non_standard_fieldnames": {"Asset Movement": "asset"},
		"transactions": [{"label": _("Movement"), "items": ["Asset Movement"]},{"label":_("Journal Entry"), "items":["Journal Entry"]}],
	}
