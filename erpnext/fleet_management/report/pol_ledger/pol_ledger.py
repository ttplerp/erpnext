# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt, get_datetime
from erpnext.fleet_management.fleet_utils import get_pol_till, get_pol_consumed_till
from collections import defaultdict
import datetime

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_data(filters=None):
    conditions = []
    params = {}
    query = """
        SELECT 
            pe.name,
            pe.posting_date,
            pe.posting_time,
            pe.branch,
            pe.equipment,
            pe.pol_type,
            pe.qty,
            pe.type,
            pe.reference_type,
            pe.reference,
            pe.reference_name,
            i.item_name,
            i.stock_uom,
            e.equipment_type,
            et.is_container
        FROM `tabPOL Entry` pe
        LEFT JOIN `tabItem` i ON i.name = pe.pol_type
        LEFT JOIN `tabEquipment` e ON e.name = pe.equipment
        LEFT JOIN `tabEquipment Type` et ON et.name = e.equipment_type
        WHERE pe.docstatus = 1
    """
    
    if filters:
        if filters.get("from_date") and filters.get("to_date"):
            conditions.append("pe.posting_date BETWEEN %(from_date)s AND %(to_date)s")
            params["from_date"] = filters.from_date
            params["to_date"] = filters.to_date
        
        if filters.get("branch"):
            conditions.append("pe.branch = %(branch)s")
            params["branch"] = filters.branch

        if filters.get("equipment"):
            conditions.append("pe.equipment = %(equipment)s")
            params["equipment"] = filters.equipment
    
    if conditions:
        query += " AND " + " AND ".join(conditions)
    
    query += " ORDER BY pe.posting_date, pe.posting_time"
    
    pol_entries = frappe.db.sql(query, params, as_dict=True)
    
    if not pol_entries:
        return []
    
    # Get all reference documents in batch
    reference_names = {}
    for entry in pol_entries:
        if entry.reference_type == "POL Receive" and entry.reference:
            key = f"{entry.reference_type}::{entry.reference}"
            reference_names[key] = {
                "reference_type": entry.reference_type,
                "reference": entry.reference
            }
    
    direct_consumption_map = {}
    if reference_names:
        ref_list = list(reference_names.values())
        for ref_group in chunk_list(ref_list, 50):  
            ref_conditions = []
            ref_params = {}
            for i, ref in enumerate(ref_group):
                ref_conditions.append(f"(name = %(ref_name_{i})s)")
                ref_params[f"ref_name_{i}"] = ref["reference"]
            
            if ref_conditions:
                dc_query = f"""
                    SELECT name, direct_consumption 
                    FROM `tabPOL Receive`
                    WHERE {" OR ".join(ref_conditions)}
                """
                dc_results = frappe.db.sql(dc_query, ref_params, as_dict=True)
                for dc in dc_results:
                    direct_consumption_map[dc.name] = "Yes" if dc.direct_consumption else "No"
    
    opening_balances = defaultdict(float)
    if filters and filters.get("from_date"):
        equipment_pol_combos = set()
        for entry in pol_entries:
            equipment_pol_combos.add((entry.equipment, entry.pol_type, entry.is_container))
        
        for equipment, pol_type, is_container in equipment_pol_combos:
            if is_container == 1:
                balance_query = """
                    SELECT 
                        SUM(CASE WHEN type = 'Stock' THEN qty ELSE 0 END) as total_stock,
                        SUM(CASE WHEN type = 'Issue' THEN qty ELSE 0 END) as total_issue
                    FROM `tabPOL Entry`
                    WHERE docstatus = 1
                        AND equipment = %(equipment)s
                        AND pol_type = %(pol_type)s
                        AND (posting_date < %(from_date)s OR 
                            (posting_date = %(from_date)s AND posting_time <= '00:00'))
                """
                balance_result = frappe.db.sql(balance_query, {
                    "equipment": equipment,
                    "pol_type": pol_type,
                    "from_date": filters.from_date
                }, as_dict=True)
                
                if balance_result:
                    opening_balances[f"{equipment}|{pol_type}"] = flt(balance_result[0].total_stock) - flt(balance_result[0].total_issue)
    
    data = []
    running_balances = defaultdict(float)
    
    for key, value in opening_balances.items():
        running_balances[key] = value
    
    for entry in pol_entries:
        trans_qty = -flt(entry.qty) if entry.type == "Issue" else flt(entry.qty)
        
        balance_key = f"{entry.equipment}|{entry.pol_type}"
        
        running_balances[balance_key] += trans_qty
        
        dc = direct_consumption_map.get(entry.reference, "No")
        row = frappe._dict({
            "posting_date": get_datetime(f"{entry.posting_date} {entry.posting_time}"),
            "branch": entry.branch,
            "equipment": entry.equipment,
            "item_name": entry.item_name,
            "trans_qty": trans_qty,
            "balance": running_balances[balance_key] if entry.is_container == 1 else 0,
            "type": entry.type,
            "reference_type": entry.reference_type,
            "reference": entry.reference,
            "direct_comsumption": dc
        })
        data.append(row)
    
    return data

def chunk_list(lst, chunk_size):
    """Split list into chunks of specified size"""
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]

def get_columns():
    return [
        {"fieldname": "posting_date", "fieldtype": "Datetime", "width": 150, "label": "Posting Date"},
        {"fieldname": "branch", "fieldtype": "Link", "width": 130, "label": "Branch", "options": "Branch"},
        {"fieldname": "equipment", "fieldtype": "Link", "width": 120, "label": "Equipment", "options": "Equipment"},
        {"fieldname": "item_name", "fieldtype": "Data", "width": 100, "label": "Item Name"},
        {"fieldname": "trans_qty", "fieldtype": "Float", "width": 100, "label": "Qty", "precision": 2},
        {"fieldname": "balance", "fieldtype": "Float", "width": 100, "label": "Tanker Balance", "precision": 2},
        {"fieldname": "type", "fieldtype": "Data", "width": 100, "label": "Type"},
        {"fieldname": "reference_type", "fieldtype": "Data", "width": 100, "label": "Reference Type"},
        {"fieldname": "reference", "fieldtype": "Dynamic Link", "width": 100, "label": "Reference", "options": "reference_type"},
        {"fieldname": "direct_comsumption", "fieldtype": "Data", "width": 100, "label": "Is Direct Consumption"},
    ]