from frappe import _

def get_data():
	return {
        "fieldname": "eme_invoice_entry",
		"internal_links": {
			"Journal Entry": ["successful_transaction", "eme_invoice"]
		},
		"transactions": [
			{"label": _("Related Transaction"), "items": ["EME Invoice","Journal Entry"]},
		],
	}