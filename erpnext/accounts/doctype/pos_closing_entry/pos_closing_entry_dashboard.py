from frappe import _

def get_data():
	return {
        "fieldname":"pos_closing_entry",
        "internal_links": {
			"POS Closing Entry": ["items", "pos_closing_entry"],
		},
		"transactions": [
			{"label": _("Reference"), "items": ["Deposit Entry"]},
		],
	}