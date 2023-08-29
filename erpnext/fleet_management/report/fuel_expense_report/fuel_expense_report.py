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
				equipment, item_name, sum(qty) as qty, sum(total) as total
			FROM (
				SELECT 
					pi.equipment, p.item_name, pi.qty, pi.rate, pi.amount as total, p.posting_date 
				FROM 
					`tabPOL Issue Items` pi, 
					`tabPOL Issue` p 
				WHERE 
					p.name=pi.parent 
			UNION ALL 
				SELECT 
					pr.equipment, pr.item_name, pr.qty, pr.rate, (pr.qty * pr.rate) as total, pr.posting_date          
				FROM 
					`tabPOL Receive` pr          
				WHERE 
					pr.direct_consumption = 1
				) combile {cond} 
            GROUP BY equipment;
		""".format(
            cond=cond
        )
    else:
        sql = """
			SELECT 
				posting_date, equipment, item_name, qty, rate, total 
			FROM (
				SELECT 
					pi.equipment, p.item_name, pi.qty, pi.rate, pi.amount as total, p.posting_date 
				FROM 
					`tabPOL Issue Items` pi, 
					`tabPOL Issue` p 
				WHERE 
					p.name=pi.parent 
			UNION ALL 
				SELECT 
					pr.equipment, pr.item_name, pr.qty, pr.rate, (pr.qty * pr.rate) as total, pr.posting_date          
				FROM 
					`tabPOL Receive` pr          
				WHERE 
					pr.direct_consumption = 1
				) combile {cond};
			""".format(
            cond=cond
        )
    return sql


def get_columns(filters):
    column = []
    if not filters.consolidate:
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
            "width": 150,
        },
        {
            "fieldname": "item_name",
            "label": "Item",
            "fieldtype": "Data",
            "width": 150,
        },
        {
            "fieldname": "qty",
            "label": "Quantity",
            "fieldtype": "Float",
            "width": 150,
        },
    ]
    if not filters.consolidate:
        column.append(
            {
                "fieldname": "rate",
                "label": "Rate",
                "fieldtype": "Currency",
                "width": 150,
            }
        )
    column.append(
        {
            "fieldname": "total",
            "label": "Total",
            "fieldtype": "Currency",
            "width": 250,
        }
    )
    return column


def get_conditions(filters):
    cond = []
    if filters.equipment:
        cond.append(" equipment = '{}'".format(filters.equipment))
    if filters.item_name:
        cond.append(" item_name = '{}'".format(filters.item_name))
    # if filters.from_date > filters.to_date:
    #     frappe.throw("From Date cannot be greater than To Date")
    if filters.from_date and filters.to_date:
        cond.append(
            " posting_date between '{}' and '{}' ".format(
                filters.from_date, filters.to_date
            )
        )
    if len(cond) > 0:
        return "WHERE " + " AND".join(cond)
    return ""


def get_data(query):
    return frappe.db.sql(query, as_dict=1)
