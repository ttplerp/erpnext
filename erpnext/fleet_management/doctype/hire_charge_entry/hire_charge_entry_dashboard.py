from frappe import _


def get_data():
    return {
        "fieldname": "hire_charge_entry",
        "non_standard_fieldnames": {
            "Journal Entry": "reference_doctype",
        },
        "transactions": [
            {"label": _("Related Transaction"), "items": ["Hire Charge Invoice","Journal Entry"]},
        ],
    }
