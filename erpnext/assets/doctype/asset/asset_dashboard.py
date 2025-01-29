from frappe import _


def get_data():
	return {
		"non_standard_fieldnames": {"Asset Movement": "asset", "Sales Invoice": "asset"},
		"transactions": [{"label": _("Movement"), "items": ["Asset Movement","Sales Invoice"]}],
	}
