# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe

def execute(filters=None):
    columns = get_columns()
    cond = get_conditions(filters)
    query = construct_query(cond)
    data = get_data(query)
    return columns, data

def construct_query(cond):
    query = """
        SELECT
            name, branch, equipment_name, equipment_category,
            equipment_model, equipment_type, wheeler, fuel_type
        FROM
            `tabEquipment`
        WHERE
            enabled = 1 AND status = 'Running'
            AND equipment_category = 'Pool' {}
    """.format(cond)
    return query

def get_columns():
    return [
        {
            "fieldname": "branch",
            "label": "Branch",
            "fieldtype": "Link",
            "options": "Branch",
            "width": 150
        },
        {
            "fieldname": "cost_center",
            "label": "Cost Center",
            "fieldtype": "Link",
            "options": "Cost Center",
            "width": 150
        },
        {
            "fieldname": "equipment_number",
            "label": "Equipment Number",
            "fieldtype": "Link",
            "options": "Equipment",
            "width": 150
        },
        {
            "fieldname": "equipment_model",
            "label": "Equipment Model",
            "fieldtype": "Link",
            "options": "Equipment Model",
            "width": 150
        },
        {
            "fieldname": "equipment_type",
            "label": "Equipment Type",
            "fieldtype": "Link",
            "options": "Equipment Type",
            "width": 150
        },
        {
            "fieldname": "status",
            "label": "Availability",
            "fieldtype": "Data",
            "width": 150
        }
    ]

def get_conditions(filters):
    cond = ''
    if filters.vehicle_type:
        cond += " AND equipment_type = '{}'".format(filters.vehicle_type)
    if filters.branch:
        cond += " AND branch = '{}'".format(filters.branch)
    if filters.vehicle:
        cond += " AND name = '{}'".format(filters.vehicle)
    return cond

def get_data(query):
    data = []
    active_equipment = frappe.db.sql(query, as_dict=1)
    for d in active_equipment:
        cc = frappe.db.get_value("Branch", d.branch, "cost_center")
        booking_status = "Booked" if frappe.db.exists("Vehicle Request", {"vehicle": d.name, "status": "Booked", "docstatus": 1}) else "Free"
        row = {
            "branch": d.branch,
            "cost_center": cc,
            "equipment_number": d.name,
            "equipment_model": d.equipment_model,
            "equipment_type": d.equipment_type,
            "status": booking_status
        }
        data.append(row)
    return data
