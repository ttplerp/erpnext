from frappe import _


def get_data():
    return {
        "fieldname": "journal_entry",
        "non_standard_fieldnames": {
            "Journal Entry": "reference_doctype",
        },
        "transactions": [
            {"label": _("Related Transaction"), "items": ["Journal Entry"]},
        ],
    }
