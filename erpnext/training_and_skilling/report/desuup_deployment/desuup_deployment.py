# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import getdate

def execute(filters=None):
    if getdate(filters.from_date) > getdate(filters.to_date):
        frappe.throw("Invalid from and to date")
    columns, data = get_columns(filters), get_data(filters)

    return columns, data

def get_data(filters):
    if filters.show == "Deployment":
        additional_filters = ""
        if filters.deployment:
            additional_filters = " and name = %(deployment)s "
        if filters.dzongkhag:
            additional_filters = " and dzongkhag = %(dzongkhag)s "
        data = frappe.db.sql("""
                    SELECT 
                        deployment_code, type_of_deployment, event,category, country, dzongkhag, gewog, start_date, end_date, gojay, gojay_name
                    FROM `tabDesuup Deployment`
                    WHERE docstatus = 1 and type_of_deployment != 'Skilling'
                     AND (start_date between %(fromdate)s and %(todate)s OR end_date BETWEEN %(fromdate)s and %(todate)s)
                     {0}
                     ORDER BY start_date
                """.format(additional_filters), {"deployment": filters.deployment, "dzongkhag": filters.dzongkhag, "fromdate": filters.from_date, "todate": filters.to_date})
        return data
    else:
        cols = "full_name, cid, desuup, phone_number, days_attended, start_date, end_date"

        where = "docstatus = 1 "
        if filters.deployment:
            where += " and desuup_deployment = %(deployment)s "
        else:
            cols += ", code, description"

        if filters.dzongkhag:
            where += " and dzongkhag = %(dzongkhag)s"
        else:
            cols += ", dzongkhag"

        data = frappe.db.sql("""
                    SELECT 
                        {0}
                    FROM `tabDeployment Entry` 
                    WHERE {1}
                     AND (start_date between %(fromdate)s and %(todate)s OR end_date BETWEEN %(fromdate)s and %(todate)s)
                    ORDER BY full_name
                 """.format(cols, where), {"deployment": filters.deployment, "dzongkhag": filters.dzongkhag, "fromdate": filters.from_date, "todate": filters.to_date})

        return data

def get_columns(filters):
    if filters.show == "Deployment":
        columns = [
                    {
                        "fieldname":"deployment_code",
                        "label":_("Code"),
                        "fieldtype":"Data",
                        "width":180
                    },
                    {
                        "fieldname":"type_of_deployment",
                        "label":_("Type"),
                        "fieldtype":"Data",
                        "width":180
                    },
                    {
                        "fieldname":"event",
                        "label":_("Type of Event"),
                        "fieldtype":"Data",
                        "width":180
                    },
                    {
                        "fieldname":"category",
                        "label":_("Category"),
                        "fieldtype":"Data",
                        "width":180
                    },
                    {
                        "fieldname":"country",
                        "label":_("Country"),
                        "fieldtype":"Data",
                        "width":120
                    },
                    {
                        "fieldname":"dzongkhag",
                        "label":_("Dzongkhag"),
                        "fieldtype":"Data",
                        "width":140
                    },
                    {
                        "fieldname":"gewog",
                        "label":_("Gewog"),
                        "fieldtype":"Data",
                        "width":140
                    },
                    {
                        "fieldname":"start_date",
                        "label":_("Start Date"),
                        "fieldtype":"Date",
                        "width":120
                    },
                    {
                        "fieldname":"end_date",
                        "label":_("End Date"),
                        "fieldtype":"Date",
                        "width":120
                    },
                    {
                        "fieldname":"gojay",
                        "label":_("Gojay"),
                        "fieldtype":"Data",
                        "width":140
                    },
                    {
                        "fieldname":"gojay_name",
                        "label":_("Gojay Name"),
                        "fieldtype":"Data",
                        "width":180
                    },
                ]
        return columns
    else:
        columns = [
                    {
                        "fieldname":"full_name",
                        "label":_("Name"),
                        "fieldtype":"Data",
                        "width":140
                    },
                    {
                        "fieldname":"cid",
                        "label":_("CID"),
                        "fieldtype":"Data",
                        "width":120
                    },
                    {
                        "fieldname":"desuup",
                        "label":_("DID"),
                        "fieldtype":"Data",
                        "width":140
                    },
                    {
                        "fieldname":"phone_number",
                        "label":_("Phone"),
                        "fieldtype":"Data",
                        "width":130
                    },
                    {
                        "fieldname":"days_attended",
                        "label":_("No. of days"),
                        "fieldtype":"Data",
                        "width":100
                    },
                    {
                        "fieldname":"start_date",
                        "label":_("Start Date"),
                        "fieldtype":"Date",
                        "width":120
                    },
                    {
                        "fieldname":"end_date",
                        "label":_("End Date"),
                        "fieldtype":"Date",
                        "width":120
                    }]
        if not filters.deployment:
            columns.append({
                "fieldname":"code",
                "label":_("Deployment Code"),
                "fieldtype":"Data",
                "width":170
            })

            columns.append({
                "fieldname":"description",
                "label":_("Title"),
                "fieldtype":"Data",
                "width":140
            })
        if not filters.dzongkhag:
            columns.append({
                "fieldname":"dzongkhag",
                "label":_("Dzongkhag"),
                "fieldtype":"Data",
                "width":120
            })

        return columns
