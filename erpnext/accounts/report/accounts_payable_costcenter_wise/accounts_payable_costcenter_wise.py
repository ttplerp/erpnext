import frappe
def execute(filters=None):
    columns, data = get_columns(filters), get_data(filters)
    return columns, data

def get_columns(filters):
    return [
        {
            "fieldname": "cost_center",
            "label": "Cost Center",
            "fieldtype": "Data",
            "width": 160
        },
        {
            "fieldname": "accounts_payable",
            "label": "Accounts Payable",
            "fieldtype": "Data",
            "width": 160
        },
    ]

def get_data(filters):
    data1 = frappe.db.sql('''
        SELECT
            gl.cost_center,
            SUM(CASE WHEN a.name = "21.101 - Sundry Creditors" THEN gl.credit - gl.debit ELSE 0 END) AS accounts_payable
        FROM
            `tabGL Entry` AS gl
        INNER JOIN
            `tabAccount` AS a
        ON
            gl.account = a.name
        WHERE
            gl.company = "VAJRA BUILDERS PRIVATE LIMITED"
            AND gl.fiscal_year = "2023"
        GROUP BY
            gl.cost_center
    ''', as_dict=1)

    data2 = frappe.db.sql('''
        SELECT
            gl.cost_center,
            SUM(CASE WHEN a.name = "21.101 - Sundry Creditors" THEN gl.credit - gl.debit ELSE 0 END) AS accounts_payable
        FROM
            `tabGL Entry` AS gl
        INNER JOIN
            `tabAccount` AS a
        ON
            gl.account = a.name
        WHERE
            gl.company = "VAJRA BUILDERS PRIVATE LIMITED"
            AND gl.fiscal_year = "2024"
        GROUP BY
            gl.cost_center
    ''', as_dict=1)

    # Convert data1 and data2 to dictionaries for easier lookup
    data1_dict = {d['cost_center']: d['accounts_payable'] for d in data1}
    data2_dict = {d['cost_center']: d['accounts_payable'] for d in data2}

    # List of all cost centers
    cost_centers = set(data1_dict.keys()).union(set(data2_dict.keys()))

    data3 = []
    for cost_center in cost_centers:
        accounts_payable_2023 = data1_dict.get(cost_center, 0)
        accounts_payable_2024 = data2_dict.get(cost_center, 0)
        accounts_payable_difference = accounts_payable_2023 + accounts_payable_2024
        
        data3.append({
            'cost_center': cost_center,
            'accounts_payable': accounts_payable_difference
        })
        

    return data3
