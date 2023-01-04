# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt
'''
--------------------------------------------------------------------------------------------------------------------------
Version          Author          CreatedOn          ModifiedOn          Remarks
------------ --------------- ------------------ -------------------  -----------------------------------------------------
1.0		  		Phuntsho		March,05,2021                       	Calaculate the fuel balance amount using POL Entry
--------------------------------------------------------------------------------------------------------------------------                                                                          
'''

from __future__ import unicode_literals
import frappe
from frappe import throw, _
from frappe.utils import flt

def execute(filters=None):
    columns =  get_column(filters)
    data = get_data(filters)
    return columns, data

def get_column(filters): 
    return [
        _("Date") + ":Date:120",
        _("Logbook/POL Entry") + ":Link/Vehicle Logbook: 120",
        _("Type ") + ":Data:120",
        _("Equipment ") + ":Link/Equipment:120",
        _("Equipment Type") + ":Data:100",
        _("Registration No.") + ":Data:100",
        _("Initial KM") + ":Float:100",
        _("Final KM") + ":Float:100",
        _("Total KM") + ":Float:100",
        _("POL Received") + ":Float:100",
        _("Opening Balance") + ":Float:100",
        _("Total Consumption") + ":Float:100",
        _("Balance") + ":Float:100",
        #("From Date") + ":Date:120",
        #("To Date") + ":Date:120",
        _("From Place") + ":Data:120",
        _("To Place") + ":Data:120",
        _("Purpose") + ":Data:120",
    ]

def get_data(filters): 	
    data = get_vehicle_logbook_details(filters)
    #frappe.msgprint(str(data))
    pol_receive = get_pol_receive_entries(filters)
    final_data = []
    for item in pol_receive: 
        final_data.append([ item.date,item.name,"POL Entry",item.equipment,item.equipment_type,item.equipment_number,"","","",item.qty,"","","","","",""])
        
    
    for item in data: 
        # POL received and consumed respectively
        received_so_far = frappe.db.sql("""
            SELECT 
                sum(qty) as sum 
            FROM 
                `tabPOL Entry` 
            WHERE 
                equipment = '{equipment}' and 
                date <= '{date}' and 
                type='Receive' and 
                docstatus=1 """.format(equipment=item.equipment,date=item.date),as_dict=True)
        
        consumed_so_far =  frappe.db.sql ("""
            SELECT sum(qty) as sum FROM `tabPOL Entry` 
            WHERE equipment = '{equipment}' and date < '{date}' and type='consumed' and docstatus=1 """.format(equipment=item["equipment"],date=item["date"]),as_dict=True)

        if not received_so_far[0]['sum']: received_so_far[0]['sum'] = 0 
        if not consumed_so_far[0]['sum']: consumed_so_far[0]['sum'] = 0

        opening = received_so_far[0]['sum'] - consumed_so_far[0]['sum']
        balance = opening - item["total_consumption"]
        balance = flt(balance)

        final_data.append([
            item.date,
            item.name,
            "Vehicle Logbook",
            item.equipment,
            item.equipment_type,
            item.registration_number,
            item.initial_km,
            item.final_km,
            item.total_km_run,
            "",
            opening,
            item.total_consumption,
            balance,
            #item.to_date,
            item.from_place,
            item.to_place,
            item.purpose,
        ])

    #final_data.sort(key= lambda x: x[10]) # sort the final list based on from date
    return final_data


def get_pol_receive_entries (filters): 
    # from_date = to_date = ""
    # if (filters.get("from_date")): 
    # 	from_date = "and pe.date >= '{}'".format(filters.get("from_date"))
    # if (filters.get("to_date")): 
    # 	to_date = "and pe.date <= '{}'".format(filters.get("to_date"))

    pol_entry = frappe.db.sql("""
        SELECT 
            pe.name,
            pe.equipment, 
            pe.date, 
            pe.qty, 
            e.equipment_type,
            e.equipment_number
        FROM 
            `tabPOL Entry` as pe,
            `tabEquipment` as e
        WHERE 
            e.name = pe.equipment and
            pe.type = "Receive" and
            pe.equipment = '{}' and
            pe.date between '{}' and '{}'
        ORDER BY
            pe.date ASC
        """.format(filters.get("equipment_no"), filters.get("from_date"), filters.get("to_date")), as_dict=True)
   # frappe.msgprint(str(pol_entry))
    return pol_entry


def get_vehicle_logbook_details(filters):
    """
        get details from vehicle logbook
    """
    # from_date = to_date = ""
    # if (filters.get("from_date")): 
    # 	from_date = "and vlog.date >= '{}'".format(filters.get("from_date"))
    # if (filters.get("to_date")): 
    # 	to_date = "and vlog.date <= '{}'".format(filters.get("to_date"))

    data = frappe.db.sql("""
        SELECT 
            vl.name, 
            vl.equipment , 
            vlog.initial_km , 
            vlog.final_km , 
            vlog.total_km_run , 
            vlog.total_consumption ,
            vl.equipment_type, 
            vl.registration_number, 
            vlog.date,
            vlog.from_place, 
            vlog.to_place, 
            vlog.purpose 
        FROM `tabVehicle Logbook` as vl, `tabVehicle Log` as vlog
        WHERE vlog.parent = vl.name and vl.docstatus = 1 and vl.equipment = '{0}'
        AND vlog.date BETWEEN '{1}' and '{2}' 
        ORDER BY vlog.date ASC """.format(filters.get("equipment_no"), filters.get("from_date"), filters.get("to_date")),as_dict=True
    )
    return data
