import frappe

def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data

def get_columns():
	return [
		{
			"fieldname": "suppliertype",
			"label": "Supplier Type/Supplier",
			"fieldtype": "Data",
			"width": 300
		},
		{
			"fieldname": "total",
			"label": "Total",
			"fieldtype": "Data",
			"width": 160
		},
		{
			"fieldname": "advance",
			"label": "Advance",
			"fieldtype": "Data",
			"width": 200
		},
		{
			"fieldname": "payable",
			"label": "Payable",
			"fieldtype": "Data",
			"width": 200
		}
	]

def get_data(filters):
	conditions = get_conditions(filters)
	if not filters.get("individual"):
		query = '''
			SELECT s.supplier_type AS suppliertype,     
			SUM(gl.credit) AS total,     
			SUM(gl.debit) AS advance,     
			SUM(gl.credit - gl.debit) AS payable FROM     
			`tabGL Entry` AS gl
			left join `tabSupplier` s on s.name=gl.party 
			WHERE gl.account="21.101 - Sundry Creditors"
			and gl.is_cancelled=0 
			group by s.supplier_type ;
		'''
		data = frappe.db.sql(query, as_dict=1)
		return data
	else:
		query = '''
			SELECT
			gl.party AS suppliertype,
			gl.credit AS total,
			gl.debit AS advance,
			(gl.credit - gl.debit) AS payable
			FROM
			`tabGL Entry` AS gl
			LEFT JOIN
			`tabSupplier` AS s ON s.name = gl.party
			WHERE
			gl.account = "21.101 - Sundry Creditors"
			AND gl.is_cancelled = 0 {conditions}
   			group by gl.party;
		'''.format(conditions=conditions)
		data = frappe.db.sql(query, as_dict=1)
		return data
	 
def get_conditions(filters):
	conditions = []
	if filters and filters.get("supplier"):
		conditions.append("s.supplier_type = '{}'".format(filters.get("supplier")))
	

	return "AND {}".format(" AND ".join(conditions)) if conditions else ""