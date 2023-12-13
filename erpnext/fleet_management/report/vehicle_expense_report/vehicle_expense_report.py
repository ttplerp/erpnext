# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
    columns = get_columns(filters)
    cond = get_conditions(filters)
    query = construct_query(cond, filters)
    data = get_data(query)
    return columns, data


def construct_query(cond, filters):
    if filters.consolidate == 1:
        sql = """
        SELECT 
            equipment,
            type,
            sum(amount) as amount
        FROM (
                SELECT
                    ir.posting_date,
                    ir.equipment, 
                    be.type, 
                    be.total_amount as amount
                FROM 
                    `tabBluebook and Emission` be,
                    `tabInsurance and Registration` ir 
                WHERE 
                    ir.name = be.parent 
                UNION ALL
                SELECT 
                    p.posting_date,
                    pi.equipment, 
                    "POL Issue" as type, 
                    pi.amount as amount
                FROM 
                    `tabPOL Issue Items` pi,
                    `tabPOL Issue` p
                WHERE 
                    p.docstatus = 1 and
                    p.name = pi.parent

                UNION ALL

                SELECT 
                    pr.posting_date,
                    pr.equipment, 
                    "POL Receive" as type, 
                    pr.total_amount as amount
                FROM 
                    `tabPOL Receive` pr 
                WHERE 
                    pr.docstatus = 1 AND
                    pr.direct_consumption=1
            ) combine 
        {cond}  
        GROUP BY 
            equipment, type
        ORDER BY 
            equipment
		""".format(
            cond=cond
        )
    else:
        sql = """
        SELECT 
            posting_date,
            name,
            equipment,
            type,
            amount
        FROM (
                SELECT
                    rs.name,
                    rs.posting_date,
                    rs.equipment, 
                    'Repair And Services' AS type, 
                    rs.total_amount as amount
                FROM 
                    `tabRepair And Services` rs
                WHERE 
                    rs.docstatus = 1 

                UNION ALL
                
                SELECT
                    ir.name,
                    ir.posting_date,
                    ir.equipment, 
                    be.type, 
                    be.total_amount as amount
                FROM 
                    `tabBluebook and Emission` be,
                    `tabInsurance and Registration` ir 
                WHERE 
                    ir.name = be.parent 

                UNION ALL

                SELECT 
                    p.name,
                    p.posting_date,
                    pi.equipment, 
                    "POL Issue" as type, 
                    pi.amount as amount
                FROM 
                    `tabPOL Issue Items` pi,
                    `tabPOL Issue` p
                WHERE 
                    p.docstatus = 1 and
                    p.name = pi.parent

                UNION ALL

                SELECT 
                    pr.name,
                    pr.posting_date,
                    pr.equipment, 
                    "POL Receive" as type, 
                    pr.total_amount as amount
                FROM 
                    `tabPOL Receive` pr 
                WHERE 
                    pr.docstatus = 1 AND
                    pr.direct_consumption=1
            ) combine 
        {cond} 
        ORDER BY 
            equipment
		""".format(
            cond=cond
        )
    return sql


def get_columns(filters):
    column = []
    if not filters.consolidate:
        column.append(
            {
                "fieldname": "name",
                "label": "Transaction ID",
                "fieldtype": "Data",
                "width": 200,
            }
        )
        column.append(
            {
                "fieldname": "posting_date",
                "label": "Posting Date",
                "fieldtype": "Date",
                "width": 150,
            }
        )
    column = column + [
        {
            "fieldname": "equipment",
            "label": "Equipment",
            "fieldtype": "Link",
            "options": "Equipment",
            "width": 200,
        },
        {
            "fieldname": "type",
            "label": "Type",
            "fieldtype": "Data",
            "width": 200,
        },
        {
            "fieldname": "amount",
            "label": "Amount",
            "fieldtype": "Currency",
            "width": 250,
        },
    ]
    return column


def get_conditions(filters):
    cond = []
    condition = ""
    if filters.equipment:
        cond.append(" equipment = '{}'".format(filters.equipment))
    if filters.type:
        cond.append(" type = '{}'".format(filters.type))
    if filters.from_date and filters.to_date:
        cond.append(
            " posting_date between '{}' and '{}' ".format(
                filters.from_date, filters.to_date
            )
        )
    if len(cond) > 0:
        condition = "WHERE " + " AND".join(cond)
    return condition


def get_data(query):
    return frappe.db.sql(query, as_dict=1)
