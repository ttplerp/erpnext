import frappe
from barcode import Code128
import pandas as pd

def check_ignore_budget():
    accs = frappe.db.sql("""
        select name from `tabAccount`
    """,as_dict = 1)
    for a in accs:
        frappe.db.sql("update `tabAccount` set budget_check = 1 where name = '{}'".format(a.name))
        print(a.name)

def export_department_division():
    datas = []
    department = frappe.db.sql("""
        select name from `tabDepartment` where is_department = 1
    """,as_dict=1)
    for a in department:
        divisions = frappe.db.sql("""
            select name from `tabDepartment` where is_division = 1 and parent_department = '{}'
        """.format(a.name),as_dict=1)
        datas.append({"Department":a.name, "Division":""})
        for b in divisions:
            datas.append({"Department":"", "Division":b.name})
    df = pd.DataFrame(data = datas) # convert dict to dataframe
    df.to_excel("Department and Divsion Link.xlsx", index=False)
    print("Dictionary Converted in to Excel")

def update_asset_barcode():
    assets = frappe.db.sql("""
        select name from `tabAsset` where docstatus = 1 and asset_barcode is NULL
    """,as_dict=1)
    for a in assets:
        bc = Code128(str(a.name))
        path = bc.save(str(a.name))
        frappe.db.sql("update `tabAsset` set asset_barcode = '{}' where name = '{}'".format(path, a.name))
        print(path)

# def update_asset_barcode():
#     asset = frappe.get_doc("Asset",'RCPL-F&F-22-0073')
# 	file = open('{}'.format(self.asset_barcode)).read()
#     asset.db_set("barcode_image",file)
