# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import date_diff, getdate, ceil, flt
from frappe.model.mapper import get_mapped_doc
from erpnext.custom_utils import queue_sms

class DesuupDeployment(Document):
    def validate(self):
        self.generate_code()

    def generate_code(self):
        if self.deployment_code:
            return
        type_abbr = frappe.db.get_value("Type of Event", self.event, "abbreviation")
        cat_abbr = frappe.db.get_value("Category of Deployment", self.category, "abbreviation")
        gwg_abbr = frappe.db.get_value("Gewogs", self.gewog, "code")
        date = getdate(self.start_date)
        month = date.month
        year = date.strftime("%y")
        code = str(type_abbr) + "-" + str(cat_abbr) + "-" + str(gwg_abbr) + " : " + str(month) + "/" + str(year)  
        num = frappe.db.sql("select count(1) as num from `tabDesuup Deployment` where deployment_code LIKE %(dep_code)s and name != %(name)s", {"dep_code": f"%{code}%", "name": self.name}, as_dict=1)
        self.deployment_code = code + "-" + str(num[0].num)

    def on_submit(self):
        self.update_applicants()
        self.update_announcement()

    def update_applicants(self):
        for a in self.items:
            if a.manual_replace:
                frappe.throw("Click on shortlist applicants again as you wanted to replace desuups")
            app = frappe.get_doc("Deployment Application", a.deployment_application)
            app.db_set("status", "Accepted")
            if app.mobile_number:
                queue_sms(app.mobile_number, "You had been selected for {}. Check for details on Desuung App".format(self.deployment_code))

        for a in self.standbys:
            app = frappe.get_doc("Deployment Application", a.deployment_application)
            app.db_set("status", "Standby")

        automark = frappe.db.get_single_value("Desuup Settings", "automark_not_selected")
        if not automark:
            return

        selected = [s.deployment_application for s in self.items]
        standby = [s.deployment_application for s in self.standbys]
        selectedstandbys = tuple(selected + standby)
        others = frappe.db.sql("select name from `tabDeployment Application` where name not in {names} and status = 'Applied' and docstatus = 1 and deployment_announcement = %(dn)s".format(names=selectedstandbys), {"dn": self.deployment_announcement} , as_dict=1)
        for a in others:
            doc = frappe.get_doc("Deployment Application", a.name)
            doc.db_set("status", "Not Selected")

    def update_announcement(self):
        if self.deployment_announcement:
            doc = frappe.get_doc("Deployment Announcement", self.deployment_announcement)
            doc.db_set("deployment_created", 1 if self.docstatus == 1 else 0)

    @frappe.whitelist()
    def get_applicants(self):
        deploy = frappe.get_doc("Deployment Announcement", self.deployment_announcement)
        removed_items = [
                    item.deployment_application for item in self.items if item.get("manual_replace") == 1]
        to_remove = tuple(removed_items)
        for a in removed_items:
            frappe.db.sql("update `tabDeployment Application` set status = 'Not Selected' where name = %(name)s", {"name": a})

        remove_query = ""
        if removed_items:
            remove_query = """
                AND a.name not in %(to_remove)s
            """

        applicants = dict()
        columns = "name, desuup_name, mobile_number, email_id, desuup, cid, gender, batch"
        if deploy.by_gender == 0:
            applicants = frappe.db.sql(f""" 
                    SELECT distinct 
                    name, desuup_name, mobile_number, email_id, desuup, cid, gender, batch, creation
                    FROM `tabDeployment Application` a 
                    WHERE status = 'Applied' and docstatus = 1 and deployment_announcement = %(da)s 
                        AND NOT EXISTS (
                            SELECT 1
                            FROM `tabDeployment Application` a2
                            WHERE a2.desuup = a.desuup
                              AND a2.status = 'Accepted'
                              AND a2.docstatus = 1
                              AND a2.start_date <= a.end_date
                              AND a2.end_date >= a.start_date
                          )
                          {remove_query}
                    GROUP BY desuup
                    ORDER BY creation asc limit %(limit)s
                """, {"columns": columns, "da": self.deployment_announcement, "limit": deploy.total_desuups, "to_remove": to_remove}, as_dict=1)    
        else:
            male = frappe.db.sql(f"""
                    select distinct 
                    name, desuup_name, mobile_number, email_id, desuup, cid, gender, batch, creation
                    from `tabDeployment Application` a where status  = 'Applied' and docstatus = 1 and deployment_announcement = %(da)s and gender = %(gender)s 
                        AND NOT EXISTS (
                            SELECT 1
                            FROM `tabDeployment Application` a2
                            WHERE a2.desuup = a.desuup
                              AND a2.status = 'Accepted'
                              AND a2.docstatus = 1
                              AND a2.start_date <= a.end_date
                              AND a2.end_date >= a.start_date
                          )
                          {remove_query}
                    GROUP BY desuup
                    order by creation asc limit %(limit)s
                """, {"columns": columns, "da": self.deployment_announcement, "gender": "Male", "limit": deploy.male_desuups, "to_remove": to_remove}, as_dict=1)
            female = frappe.db.sql(f"""
                    select distinct 
                    name, desuup_name, mobile_number, email_id, desuup, cid, gender, batch, creation
                    from `tabDeployment Application` a where status  = 'Applied' and docstatus = 1 and deployment_announcement = %(da)s and gender = %(gender)s  
                        AND NOT EXISTS (
                            SELECT 1
                            FROM `tabDeployment Application` a2
                            WHERE a2.desuup = a.desuup
                              AND a2.status = 'Accepted'
                              AND a2.docstatus = 1
                              AND a2.start_date <= a.end_date
                              AND a2.end_date >= a.start_date
                          )
                          {remove_query}
                    GROUP BY desuup
                    order by creation asc limit %(limit)s
                """, {"columns": columns, "da": self.deployment_announcement, "gender": "Female", "limit": deploy.female_desuups, "to_remove": to_remove}, as_dict=1)
            applicants = male + female 
        self.set('items', [])

        for d in applicants:
            d.full_name = d.desuup_name
            d.deployment_application = d.name
            d.phone = d.mobile_number
            d.email = d.email_id
            d.applied_at = d.creation
            d.from_date = self.start_date
            d.to_date = self.end_date
            d.name = None
            row = self.append('items', {})
            row.update(d)

        standby_percent = frappe.db.get_single_value("Desuup Settings", "shortlist_percent")
        standbys = dict()
        columns = "name, desuup_name, mobile_number, email_id, desuup, cid, gender, batch"
        if deploy.by_gender == 0:
            standby_num = ceil(flt(standby_percent/100) * flt(deploy.total_desuups))
            standbys = frappe.db.sql(f""" 
                    select distinct 
                    name, desuup_name, mobile_number, email_id, desuup, cid, gender, batch, creation
                    from `tabDeployment Application` a where status = 'Applied' and docstatus = 1 and deployment_announcement = %(da)s 
                        AND NOT EXISTS (
                            SELECT 1
                            FROM `tabDeployment Application` a2
                            WHERE a2.desuup = a.desuup
                              AND a2.status = 'Accepted'
                              AND a2.docstatus = 1
                              AND a2.start_date <= a.end_date
                              AND a2.end_date >= a.start_date
                          )
                          {remove_query}
                    GROUP BY desuup
                    order by creation asc 
                    limit %(num)s offset %(limit)s
                """, {"columns": columns, "da": self.deployment_announcement, "num": standby_num, "limit": deploy.total_desuups, "to_remove": to_remove}, as_dict=1)    
        else:
            standby_male = ceil(flt(standby_percent/100) * flt(deploy.male_desuups))
            male_standby = frappe.db.sql(f"""
                    select distinct 
                    name, desuup_name, mobile_number, email_id, desuup, cid, gender, batch, creation
                    from `tabDeployment Application` a where status  = 'Applied' and docstatus = 1 and deployment_announcement = %(da)s and gender = %(gender)s 
                        AND NOT EXISTS (
                            SELECT 1
                            FROM `tabDeployment Application` a2
                            WHERE a2.desuup = a.desuup
                              AND a2.status = 'Accepted'
                              AND a2.docstatus = 1
                              AND a2.start_date <= a.end_date
                              AND a2.end_date >= a.start_date
                          )
                          {remove_query}
                    GROUP BY desuup
                    order by creation asc
                    limit %(num)s offset %(limit)s
                """, {"columns": columns, "da": self.deployment_announcement, "gender": "Male", "num": standby_male, "limit": deploy.male_desuups, "to_remove": to_remove}, as_dict=1)
            standby_female = ceil(flt(standby_percent/100) * flt(deploy.female_desuups))
            female_standby = frappe.db.sql(f"""
                    select distinct 
                    name, desuup_name, mobile_number, email_id, desuup, cid, gender, batch, creation
                    from `tabDeployment Application` a where status  = 'Applied' and docstatus = 1 and deployment_announcement = %(da)s and gender = %(gender)s  
                        AND NOT EXISTS (
                            SELECT 1
                            FROM `tabDeployment Application` a2
                            WHERE a2.desuup = a.desuup
                              AND a2.status = 'Accepted'
                              AND a2.docstatus = 1
                              AND a2.start_date <= a.end_date
                              AND a2.end_date >= a.start_date
                          )
                          {remove_query}
                    GROUP BY desuup
                    order by creation asc 
                    limit %(num)s offset %(limit)s
                """, {"columns": columns, "da": self.deployment_announcement, "gender": "Female", "num": standby_female, "limit": deploy.female_desuups, "to_remove": to_remove}, as_dict=1)
            standbys = male_standby + female_standby 
        self.set('standbys', [])

        for d in standbys:
            d.full_name = d.desuup_name
            d.deployment_application = d.name
            d.phone = d.mobile_number
            d.email = d.email_id
            d.applied_at = d.creation
            d.name = None
            row = self.append('standbys', {})
            row.update(d)

@frappe.whitelist()
def complete_deployment(source_name, target_doc=None):
    doclist = get_mapped_doc(
        "Desuup Deployment",
        source_name,
        {
            "Desuup Deployment": {"doctype": "Complete Deployment", "validation": {"docstatus": "1"}},
            "field_map": {"deployment": "name"}
        },
        target_doc,
    )

    return doclist
