from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from frappe import msgprint
from frappe.utils import today, now, flt, cint, nowdate, getdate, formatdate, add_to_date
from erpnext.stock.utils import get_latest_stock_qty
from frappe.utils.file_manager import save_file
import json
import re

def get_desuup():
    name = frappe.db.get_value("Desuup", {"cid_number": frappe.auth.get_logged_user()}, "name")
    return name

@frappe.whitelist()
def get_desuup_detail():
    desuup = frappe.get_doc("Desuup", get_desuup())
    desuup.deployment_history = frappe.db.sql("select * from `tabDeployment Entry` where desuup = %(desuup)s", {"desuup": desuup.name}, as_dict=1)
    return desuup

@frappe.whitelist()
def get_announcement_list(dep_type=None):
    filters = {}
    if not dep_type:
        frappe.throw("Type is mandatory")
    desup = frappe.get_doc("Desuup", get_desuup())
    if dep_type == "Skilling":
        for a in frappe.db.sql("select * from `tabBarred Desuup` where desuung_id = %(desuup)s and %(today)s between from_date and to_date and docstatus = 1", {"desuup": desup.name, "today": today()}, as_dict=1):
            frappe.throw("User is barred from skilling activities")

    filters["desupid"] = desup.name
    filters["dep_type"] = dep_type
    additional_cond = set_deployment_conditions(desup, filters)
    doc_list = frappe.db.sql("""
        SELECT a.*, 
            d.status as application_status, 
            d.reason, 
            COALESCE(d.applied, 0) AS applied
        FROM `tabDeployment Announcement` a 
            LEFT JOIN (select deployment_announcement, status, reason, 1 as applied from `tabDeployment Application` where desuup = %(desupid)s and docstatus = 1) d ON d.deployment_announcement = a.name 
        WHERE a.docstatus = 1  {}""".format(additional_cond), filters, as_dict=1)
    for a in doc_list:
        a.by_dzongkhag = frappe.db.sql("select dzongkhag from `tabDeployment Announcement Dzongkhag` where parent = %(d)s", {"d": a.name}, as_dict=1)
        a.by_batch = frappe.db.sql("select batch from `tabDeployment Announcement Batch` where parent = %(d)s", {"d": a.name}, as_dict=1)

    return doc_list

@frappe.whitelist()
def get_deployment_list(dep_type=None):
    if not dep_type:
        frappe.throw("Deployment Type is mandatory")

    filters = {}
    desup = frappe.get_doc("Desuup", get_desuup())
    filters["desupid"] = desup.name
    filters["dep_type"] = dep_type
    filters["deadline"] = getdate(now())
    doc_list = frappe.db.sql("""
        SELECT d.*, di.status 
        FROM `tabDesuup Deployment` d, `tabDeployment Item` di 
        WHERE di.desuup = %(desupid)s 
        and d.docstatus = 1 
        and di.parent = d.name
        and d.type_of_deployment = %(dep_type)s
        and d.end_date > %(deadline)s
        """, filters, as_dict=1)

    return doc_list

@frappe.whitelist()
def apply_for_deployment(deployment_announcement=None):
    if not deployment_announcement:
        frappe.throw("Deployment announcement is required")
    desup = frappe.get_doc("Desuup", get_desuup())
    deploy_app = frappe.new_doc("Deployment Application")
    deploy_app.deployment_announcement = deployment_announcement
    deploy_app.desuup = desup.name
    deploy_app.docstatus = 1
    deploy_app.save(ignore_permissions=True)
    return deploy_app

@frappe.whitelist()
def deregister_from_deployment(announcement, reason):
    if not announcement:
        frappe.throw("Deployment Announcement is mandatory")
    if not reason:
        frappe.throw("Reason is mandatory")
        
    desup = frappe.get_doc("Desuup", get_desuup())
    dep_app = frappe.db.get_value("Deployment Application", {"desuup": desup.name, "deployment_announcement": announcement}, "name")
    if not dep_app:
        frappe.throw("Have you applied for the announcement?")
    app = frappe.get_doc("Deployment Application", dep_app)
    app.db_set("status", "Deregistered")
    app.db_set("reason", str(reason))
    app.db_set("withdraw_date", now(), update_modified=False)

@frappe.whitelist()
def withdraw_from_deployment(deployment, withdrawal_date, reason):
    if not deployment:
        frappe.throw("Deployment is mandatory")
    if not reason:
        frappe.throw("Reason is mandatory")
    if not withdrawal_date:
        frappe.throw("Withdrawal date is mandatory")

    desup = frappe.get_doc("Desuup", get_desuup())
    dep_with = frappe.new_doc("Deployment Withdrawal")
    dep_with.deployment = deployment
    dep_with.withdrawal_date = withdrawal_date
    dep_with.docstatus = 1
    dep_with.save(ignore_permissions=True)
    return dep_with

@frappe.whitelist()
def get_deployment_as_gojay():
    filters = {}
    desup = frappe.get_doc("Desuup", get_desuup())
    filters["gojay"] = desup.name
    filters["end"] = add_to_date(now(), days=-7)
    filters["start"] = now()

    doc_list = frappe.db.sql("""
        SELECT * 
        FROM `tabDesuup Deployment`  
        WHERE completed = 0 and gojay = %(gojay)s and docstatus = 1 and end_date > %(end)s and start_date <= %(start)s""", filters, as_dict=1)
    return doc_list

@frappe.whitelist()
def get_desuups_for_attendance(deployment, date):
    if not deployment or not date:
        frappe.throw("Invalid post parameters")

    desup_list = frappe.db.sql("""select desuup, full_name, cid, gender from `tabDeployment Item`
                where parent = %(deployment)s and %(att_date)s between from_date and to_date
            """, {"deployment": deployment, "att_date": date}, as_dict=True)

    for a in desup_list:
        a.attendance_status = None
        a.name = None
        a.attendance_status = frappe.db.get_value("Desuup Attendance", {"reference_name": deployment, "reference_doctype": "Desuup Deployment", "attendance_date": date, "desuup": a.desuup}, "status")
        a.name = frappe.db.get_value("Desuup Attendance", {"reference_name": deployment, "reference_doctype": "Desuup Deployment", "attendance_date": date, "desuup": a.desuup}, "name")

    return desup_list

@frappe.whitelist()
def submit_attendance(deployment, date, attendance_detail):
    if not deployment or not date or not attendance_detail:
        frappe.throw("Invalid post parameters")
    start, end = frappe.db.get_value("Desuup Deployment", deployment, ["start_date", "end_date"])
    if not start:
        frappe.throw("Invalid deployment id")
    if getdate(date) < getdate(start) or getdate(date) > getdate(end):
        frappe.throw("Invalid date")

    desup_list = frappe.db.sql("""select desuup, full_name, cid, gender from `tabDeployment Item`
                where parent = %(deployment)s
            """, {"deployment": deployment}, as_dict=True)
    desups = [x.desuup for x in desup_list]

    for a in attendance_detail:
        d = a.get('desuup')
        s = a.get('status')
        name = a.get('name')
        if not d and not s and not name:
            frappe.throw("Invalid attendance details")
        if d not in desups:
            frappe.throw("{} wasn't enrolled in this deployment".format(d))

        desup = frappe.get_doc("Desuup", d)
        if not name:
            att = frappe.new_doc("Desuup Attendance")
            att.attendance_for = "Deployment"
            att.status = s
            att.desuup = d
            att.attendance_date = date
            att.reference_doctype = "Desuup Deployment"
            att.reference_name = deployment
            att.submit()
        else:
            att = frappe.get_doc("Desuup Attendance", n)
            att.db_set("status", s)

@frappe.whitelist()
def change_present_address(country, dzongkhag, gewog):
    if not country or not dzongkhag or not gewog:
        frappe.throw("Invalid present address")
    if country:
        if not frappe.db.exists("Country", country):
            frappe.throw("Invalid country")
    if dzongkhag:
        if not frappe.db.exists("Dzongkhags", {"name": dzongkhag, "country_name": country}):
            frappe.throw("Invalid Present Dzongkhag")
    if gewog:
        if not frappe.db.exists("Gewogs", {"name": gewog, "dzongkhag": dzongkhag}):
            frappe.throw("Invalid Present Gewog")
        
    desup = frappe.get_doc("Desuup", get_desuup())
    desup.db_set("present_country", country, update_modified=False)
    desup.db_set("present_dzongkhag", dzongkhag, update_modified=False)
    desup.db_set("present_gewog", gewog, update_modified=False)
    return desup

@frappe.whitelist()
def change_employment_status(employment_type):
    if not employment_type:
        frappe.throw("Invalid employment status")
        
    desup = frappe.get_doc("Desuup", get_desuup())
    desup.db_set("employment_type", employment_type, update_modified=False)
    return desup

@frappe.whitelist()
def change_mobile(mobile):
    if not mobile:
        frappe.throw("Invalid phone number")
    pattern = r'^(17|16|77)\d{6}$'
    if not bool(re.fullmatch(pattern, mobile)):
        frappe.throw("Invalid phone number")
        
    desup = frappe.get_doc("Desuup", get_desuup())
    desup.db_set("mobile_number", mobile, update_modified=False)
    if desup.user:
        user = frappe.get_doc("User", desup.user)
        user.db_set("phone", mobile, update_modified=False)
    return desup

@frappe.whitelist()
def upload_cv():
    file = frappe.request.files.get("file")
    if file:
        desup = frappe.get_doc("Desuup", get_desuup())
        if desup.cv:
            existing_file = frappe.db.sql("select name from tabFile where file_url = %(file)s", {"file": desup.cv}, as_dict=1)
            if existing_file:
                frappe.delete_doc("File", existing_file[0].name, ignore_permissions=True)

        file_doc = upload_file(file, desup.doctype, desup.name) 
        desup.db_set("cv", file_doc.file_url, update_modified=False)
    else:
        frappe.throw("File is mandatory")

@frappe.whitelist()
def upload_profile():
    file = frappe.request.files.get("file")
    if file and file.mimetype.startswith("image/"):
        desup = frappe.get_doc("Desuup", get_desuup())
        if desup.photo:
            existing_file = frappe.db.sql("select name from tabFile where file_url = %(file)s", {"file": desup.cv}, as_dict=1)
            if existing_file:
                frappe.delete_doc("File", existing_file[0].name, ignore_permissions=True)

        file_doc = upload_file(file, desup.doctype, desup.name) 
        desup.db_set("photo", file_doc.file_url, update_modified=False)
    else:
        frappe.throw("An image file is mandatory")

@frappe.whitelist()
def get_dress_requisitions():
    filters = {}
    desup = frappe.get_doc("Desuup", get_desuup())
    filters["desuup"] = desup.name

    doc_list = frappe.db.sql("""
        SELECT * 
        FROM `tabDress Requisition`  
        WHERE desuup = %(desuup)s and docstatus = 1""", filters, as_dict=1)
    return doc_list

@frappe.whitelist()
def apply_dress_requisitions(details):
    desup = frappe.get_doc("Desuup", get_desuup())
    req = frappe.new_doc("Dress Requisition")
    req.desuup = desup.name
    req.details = details
    req.docstatus = 1
    req.save(ignore_permissions=True)
    return req

@frappe.whitelist()
def get_items_for_sale():
    response = dict()
    shop_details = frappe.get_single("Online Shopping Settings")
    if not shop_details.enable or not shop_details.warehouse or not shop_details.items:
        return response 

    response['account_no'] = shop_details.account_no 

    pickup_details = frappe.db.sql("select name from `tabPickup Location` where is_disabled = 0",as_dict=True)
    response['pickup_locations'] = pickup_details

    items_for_sale = list()
    for a in shop_details.items:
        if a.disable:
            continue
        available_qty = get_latest_stock_qty(a.item_code, shop_details.warehouse)
        if not available_qty or cint(available_qty) < 1:
            available_qty = 0
        image = frappe.db.get_value("Item", a.item_code, "image")

        item = {
                "item_code": a.item_code,
                "item_name": a.item_name,
                "qty": available_qty,
                "selling_price": a.selling_price,
                "image": image
                }
        items_for_sale.append(item)
    response['items'] = items_for_sale

    return response

@frappe.whitelist()
def place_order(orders, location):
    if not orders:
        frappe.throw("Invalid orders")
    if not location or not frappe.db.exists("Pickup Location", location):
        frappe.throw("Invalid location")
    file = frappe.request.files.get("file")
    if not file:
        frappe.throw("Journal Screenshot is mandatory")

    desup = frappe.get_doc("Desuup", get_desuup())
    order = frappe.new_doc("Online Order")
    order.posting_date = now()
    order.desuup = desup.name
    order.total_amount = 0 
    order.location = location
    order.journal = "Initial"
    order.insert(ignore_permissions=True)

    file_doc = upload_file(file, order.doctype, order.name) 
    order.journal = file_doc.file_url
    order.docstatus = 1
    for a in json.loads(orders):
        item = a.get('item_code')
        if not item:
            frappe.throw("Invalid Item")
        qty = a.get('qty')
        if not qty or cint(qty) < 1:
            frappe.throw("Invalid Qty")

        order.append("items", {
            "item_code": item,
            "qty": qty
            })
    order.save(ignore_permissions=True)
    return order

@frappe.whitelist()
def get_vacancies():
    desup = frappe.get_doc("Desuup", get_desuup())
    doc_list = frappe.db.sql("""
        SELECT * 
        FROM tabVacancy v
        WHERE published = 1 and application_end_date >= %(date)s
            and (not exists (select 1 from `tabVacancy Dzongkhag` where parent =  %(dzongkhag)s) or exists (select 1 from `tabVacancy Dzongkhag` where dzongkhag = %(dzongkhag)s and parent = v.name)) 
        """, {"date": str(getdate(now())), "dzongkhag": desup.present_dzongkhag}, as_dict=1)

    for a in doc_list:
        app = frappe.db.exists("Job Applicant", {"desuup": desup.name, "vacancy": a.name})
        if app:
            jp = frappe.get_doc("Job Applicant", {"desuup": desup.name, "vacancy": a.name})
            a.job_application = jp.name
            a.application_status = jp.status
            a.reason = jp.reason
        else:
            a.job_application = None 
            a.application_status = None
            a.reason = None

    return doc_list

@frappe.whitelist()
def apply_for_vacancy(vacancy):
    if not vacancy:
        frappe.throw("Invalid vacancy")
    
    if not frappe.db.exists("Vacancy", vacancy):
        frappe.throw("Invalid vacancy")

    desup = frappe.get_doc("Desuup", get_desuup())
    if not desup.cv:
        frappe.throw("Update your CV from the profile")

    application = frappe.new_doc("Job Applicant")
    application.desuup = desup.name
    application.vacancy = vacancy
    application.insert(ignore_permissions=True)

    file = frappe.get_doc("File", {"file_url": desup.cv})
    file_doc = save_file(
                fname=file.file_name,
                content=file.get_content(),
                dt=application.doctype,
                dn=application.name,
                is_private=1
            )
    application.resume_attachment = file_doc.file_url
    application.docstatus = 1
    application.save(ignore_permissions=True)
    return application

@frappe.whitelist()
def get_deployment_attendance(deploy):
    if not deploy or not frappe.db.exists("Desuup Deployment", deploy):
        frappe.throw("Invalid Deployment")
    att_list = frappe.db.sql("select * from `tabDesuup Attendance` where reference_name = %(deployment)s and status != %(present)s and docstatus = 1 and desuup = %(desuup)s", {"deployment": deploy, "status": "Present", "desuup": get_desuup(), "present": "Present"}, as_dict=True)
    return att_list
    
@frappe.whitelist()
def get_enquiries():
    en_list = frappe.db.sql("select * from `tabAbsence Enquiry` where docstatus = 1 and desuup = %(desuup)s", {"desuup": get_desuup()}, as_dict=True)
    return en_list
    
@frappe.whitelist()
def get_enquiries_for_gojay():
    en_list = frappe.db.sql("select t.* from `tabAbsence Enquiry` t, `tabDesuup Deployment` d where d.gojay = %(desuup)s and d.name = t.deployment and t.status = %(status)s and t.docstatus = 1 and d.docstatus = 1", {"desuup": get_desuup(), "status": "Submitted"}, as_dict=True)
    return en_list

@frappe.whitelist()
def action_on_enquiry(enquiry, action):
    if not action or action not in (1, 0):
        frappe.throw("Invalid action on attendance")
    if not enquiry or not frappe.db.exists("Absence Enquiry", enquiry):
        frappe.throw("Invalid Absence Enquiry")
    ab_en = frappe.get_doc("Absence Enquiry", enquiry)
    if action == 0:
        ab_en.db_set("status", "Rejected")
    else:
        ab_en.db_set("status", "Accepted")
        frappe.db.sql("update `tabDesuup Attendance` set status = %(status)s where name = %(name)s", {"status": "Present", "name": ab_en.desuup_attendance})

@frappe.whitelist()
def raise_enquiry(att, enquiry):
    if not att or not frappe.db.exists("Desuup Attendance", att):
        frappe.throw("Invalid attendance record")
    doc = frappe.new_doc("Absence Enquiry")
    doc.desuup_attendance = att
    doc.enquiry = enquiry
    doc.insert(ignore_permissions=True)

    file = frappe.request.files.get("file")
    if file:
        file_doc = upload_file(file, doc.doctype, doc.name) 
        doc.support_doc = file_doc.file_url
    doc.docstatus = 1
    doc.save(ignore_permissions=True)
    return doc

def upload_file(file, doctype, docname, is_private=1):
    if file:
        file_doc = save_file(
                    fname=file.filename,
                    content=file.stream.read(),
                    dt=doctype,
                    dn=docname,
                    is_private=is_private
                )
        return file_doc
    frappe.throw("File is mandatory")

@frappe.whitelist()
def get_orders():
    doc_list = frappe.db.sql("select * from `tabOnline Order` where docstatus = 1 and desuup = %(desuup)s order by posting_date", {"desuup": get_desuup()}, as_dict=1)
    for a in doc_list:
        a.items = frappe.db.sql("select * from `tabOnline Order Item` where parent = %(parent)s", {"parent": a.name}, as_dict=1)
    return doc_list

@frappe.whitelist()
def submit_feedback(feedback):
    doc = frappe.new_doc("System Feedback")
    doc.desuup = get_desuup()
    doc.submitted_on = now()
    doc.feedback = feedback
    doc.docstatus = 1
    doc.save(ignore_permissions=True)
    return doc

@frappe.whitelist()
def get_feedback():
    doc_list = frappe.db.sql("select * from `tabSystem Feedback` where docstatus = 1 and desuup = %(desuup)s order by submitted_on", {"desuup": get_desuup()}, as_dict=1)
    return doc_list

@frappe.whitelist()
def get_messages():
    return frappe.db.sql("select * from tabMessage where docstatus = 1 and desuup = %(desuup)s and seen = 0 order by creation limit 10", {"desuup": get_desuup()}, as_dict=1)

@frappe.whitelist()
def mark_seen(doc_id):
    if not doc_id:
        frappe.throw("Invalid document reference")
    frappe.db.sql("update tabMessage set seen = 1 where name = %(doc_id)s", {"doc_id": doc_id})
    return {"status": "success"}

@frappe.whitelist()
def queue_sms(mobile, message):
    if not mobile:
        frappe.throw("Mobile number is mandatory")
    if not message:
        frappe.throw("Message is mandatory")
    frappe.enqueue(
        "erpnext.custom_utils.send_sms",
        queue="short",
        mobile=mobile,
        message=message
    )

@frappe.whitelist()
def create_desuup(desuup_details):
    if not desuup_details:
        frappe.throw("Desuup details is mandatory")
    frappe.enqueue(
        "erpnext.custom_utils.create_desuup",
        queue="short",
        desuup_details=desuup_details
    )

@frappe.whitelist()
def get_questionaire():
    questionaires = frappe.db.sql("select q.* from tabQuestionaire q where q.is_active = 1 and q.docstatus = 1 and %(today)s between q.from_date and q.to_date and not exists (select 1 from `tabSurvey Response` sr where sr.questionaire = q.name and sr.desuup = %(desuup)s)",{"today": today(), "desuup": get_desuup()}, as_dict=1)
    for a in questionaires:
        a['questions'] = []
        for q in frappe.db.sql("select * from `tabQuestionaire Item` where docstatus = 1 and parent = %(parent)s", {"parent": a.name}, as_dict=1):
            answers = frappe.db.sql("select * from `tabSurvey Question Item` where parent = %(question)s", {"question": q.question}, as_dict=1)
            q['options'] = answers
            a['questions'].append(q)
    return questionaires

@frappe.whitelist()
def submit_questionaire(questionaire, response):
    if not response:
        frappe.throw("Response is mandatory")
    doc = frappe.new_doc("Survey Response")
    doc.questionaire = questionaire
    doc.desuup = get_desuup()

    for a in response:
        question = a.get('question')
        if not question:
            frappe.throw("Invalid question")
        answers = a.get('answers')
        other_text = a.get('other_text')

        doc.append("items", {
            "question_id": question,
            "answer": answers,
            "other_text": other_text
            })
    doc.docstatus = 1
    doc.save(ignore_permissions=True)

@frappe.whitelist()
def get_announcement():
    return frappe.db.sql("select * from tabAnnouncement where status = %(status)s", {"status": "Active"}, as_dict=1)

def set_deployment_conditions(desup, filter):
    additional_conditions = []
    gender = desup.gender
    batch = desup.batch_number
    present_dzo = desup.present_dzongkhag
    employment_type = desup.employment_type

    if gender == "Male":
        additional_conditions.append("(a.by_gender = 0 OR a.male_desuups > 0)")
    else:
        additional_conditions.append("(a.by_gender = 0 OR a.female_desuups > 0)")

    # for batch
    additional_conditions.append("(NOT EXISTS (select 1 from `tabDeployment Announcement Batch` where parent = a.name) OR EXISTS (select 1 from `tabDeployment Announcement Batch` where parent = a.name and batch = %(batch)s)) ")
    filter["batch"] = batch

    # for present dzongkhag
    additional_conditions.append("(NOT EXISTS (select 1 from `tabDeployment Announcement Dzongkhag` where parent = a.name) OR EXISTS (select 1 from `tabDeployment Announcement Dzongkhag` where parent = a.name and dzongkhag = %(present_dzo)s)) ")
    filter["present_dzo"] = present_dzo

    # for emplyement type 
    if employment_type:
        additional_conditions.append("(NULLIF(a.by_employment_status, '') is null OR a.by_employment_status = %(employment_type)s)")
        filter["employment_type"] = employment_type

    # for qualification
    levels = [x.level for x in desup.desuup_qualification_table]
    levels = list(set(levels))
    if levels:
        additional_conditions.append("(NULLIF(a.by_qualification, '') is null OR a.by_qualification IN %(by_qualification)s)")
        filter["by_qualification"] = levels

    # for deployment type 
    additional_conditions.append("a.type_of_deployment = %(dep_type)s")

    # filter only active announcements
    additional_conditions.append("a.registration_deadline >= %(reg_deadline)s")
    filter["reg_deadline"] = getdate(now())

    return " and {}".format(" and ".join(additional_conditions)) if additional_conditions else ""

