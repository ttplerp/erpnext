# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import flt, cint, getdate, add_days, get_datetime, datetime
from erpnext.custom_utils import check_uncancelled_linked_doc
import datetime
from frappe.model.mapper import get_mapped_doc
# from datetime import date
class VehicleLogbook(Document):
    def validate(self):
        self.validate_date()
        #self.set_data()
        self.check_dates()
        self.check_double_vl()
        # self.check_hire_form()
        # self.check_duplicate()
        self.update_consumed()
        self.calculate_totals()
        self.update_operator()
        self.check_consumed()	
        self.calculate_grand_totals()
        self.calculate_total_days()
        

    def validate_date(self):
        pass
        # if self.posting_date > str(datetime.datetime.now()): 
        # 	frappe.throw("Cannot post for Future Date")
        #         from_date = get_datetime(str(self.from_date) + ' ' + str(self.from_time))
        #         to_date = get_datetime(str(self.to_date) + ' ' + str(self.to_time))
        #         if to_date < from_date:
        #                 frappe.throw("From Date/Time cannot be greater than To Date/Time")

    def set_data(self):
        if not self.ehf_name:
            frappe.throw("Equipment Hire Form is mandatory")
        self.customer_type = frappe.db.get_value("Equipment Hiring Form", self.ehf_name, "private")
        self.customer = frappe.db.get_value("Equipment Hiring Form", self.ehf_name, "customer")

    def check_consumed(self):
        if self.include_hour or self.include_km:
            if flt(self.consumption) <= 0:
                frappe.throw("Total consumption cannot be zero or less")

    def on_update(self):
        self.calculate_balance()

    def on_submit(self):
        #self.check_double_vl()
        self.update_consumed()
        #self.calculate_totals()
        self.post_pol_entry()
        #self.check_consumption()
        self.update_hire()
        #self.post_equipment_status_entry()
        #self.check_tank_capacity()
        
    
    # by phuntsho on march 13 2021. 
    # submit pol entry with every logbook for ease of generating vehicle history report. 
    def post_pol_entry(self): 
        for item in self.vlogs: 
            doc = frappe.new_doc("POL Entry")
            doc.flags.ignore_permissions = 1 
            doc.branch = self.branch
            doc.company = "De-Suung"
            doc.equipment = self.equipment
            doc.pol_type = "100268" #TODO: NEED TO ACTUALLY FETCH THIS FROM SOMEWHERE
            #doc.date = item.from_date
            doc.date = item.date
            doc.posting_time = self.posting_date
            doc.qty = item.total_consumption
            doc.reference_type = "Vehicle Logbook"
            doc.reference_name = self.name
            doc.type = "consumed"
            doc.is_opening = 0 
            doc.own_cost_center = 1
            doc.submit()
        # for item in self.vlogs: 
        # 	doc = frappe.new_doc("POL Entry")
        # 	doc.flags.ignore_permissions = 1 
        # 	doc.branch = self.branch
        # 	doc.company = "De-Suung"
        # 	doc.equipment = self.equipment
        # 	doc.pol_type = "100268" #TODO: NEED TO ACTUALLY FETCH THIS FROM SOMEWHERE
        # 	#doc.date = item.from_date
        # 	doc.date = item.date
        # 	doc.posting_time = self.from_time
        # 	doc.qty = item.total_consumption
        # 	doc.reference_type = "Vehicle Logbook"
        # 	doc.reference_name = self.name
        # 	doc.type = "consumed"
        # 	doc.is_opening = 0 
        # 	doc.own_cost_center = 1
        # 	doc.submit()


    def on_cancel(self):
        self.cancel_pol_entry()
        check_uncancelled_linked_doc(self.doctype, self.name)
        #frappe.db.sql("delete from `tabEquipment Status Entry` where ehf_name = \'"+str(self.name)+"\'")
    def cancel_pol_entry(self): 
        frappe.db.sql("update `tabPOL Entry` set docstatus=2 where reference_name='{}' and reference_type='Vehicle Logbook'".format(self.name))

    def check_dates(self):
        if getdate(self.from_date) > getdate(self.to_date):
            frappe.throw("From Date cannot be smaller than To Date")

        if getdate(self.from_date).month != getdate(self.to_date).month:
                        frappe.throw("From Date and To Date should be in the same month")

    def check_hire_form(self):
        if self.ehf_name:
            docstatus = frappe.db.get_value("Equipment Hiring Form", self.ehf_name, "docstatus")
            if docstatus != 1:
                frappe.throw("Cannot create Vehicle Logbook without submitting Hire Form")
        try:
            name = frappe.db.sql("select name from `tabHiring Approval Details` where parent = %s and equipment = %s", (self.ehf_name, self.equipment))[0]
        except:
            frappe.throw("Make sure the equipment you selected is in the corresponding hire form")	

    def update_operator(self):
        self.equipment_operator = frappe.db.get_value("Equipment", self.equipment, "current_operator")

    def check_duplicate(self):		
        for a in self.vlogs:
            for b in self.vlogs:
                if a.date == b.date and a.idx != b.idx:
                    frappe.throw("Duplicate Dates in Vehicle Logs in row " + str(a.idx) + " and " + str(b.idx))

    def update_consumed(self):
        pol_type = frappe.db.get_value("Equipment", self.equipment, "hsd_type")
        closing = frappe.db.sql("select closing_balance, to_date from `tabVehicle Logbook` where docstatus = 1 and equipment = %s and to_date <= %s order by to_date desc limit 1", (self.equipment, self.from_date), as_dict=True)

        if closing:
            qty = frappe.db.sql("select sum(qty) as qty from `tabConsumed POL` where equipment = %s and date between %s and %s and docstatus = 1 and pol_type = %s", (self.equipment, add_days(closing[0].to_date, 1), self.to_date, pol_type), as_dict=True)
        else:
            qty = frappe.db.sql("select sum(qty) as qty from `tabConsumed POL` where equipment = %s and date <= %s and docstatus = 1 and pol_type = %s", (self.equipment, self.to_date, pol_type), as_dict=True)
        if qty:
            self.hsd_received = qty[0].qty

    def calculate_totals(self):
        # commented out by phuntsho since there is no such field in the child table
        # if self.vlogs:
            # total_w = total_i = 0
            # for a in self.vlogs:
            # 	total_w += flt(a.work_time)
            # 	total_i += flt(a.idle_time)
            # self.total_work_time = total_w
            # self.total_idle_time = total_i

        if self.include_km:
            if flt(self.ys_km) > 0:
                self.consumption_km = flt(self.distance_km) / flt(self.ys_km)

        if self.include_hour:
            self.consumption_hours = flt(self.ys_hours) * flt(self.total_work_time)
        
        self.consumption = flt(self.other_consumption) + flt(self.consumption_hours) + flt(self.consumption_km)
        self.closing_balance = flt(self.hsd_received) + flt(self.opening_balance) - flt(self.consumption)

    def update_hire(self):
        #if self.ehf_name:
        #	doc = frappe.get_doc("Equipment Hiring Form", self.ehf_name)
        #	doc.db_set("hiring_status", 1)
        e = frappe.get_doc("Equipment", self.equipment)

        if self.final_km:
            self.check_repair(cint(e.current_km_reading), cint(self.final_km))
            e.db_set("current_km_reading", flt(self.final_km))

        if self.final_hour:
            self.check_repair(cint(e.current_hr_reading), cint(self.final_hour))
            e.db_set("current_hr_reading", flt(self.final_hour))

    def post_equipment_status_entry(self):
        doc = frappe.new_doc("Equipment Status Entry")
        doc.flags.ignore_permissions = 1 
        doc.equipment = self.equipment
        doc.reason = "Hire"
        doc.ehf_name = self.name
        doc.from_date = self.from_date
        doc.to_date = self.to_date
        doc.hours = self.total_work_time
        doc.to_time = self.to_time
        doc.from_time = self.from_time
        doc.submit()

    def calculate_balance(self):
        self.db_set("closing_balance", flt(self.opening_balance) + flt(self.hsd_received) - flt(self.consumption))

    def check_repair(self, start, end):
        et, em, branch = frappe.db.get_value("Equipment", self.equipment, ["equipment_type", "equipment_model", "branch"])
        interval = frappe.db.get_value("Hire Charge Parameter", {"equipment_type": et, "equipment_model": em}, "interval")
        if interval:
            for a in xrange(start, end):
                if (flt(a) % flt(interval)) == 0:
                    mails = frappe.db.sql("select email from `tabRegular Maintenance Item` where parent = %s", branch, as_dict=True)
                    for b in mails:
                        subject = "Regular Maintenance for " + str(self.equipment)
                        message = "It is time to do regular maintenance for equipment " + str(self.equipment) + " since it passed the hour/km reading of " + str(a) 
                        if b.email:
                            try:
                                frappe.sendmail(recipients=b.email, sender=None, subject=subject, message=message)
                            except:
                                pass
                    break

    def check_tank_capacity(self):
        em = frappe.db.get_value("Equipment", self.equipment, "equipment_model")
        tank = frappe.db.get_value("Equipment Model", em, "tank_capacity") 
        if tank:
            if flt(tank) < flt(self.closing_balance):
                frappe.msgprint("Closing balance cannot be greater than the tank capacity (" + str(tank) + ")")

    def check_double_vl(self):
        pass
        # from_datetime = str(get_datetime(str(self.from_date) + ' ' + str(self.from_time)))
        #         to_datetime = str(get_datetime(str(self.to_date) + ' ' + str(self.to_time)))

        #         query = "select name from `tabVehicle Logbook` where equipment = '{equipment}' and docstatus in (1, 0) and ('{from_date}' between concat(from_date, ' ', from_time) and concat(to_date, ' ', to_time) OR '{to_date}' between concat(from_date, ' ', from_time) and concat(to_date, ' ', to_time) OR ( '{from_date}' <= concat(from_date, ' ', from_time) AND '{to_date}' >= concat(to_date, ' ', to_time) )) and name != '{vl_name}'" .format(from_date=from_datetime, to_date=to_datetime, vl_name=self.name, equipment=self.equipment)
        #         result = frappe.db.sql(query, as_dict=1)
        # # frappe.msgprint("this is the result of existing logbook : {}".format(result))
        # for a in result:
        #	frappe.throw("The logbook for the same equipment, date, and time has been created at " + str(a.name))

    def check_consumption(self):
        no_own_fuel_tank = frappe.db.get_value("Equipment Type", frappe.db.get_value("Equipment", self.equipment, "equipment_type"), "no_own_tank")
        if no_own_fuel_tank:
            return
        if self.customer_type == "CDCL":
            if flt(self.consumption_km) == 0 and flt(self.consumption_hours) == 0 and flt(self.consumption) == 0:
                self.check_condition()	
        else:
            if self.rate_type == "Without Fuel":
                if flt(self.consumption_km) > 0 or flt(self.consumption_hours) > 0:
                    frappe.throw("Should not have consumption when on dry hire to outside customers")
            else:
                if flt(self.consumption_km) == 0 and flt(self.consumption_hours) == 0 and flt(self.consumption) == 0:
                    self.check_condition()	

    def check_condition(self):
        if self.include_km or self.include_hour:
            if self.include_km and self.initial_km == self.final_km:
                pass
            elif self.include_hour and self.initial_hour == self.final_hour:
                pass
            else:
                frappe.throw("Consumption is Mandatory")
        else:
            frappe.throw("Consumption is Mandatory")

    def calculate_grand_totals(self): 
        total_km_run = 0
        total_consumption = 0
        for item in self.vlogs:
            if item.total_km_run is None:
                item.total_km_run = 0.0
                total_km_run += item.total_km_run
            if item.total_consumption is None:
                item.total_consumption = 0.0
                total_consumption += item.total_consumption
            total_km_run += item.total_km_run
            total_consumption += item.total_consumption
        self.grand_total_km = total_km_run
        self.grand_total_fuel_consumption = total_consumption
        # for item in self.vlogs:
        #     if (item.total_km_run or item.total_consumption) is None:
        #         item.total_km_run, item.total_consumption = 0, 0
        #         total_km_run += item.total_km_run 
        #         total_consumption += item.total_consumption
        # self.grand_total_km = total_km_run
        # self.grand_total_fuel_consumption = total_consumption
    
    def calculate_total_days(self): 
        get_days = frappe.db.sql("""select 
                                    count(distinct(vlog.date))
                                    from `tabVehicle Logbook` as vl,`tabVehicle Log` as vlog 
                                    where vl.name=vlog.parent and vl.name='{}'""".format(self.name))
        self.total_days = get_days[0][0]

@frappe.whitelist()
def get_opening(equipment, from_date, to_date, pol_type):
    if not pol_type:
        frappe.throw("Set HSD type in Equipment")

    closing = frappe.db.sql("select name, closing_balance, to_date, final_km, final_hour from `tabVehicle Logbook` where docstatus = 1 and equipment = %s and to_date <= %s order by to_date desc, to_time desc limit 1", (equipment, from_date), as_dict=True)

    if closing:
        qty = frappe.db.sql("select sum(qty) as qty from `tabConsumed POL` where equipment = %s and date between %s and %s and docstatus = 1 and pol_type = %s", (equipment, add_days(closing[0].to_date, 1), to_date, pol_type), as_dict=True)
    else:
        qty = frappe.db.sql("select sum(qty) as qty from `tabConsumed POL` where equipment = %s and date <= %s and docstatus = 1 and pol_type = %s", (equipment, to_date, pol_type), as_dict=True)

    c_km = frappe.db.sql("select final_km from `tabVehicle Logbook` where docstatus = 1 and equipment = %s and to_date <= %s order by to_date desc limit 1", (equipment, from_date), as_dict=True)

    c_hr = frappe.db.sql("select final_hour from `tabVehicle Logbook` where docstatus = 1 and equipment = %s and to_date <= %s order by to_date desc limit 1", (equipment, from_date), as_dict=True)
    result = []
    if closing:
        result.append(closing[0].closing_balance)
        result.append(closing[0].final_km)
        result.append(closing[0].final_hour)
    else:
        result.append(0)
        result.append(0)
        result.append(0)

    if qty:
        result.append(qty[0].qty)
    else:
        result.append(0)

    '''if c_km:
        result.append(c_km[0].final_km)
    else:
        result.append(0)

    if c_hr:
        result.append(c_hr[0].final_hour)
    else:
        result.append(0)'''

    return result

@frappe.whitelist()
def get_vehicle_request_details(vehicle_request):
    return(frappe.db.sql("""
        SELECT
            from_date, 
            to_date, 
            equipment, 
            equipment_type,
            branch
        FROM 
            `tabVehicle Request` 
        WHERE
            name = '{vechicle_request_name}'
    """.format(vechicle_request_name= vehicle_request)))

@frappe.whitelist()
def get_equipment_hiring_form(equipment, from_date,  to_date): 
    # TODO : need to convert the from date and to date to date format, currently its in datetime format.
    from_date = datetime.datetime.strptime(from_date, '%Y-%m-%d %H:%M:%S')
    to_date = datetime.datetime.strptime(to_date, '%Y-%m-%d %H:%M:%S')
    return (frappe.db.sql("""
        SELECT
            name
        FROM 
            `tabEquipment Hiring Form`
        WHERE 
            equipment  = '{}' and 
            start_date = '{}' and
            end_date = '{}'
    """.format(equipment, from_date.date(), to_date.date())))



@frappe.whitelist()
def prepare_hire_charge_invoice(source_name, target_doc=None):
    def update_docs(obj, target, source_parent):
        target.vehicle_logbook = obj.name
    doc = get_mapped_doc("Vehicle Logbook", source_name,{
        "Vehicle Logbook": {
            "doctype": "Hire Charge Invoice", "field_map": {
                "equipment_hiring_form": "ehf_name"

            },
            "postprocess": update_docs,
            "validation": {"docstatus": ["=", 1]}
        },
    }, target_doc)
    return doc