from frappe import _


def get_data():
    return {
        "fieldname": "transportation_and_hire_charge_entry",
        "non_standard_fieldnames": {
            "Journal Entry": "reference_doctype",
        },
        "transactions": [
            {"label": _("Related Transaction"), "items": ["Transportation and Hire Charge Invoice","Journal Entry"]},
        ],
    }
