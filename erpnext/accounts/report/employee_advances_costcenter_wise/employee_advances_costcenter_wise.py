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
            "fieldname": "salary_advance",
            "label": "Salary Advance Difference",
            "fieldtype": "Data",
            "width": 160
        },
        {
            "fieldname": "travel_advance",
            "label": "Travel Advance Difference",
            "fieldtype": "Data",
            "width": 160
        },
        {
            "fieldname": "workers_advance_account",
            "label": "Workers Advance Account Difference",
            "fieldtype": "Data",
            "width": 200
        },
    ]

def get_data(filters):
    data1 = frappe.db.sql('''
        SELECT
            gl.cost_center,
            SUM(CASE WHEN a.name = "11.501 - Salary Advance" THEN gl.debit - gl.credit ELSE 0 END) AS salary_advance,
            SUM(CASE WHEN a.name = "11.502 - Travel Advance" THEN gl.debit - gl.credit ELSE 0 END) AS travel_advance,
            SUM(CASE WHEN a.name = "11.900 - Workers Advance Account" THEN gl.debit - gl.credit ELSE 0 END) AS workers_advance_account
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
            SUM(CASE WHEN a.name = "11.501 - Salary Advance" THEN gl.debit - gl.credit ELSE 0 END) AS salary_advance,
            SUM(CASE WHEN a.name = "11.502 - Travel Advance" THEN gl.debit - gl.credit ELSE 0 END) AS travel_advance,
            SUM(CASE WHEN a.name = "11.900 - Workers Advance Account" THEN gl.debit - gl.credit ELSE 0 END) AS workers_advance_account
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
    data1_dict = {d['cost_center']: d for d in data1}
    data2_dict = {d['cost_center']: d for d in data2}

    # List of all cost centers
    cost_centers = set(data1_dict.keys()).union(set(data2_dict.keys()))

    data3 = []
    for cost_center in cost_centers:
        salary_advance_2023 = data1_dict.get(cost_center, {}).get('salary_advance', 0)
        travel_advance_2023 = data1_dict.get(cost_center, {}).get('travel_advance', 0)
        workers_advance_account_2023 = data1_dict.get(cost_center, {}).get('workers_advance_account', 0)

        salary_advance_2024 = data2_dict.get(cost_center, {}).get('salary_advance', 0)
        travel_advance_2024 = data2_dict.get(cost_center, {}).get('travel_advance', 0)
        workers_advance_account_2024 = data2_dict.get(cost_center, {}).get('workers_advance_account', 0)

        data3.append({
            'cost_center': cost_center,
            'salary_advance': salary_advance_2023 + salary_advance_2024,
            'travel_advance': travel_advance_2023 + travel_advance_2024,
            'workers_advance_account': workers_advance_account_2023 + workers_advance_account_2024
        })

    return data3
