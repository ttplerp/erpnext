'''
--------------------------------------------------------------------------------------------------------------------------
Version		 	Author		  				CreatedOn		 	ModifiedOn		  	Remarks
------------ --------------- ------------------ -------------------  -----------------------------------------------------
1.0		      	Dawa Nyuehtyue Tshering		2024/11/20			2024/11/21			Original Version
--------------------------------------------------------------------------------------------------------------------------
'''

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt, cint,add_days, cstr, flt, getdate, nowdate, rounded, date_diff

def execute(filters=None):
	columns = get_columns(filters)
	data    = get_data(filters)
	return columns, data

def get_columns(filters):
        if filters.get("additional_info"):
            cols = [
                        {"fieldtype": "Link",	"fieldname": "project", "label": _("Project"),  "options": "Project", "width": 200},
		        {"fieldtype": "Data",	"fieldname": "project_name", "label": _("Project Name"), "width": 200},
                        {"fieldtype": "Link",	"fieldname": "cost_center", "label": _("Cost Center"), "options": "Cost Center", "width": 180},
                        {"fieldtype": "Link",	"fieldname": "project_type", "label": _("Project Type"), "options": "Project Type", "width": 120},
                        {"fieldtype": "Link",	"fieldname": "party_type", "label": _("Party Type"), "options": "DocType", "width": 100},
			{"fieldtype": "Dynamice Link",	"fieldname": "party", "label": _("Party"), "options": "party_type", "width": 150},
                        {"fieldtype": "Percent","fieldname": "progress", "label": _("Progress"), "width": 120},
                        {"fieldtype": "Date",	"fieldname": "expected_start_date","label": _("Start Date"),  "width": 120},
		        {"fieldtype": "Date",	"fieldname": "expected_end_date", "label": _("End Date"),  "width": 120},
		        {"fieldtype": "Float",	"fieldname": "project_value", "label": _("Project Value (Nu.)"),  "width": 200},
		        {"fieldtype": "Float",	"fieldname": "advance_amount", "label": _("Advance Amount (Nu.)"),  "width": 200},
		        {"fieldtype": "Float",	"fieldname": "advance_adjusted", "label": _("Advance Adjusted (Nu.)"),  "width": 200},
                    
			{"fieldtype": "Data",	"fieldname": "status", "label": _("Status"), "width": 110},
                   
                #     ("Physical Progress")   + ":Percent:120",
                #     ("Status")              + ":Data:120",
                #     ("Exp Start Date")      + ":Date:120",
                #     ("Exp End Date")        + ":Date:120",
                #     ("Advance")             + ":Currency:120",
                #     ("Project Value (A)")   + ":Currency:120",
                #     ("Price Adj (B)")       + ":Currency:120",
                #     ("Advance Adj (C)")     + ":Currency:120",
                #     ("TDS (D)")             + ":Currency:120",
                #     ("Other Ded (E)")       + ":Currency:120",
                #     ("Received (F)")        + ":Currency:120",
                #     ("Balance(A+B-C-D-E-F)")+ ":Currency:150",
                #     ("Created By")          + ":Data:120",
                #     ("Created Date")        + ":Date:120",
                #     ("Modified By")         + ":Data:120",
                #     ("Modified Date")       + ":Date:120"
                ]
        else:
            cols = [
                        {"fieldtype": "Link",	"fieldname": "project", "label": _("Project"),  "options": "Project", "width": 200},
		        {"fieldtype": "Data",	"fieldname": "project_name", "label": _("Project Name"), "width": 200},
			{"fieldtype": "Link",	"fieldname": "cost_center", "label": _("Cost Center"), "options": "Cost Center", "width": 180},
                        {"fieldtype": "Link",	"fieldname": "project_type", "label": _("Project Type"), "options": "Project Type", "width": 120},
                        {"fieldtype": "Link",	"fieldname": "party_type", "label": _("Party Type"), "options": "DocType", "width": 100},
			{"fieldtype": "Dynamice Link",	"fieldname": "party", "label": _("Party"), "options": "party_type", "width": 150},
		        {"fieldtype": "Percent","fieldname": "progress", "label": _("Progress"), "width": 120},
		        {"fieldtype": "Float",	"fieldname": "project_value", "label": _("Project Value (Nu.)"),  "width": 200},
                        {"fieldtype": "Date",	"fieldname": "expected_start_date","label": _("Start Date"),  "width": 120},
		        {"fieldtype": "Date",	"fieldname": "expected_end_date", "label": _("End Date"),  "width": 120},
			{"fieldtype": "Data",	"fieldname": "status", "label": _("Status"), "width": 110},
                ]

        return cols

def get_data(filters):
        cond  = get_conditions(filters)
        if filters.get("additional_info"):
            query = """
                    select 
                        name as project,
                        project_name,
                        cost_center,
                        project_type,
                        party_type,
                        party,
                            percent_complete as progress,
                            ifnull(project_value, 0) as project_value,
                            expected_start_date,
                            expected_end_date,
                            status,
                            owner,
                            creation,
                            modified_by,
                            modified
                    from `tabProject` p
                    {0}
                    order by creation desc
            """.format(cond)
        else:
            query = """
                    select  
                        name as project,
                        project_name,
                        cost_center,
                        project_type,
                        party_type,
                        party,
                        percent_complete as progress,
                        ifnull(project_value, 0) as project_value,
                        expected_start_date,
                        expected_end_date,
                        status,
                        creation
                    from `tabProject` p
                    {0}
                    order by creation desc
            """.format(cond)                

        if filters.get("additional_info"):
            data  = []
            result = frappe.db.sql(query, as_dict=1)
            
            for r in result:
                advance_amount   = 0.0
                advance_adjusted = 0.0
                price_adjustment = 0.0
                tds_amount       = 0.0
                other_ded        = 0.0
                payment_received = 0.0

                # advance_amount
                advance_amount, advance_adjusted = frappe.db.sql("""
                                        select
                                                sum(ifnull(received_amount,0)) as received_amount,
                                                sum(ifnull(adjusted_amount,0)) as adjusted_amount
                                        from  `tabProject Advance`
                                        where project   = "{0}"
                                        and   docstatus = 1
                                """.format(r.name))[0]

                # price_adjustment, tds_amount, other_ded, payment_received
                price_adjustment, tds_amount, other_ded, payment_received = frappe.db.sql("""
                    select
                        sum(ifnull(price_adjustment_amount,0)) as price_adjustment_amount,
                        sum(ifnull(tds_amount,0)) as tds_amount,
                        sum(ifnull(total_deduction_amount,0)) as other_ded,
                        sum(ifnull(net_amount-outstanding_amount,0)) as payment_received
                    from  `tabProject Invoice`
                    where project   = "{0}"
                    and   docstatus = 1
                        """.format(r.name))[0]
                data.append((
                        r.project,
                        r.project_name,
                        r.cost_center,
                        r.project_type,
                        r.party_type,
                        r.party,
                        r.progress,
                        r.expected_start_date,
                        r.expected_end_date,
                        flt(r.project_value),
                        flt(advance_amount),
                        flt(advance_adjusted),
                        r.status,
                        flt(tds_amount),
                        flt(other_ded),
                        flt(payment_received),
                        (flt(r.project_value)+flt(price_adjustment)-flt(advance_adjusted)-flt(tds_amount)-flt(other_ded)-flt(payment_received)),
                        r.branch,
                        r.cost_center,
                        r.owner,
                        r.creation,
                        r.modified_by,
                        r.modified
                ))
            return tuple(data)
        else:
            return frappe.db.sql(query)
        

def get_conditions(filters):
        cond = []

        if filters.get("project"):
                cond.append('name = "{0}"'.format(filters.get("project")))

        if filters.get("branch"):
                cond.append('branch = "{0}"'.format(filters.get("branch")))

        if filters.get("cost_center"):
                cond.append('cost_center = "{0}"'.format(filters.get("cost_center")))

        if filters.get("from_date"):
                cond.append("expected_start_date >= \'{0}\'".format(str(filters.get("from_date"))))

        if filters.get("to_date"):
                cond.append("expected_end_date <= \'{0}\'".format(str(filters.get("to_date"))))
        
        if cond:
                query = str("where ")+str(" and ".join(cond))
        else:
                query = ""

        return query
