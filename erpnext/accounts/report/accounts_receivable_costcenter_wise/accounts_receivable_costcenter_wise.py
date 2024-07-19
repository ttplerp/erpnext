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
            "fieldname": "accounts_receivable",
            "label": "Accounts Receivable",
            "fieldtype": "Data",
            "width": 160
        },
    ]

def get_data(filters):
    data1 = frappe.db.sql('''
        SELECT
            gl.cost_center,
            SUM(CASE WHEN a.name = "11.101 - Sundry Debtors-Client" THEN gl.debit - gl.credit ELSE 0 END) AS accounts_receivable
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
            SUM(CASE WHEN a.name = "11.101 - Sundry Debtors-Client" THEN gl.debit - gl.credit ELSE 0 END) AS accounts_receivable
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
    data1_dict = {d['cost_center']: d['accounts_receivable'] for d in data1}
    data2_dict = {d['cost_center']: d['accounts_receivable'] for d in data2}

    # List of all cost centers
    cost_centers = set(data1_dict.keys()).union(set(data2_dict.keys()))

    data3 = []
    for cost_center in cost_centers:
        accounts_receivable_2023 = data1_dict.get(cost_center, 0)
        accounts_receivable_2024 = data2_dict.get(cost_center, 0)
        accounts_receivable_difference = accounts_receivable_2023 + accounts_receivable_2024
        
        data3.append({
            'cost_center': cost_center,
            'accounts_receivable': accounts_receivable_difference
        })
        

    return data3
