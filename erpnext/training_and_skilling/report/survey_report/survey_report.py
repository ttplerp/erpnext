# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
import ast

def execute(filters=None):
    questions = []
    if filters.survey:
        questions = frappe.db.sql("select question, question_text, type from `tabQuestionaire Item` where parent = %(parent)s order by idx", {"parent": filters.survey}, as_dict=1)
        columns, data = get_columns(filters, questions), get_data(filters, questions)
        return columns, data

def get_data(filters, questions):
    additional_select = ""
    question_ids = []
    for a in questions:
        additional_select += """, MAX(CASE WHEN sri.question_id = '{}' THEN 
        CASE
            WHEN COALESCE(sri.other_text, '') <> '' 
            THEN
                REPLACE(sri.answer, "'Other'", CONCAT("'", sri.other_text, "'"))
            ELSE sri.answer
        END
        END) AS {} """.format(a.question, a.question)
        if a.type == "Checkbox":
            question_ids.append(a.question)

    data = frappe.db.sql("""
            SELECT sr.desuup_name, sr.desuup, sr.mobile_number, sr.employment_status, sr.country, sr.dzongkhag {0}
            FROM `tabSurvey Response` sr LEFT JOIN `tabSurvey Response Item` sri ON sri.parent = sr.name 
            WHERE sr.questionaire = %(questionaire)s and sr.docstatus = 1 
            GROUP BY sr.desuup_name, sr.desuup, sr.mobile_number;
            """.format(additional_select), {"questionaire": filters.survey}, as_dict=True)
    for a in data:
        for q in question_ids:
            ans = a.get(q)
            a[q] = get_literal_value(ans)
    return data

def get_literal_value(ans):
    if isinstance(ans, str) and ans.startswith("("):
        try:
            val = ast.literal_eval(ans)
            if isinstance(val, tuple):
                return "; ".join(val)
        except:
            pass
    return ans

def get_columns(filters, questions):
    columns = [
                {
                    "fieldname":"desuup_name",
                    "label":_("Name"),
                    "fieldtype":"Data",
                    "width":180
                },
                {
                    "fieldname":"desuup",
                    "label":_("Desuung ID"),
                    "fieldtype":"Data",
                    "width":140
                },
                {
                    "fieldname":"mobile_number",
                    "label":_("Mobile Number"),
                    "fieldtype":"Data",
                    "width":120
                },
                {
                    "fieldname":"employment_status",
                    "label":_("Employment Status"),
                    "fieldtype":"Data",
                    "width":140
                },
                {
                    "fieldname":"country",
                    "label":_("Present Country"),
                    "fieldtype":"Data",
                    "width":120
                },
                {
                    "fieldname":"dzongkhag",
                    "label":_("Present Dzongkhag"),
                    "fieldtype":"Data",
                    "width":140
                }
            ]

    for q in questions:
        columns.append({
            "fieldname": q.question,
            "label": q.question_text,
            "fieldtype" : "Data",
            "width": 200
        })
    return columns
