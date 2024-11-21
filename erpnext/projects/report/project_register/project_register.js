/* 
--------------------------------------------------------------------------------------------------------------------------
Version		 	Author		  				CreatedOn		 	ModifiedOn		  	Remarks
------------ --------------- ------------------ -------------------  -----------------------------------------------------
1.0		      	Dawa Nyuehtyue Tshering		2024/11/20			2024/11/21			Original Version
--------------------------------------------------------------------------------------------------------------------------
*/

frappe.query_reports["Project Register"] = {
	"filters": [
        {
			"fieldname": 	"project",
			"label": 		("Project"),
			"fieldtype": 	"Link",
			"options":		"Project"			
		},
		{
			"fieldname": 	"branch",
			"label": 		("Branch"),
			"fieldtype": 	"Link",
			"options":		"Branch"
		},
		{
			"fieldname": 	"cost_center",
			"label": 		("Cost Center"),
			"fieldtype": 	"Link",
			"options":		"Cost Center"
		},		
		{
			"fieldname":	"from_date",
			"label":		("From Date"),
			"fieldtype":	"Date",
			"reqd":0
		},
		{
			"fieldname":	"to_date",
			"label":		("To Date"),
			"fieldtype":	"Date",
			"reqd":0
		},
		// {
		// 	"fieldname":	"additional_info",
		// 	"label":		("Additional Information"),
		// 	"fieldtype":	"Check",
		// 	"reqd":			0
		// },	
	]
};
