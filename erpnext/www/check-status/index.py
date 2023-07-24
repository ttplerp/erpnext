import frappe

def get_context(context):
    cid = frappe.form_dict.get("cid")
    context["applicant_info"] = None

    if cid:
        applicant_info = frappe.get_all(
            "Housing Application",
            filters={"cid": cid},
            fields=["name", "applicant_name", "cid", "gender", "employment_type", "applicant_rank", "application_status", "mobile_no", "flat_no"],
        )

        context["applicant_info"] = applicant_info

    return context
