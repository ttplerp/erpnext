from frappe import _

def get_data():
	return {
        "internal_links": {
			"POS Closing Entry": ["items", "pos_closing_entry"],
		},
		"transactions": [
			{"label": _("Reference"), "items": ["POS Closing Entry"]},
		],
	}