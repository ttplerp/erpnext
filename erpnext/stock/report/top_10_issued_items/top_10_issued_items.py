# Import necessary modules  
import frappe  
from frappe.utils import flt  

def execute(filters=None):  
    if filters is None:  # Ensure filters is a dictionary  
        filters = {}  
    
    # Retrieve filters for display (this is the definition)  
    filter_options = get_filters()  
    
    columns = get_columns()  
    data = get_data(filters)  # Pass filters directly to get_data  
    
    return columns, data, filter_options  # Return columns, data, and filter display options  

def get_columns():  
    return [  
        # {"label": "Sales Invoice", "fieldname": "sales_invoice", "fieldtype": "Link", "options": "Sales Invoice", "width": "150"},  
        {"label": "Item Code", "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": "400"},  
        {"label": "Item Name", "fieldname": "item_name", "fieldtype": "Data", "width": "300"},  
        {"label": "Quantity", "fieldname": "quantity", "fieldtype": "Float", "width": "150"},  
        {"label": "Price", "fieldname": "price", "fieldtype": "Currency", "options": "currency", "width": "150"},  
    ]  

def get_data(filters):  
    # Prepare SQL query with conditions based on filters  
    conditions = ""  
    if filters.get("from_date"):  
        conditions += " AND si.posting_date >= %(from_date)s"  
    if filters.get("to_date"):  
        conditions += " AND si.posting_date <= %(to_date)s"  
    if filters.get("source_warehouse"):  
        conditions += " AND si_item.warehouse = %(source_warehouse)s"   
    if filters.get("material_code"):  
        conditions += " AND si_item.item_code = %(material_code)s"  
    if filters.get("branch"):  
        conditions += " AND si.branch = %(branch)s"  

    # Query to get top 10 items based on quantity  
    data = frappe.db.sql(f"""  
        SELECT   
            si_item.parent AS sales_invoice,  
            si_item.item_code,  
            si_item.item_name,  
            SUM(si_item.qty) AS quantity,  
            si_item.rate AS price  
        FROM   
            `tabSales Invoice Item` AS si_item  
        LEFT JOIN  
            `tabSales Invoice` AS si  
        ON  
            si_item.parent = si.name  
        WHERE  
            si.docstatus = 1  
            {conditions}  
        GROUP BY  
            si_item.item_code  
        ORDER BY  
            quantity DESC  
        LIMIT 10  
    """, filters, as_dict=True)
    
    return data  

def get_filters():  
    return [    
        {  
            "fieldname": "from_date",  
            "label": "From Date",  
            "fieldtype": "Date",  
            "default": "",  
        },  
        {  
            "fieldname": "to_date",  
            "label": "To Date",  
            "fieldtype": "Date",  
            "default": "",  
        },  
        {  
            "fieldname": "source_warehouse",  
            "label": "Source Warehouse",  
            "fieldtype": "Link",  
            "options": "Warehouse",  
            "default": "",  
        },   
        {  
            "fieldname": "material_code",  
            "label": "Material Code",  
            "fieldtype": "Link",  
            "options": "Item",  
            "default": "",  
        },  
        {
			"fieldname": "branch",
			"label": "Branch",
			"fieldtype": "Link",
			"width": "80",
			"options": "Branch",
            "default": "",
		},
    ]  

def get_purpose_options():  
    # This function should return a list of purpose options  
    return ["Project", "Sales", "Purchase"]  # Example options