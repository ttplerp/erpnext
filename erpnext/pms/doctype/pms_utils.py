import frappe
from frappe import _
from frappe.utils import nowdate, date_diff, getdate,flt
from datetime import datetime

def send_email_notification():
    recipients = get_recipients()
    pms = frappe.defaults.get_user_default('fiscal_year')
    target_start_date, target_end_date,review_start_date, review_end_date, evaluation_start_date,evaluation_end_date= frappe.db.get_value('PMS Calendar',{'name':pms},['target_start_date','target_end_date','review_start_date','review_end_date','evaluation_start_date','evaluation_end_date'])
   
    msg = ''
    sub = ''
    day = flt(date_diff(nowdate(),target_start_date))
    if flt(day) == 0 :
        sub = "Target Set Up"
        msg = """
        <p>Dear All</p><br/>
        <p>Target setup starts from {} till {} for the year {}. Visit following link to set your target https://erp.thimphutechpark.bt/</p>
        
        """.format(target_start_date,target_end_date,pms)
        send_mail(recipients,msg,sub)
    
    day = flt(date_diff(nowdate(),review_start_date))
    if flt(day) == 0 :
        sub = "Review Target"
        msg = """
        <p>Dear All</p><br/>
        <p>Review for your target starts from {} till {} for the year {}. Visit following link to review your target https://erp.thimphutechpark.bt/</p>
        """.format(review_start_date,review_end_date,pms)
        send_mail(recipients,msg,sub)
        
    day = flt(date_diff(nowdate(),review_start_date))
    if flt(day) == 0 :
        sub = "Evaluate Target"
        msg = """
        <p>Dear All</p><br/>
        <p>Evaluation for your target starts from {} till {} for the year {}. Visit following link to evaluate your target https://erp.thimphutechpark.bt/</p>
        """.format(evaluation_start_date,evaluation_end_date,pms)
        send_mail(recipients,msg,sub)

    diff = flt(date_diff(target_end_date,nowdate()))
    if flt(diff) == 1:
        sub = "Target Set Up"
        msg = """
        <p>Dear All</p><br/>
        <p>This is gentle reminder that only {} days left for target setup</p>
        """.format(int(diff))
        send_mail(recipients,msg,sub)
    
    diff = flt(date_diff(review_end_date,nowdate()))
    if flt(diff) == 1:
        sub = "Target Review"
        msg = """
        <p>Dear All</p><br/>
        <p>This is gentle reminder that only {} days left for target review</p>
        """.format(int(diff))
        send_mail(recipients,msg,sub)
    
    diff = flt(date_diff(review_end_date,nowdate()))
    if flt(diff) == 1:
        sub = "Target Evaluation"
        msg = """
        <p>Dear All</p><br/>
        <p>This is gentle reminder that only {} days left for target evaluation</p>
        """.format(int(diff))
        send_mail(recipients,msg,sub)
    
def send_mail(recipients, message, subject):
    try:
       frappe.sendmail(
                recipients=recipients,
				subject=_(subject),
				message= _(message)
			)
    except:
        pass
    
def get_recipients():
    users = []
    for u in frappe.db.get_values("Employee", fieldname=["user_id"],
                filters={"status": "Active"},
                as_dict=True
            ):
        if u.user_id :
            users.append(u.user_id)
    return users
