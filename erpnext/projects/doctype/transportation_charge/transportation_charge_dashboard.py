def get_data():
    return {
        # name of doctype
        "fieldname": "transportation_charge",
        "non_standard_fieldnames": {
            "Journal Entry": "reference_name",
        },
        "transactions": [
            {"items": ["Journal Entry"]},
        ],
    }
