import frappe

def execute(filters=None):
	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data

def get_columns(filters=None):
    if not filters.get("individual"):
        return [
		{
			"fieldname": "account",
			"label": "Account",
			"fieldtype": "Data",
			"width": 300
		},
		{
			"fieldname": "credit",
			"label": "Credit",
			"fieldtype": "Currency",
			"width": 300
		},
		{
			"fieldname": "debit",
			"label": "debit",
			"fieldtype": "Currency",
			"width": 300
		},
		{
			"fieldname": "total",
				"label": "Total",
			"fieldtype": "Currency",
			"width": 300
			},
		# {
			# 	"fieldname": "advance",
			# 	"label": "Advance",
			# 	"fieldtype": "Data",
			# 	"width": 200
			# },
			# {
			# 	"fieldname": "payable",
			# 	"label": "Payable",
			# 	"fieldtype": "Data",
			# 	"width": 200
			# },
			# {
			# 	"fieldname": "cost_center",
			# 	"label": "Cost Center",
			# 	"fieldtype": "Data",
			# 	"width": 200
			# }
		]
    else:
        return [
		{
				"fieldname": "account",
				"label": "Account",
				"fieldtype": "Data",
				"width": 250
		},
		{
				"fieldname": "party",
				"label": "Party",
				"fieldtype": "Data",
				"width": 250
		},
		{
				"fieldname": "party_type",
				"label": "Party Type",
				"fieldtype": "Data",
				"width": 200
		},
			{
				"fieldname": "credit",
				"label": "Credit",
				"fieldtype": "Currency",
				"width": 150
		},
		{
				"fieldname": "debit",
				"label": "debit",
				"fieldtype": "Currency",
				"width": 150
		},
		{
				"fieldname": "total",
				"label": "Total",
				"fieldtype": "Currency",
				"width": 150
		},
		]
		

def get_data(filters):
	conditions = get_conditions(filters)
	if not filters.get("individual"):
		# query = '''
		# 	SELECT s.suppier_category AS suppliertype,     
		# 	SUM(gl.credit) AS total,     
		# 	SUM(gl.debit) AS advance,     
		# 	SUM(gl.credit - gl.debit) AS payable,
   		# 	gl.cost_center FROM     
		# 	`tabGL Entry` AS gl
		# 	left join `tabSupplier` s on s.name=gl.party 
		# 	WHERE gl.account="21.101 - Sundry Creditors"
		# 	and gl.is_cancelled=0 
		# 	group by s.suppier_category;
		# '''
		query = '''
			SELECT gl.account, sum(gl.credit) as credit, sum(gl.debit) as debit, sum(gl.credit-gl.debit) as total  FROM       
   			`tabGL Entry` AS gl INNER JOIN `tabAccount` AS a ON gl.account = a.name left join 
      		`tabSupplier` s on s.name=gl.party WHERE   a.parent_account = "21.100 - Account Payable" 
        	and gl.is_cancelled=0 {conditions} group by gl.account;
		'''.format(conditions=conditions)
		data = frappe.db.sql(query, as_dict=1)
		return data
	else:
		query = '''
			SELECT
			gl.party AS suppliertype,
			gl.credit AS total,
			gl.debit AS advance,
			(gl.credit - gl.debit) AS payable,
			gl.cost_center 
			FROM
			`tabGL Entry` AS gl
			LEFT JOIN
			`tabSupplier` AS s ON s.name = gl.party
			WHERE
			gl.account = "21.101 - Sundry Creditors"
			AND gl.is_cancelled = 0 {conditions}
   			group by gl.party;
		'''.format(conditions=conditions)
		query='''
			SELECT gl.account as account, gl.party as party, gl.party_type as party_type,sum(gl.credit) as credit, 
   			sum(gl.debit) as debit, sum(gl.credit-gl.debit) as total
 			FROM `tabGL Entry` AS gl INNER JOIN `tabAccount` AS a ON gl.account = a.name left join        
    		`tabSupplier` s on s.name=gl.party WHERE   a.parent_account = "21.100 - Account Payable"          
      		and gl.is_cancelled=0 {conditions}
        	group by gl.party
		'''.format(conditions=conditions)
		data = frappe.db.sql(query, as_dict=1)
		return data
	 
def get_conditions(filters):
	conditions = []
	if filters and filters.get("supplier"):
		conditions.append("s.suppier_category = '{}'".format(filters.get("supplier")))
	if filters and filters.get("cost_center"):
		conditions.append("gl.cost_center = '{}'".format(filters.get("cost_center")))
	

	return "AND {}".format(" AND ".join(conditions)) if conditions else ""