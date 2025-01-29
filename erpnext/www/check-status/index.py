import datetime
import json

import frappe
import pytz
from frappe import _

no_cache = 1

@frappe.whitelist(allow_guest=True)
def get_applicant_info(cid):
    context = {}
    context["applicant_info"] = None

    if cid:
        applicant_info = frappe.get_all(
            "Housing Application",
            filters={"cid": cid},
            fields=["name", "applicant_name", "cid", "gender", "employment_type", "applicant_rank", "application_status", "mobile_no", "flat_no","building_classification","application_date_time","work_station"],
        )
        context["applicant_info"] = applicant_info
    
    return context
