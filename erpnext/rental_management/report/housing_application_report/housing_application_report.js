// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Housing Application Report"] = {
	"filters": [
		{
            'fieldname': 'application_date_time',
            'label': 'Application Date',
            'fieldtype': 'Date',
            'options': 'Application Date',
			
        },
		
		 {
            'fieldname': 'employment_type',
            'label': 'Employment Type',
            'fieldtype': 'Select',
            'options': [
				"Civil Servant",
				"Corporation, Private and etc",
			]
        },
        {
            'fieldname': 'work_station',
            'label': 'Work Station',
            'fieldtype': 'Select',
            options : [
                "Bumthang",
                "Chhukha",
                "Dagana",
                "Gasa",
                "Haa",
                "Lhuentse",
                "Mongar",
                "Paro",
                "Pema Gatshel",
                "Punakha",
                "Samdrup Jongkhar",
                "Samtse",
                "Sarpang",
                "Thimphu",
                "Trashi Yangtse",
                "Trashigang",
                "Trongsa",
                "Tsirang",
                "Wangdue Phodrang",
                "Zhemgang"
            ]
            
            
        },  
    {
            'fieldname': 'application_status',
            'label': 'Application Status',
            'fieldtype': 'Select',
            'options': [
				"pending",
				"Allotted",
				"Rejected",
				"Withdrawn",
				"Cancelled",
                "Not Eligible",
                "Resigned/Superannuated"
			]
        },
    
      {
            'fieldname': 'building_classification',
            'label': 'Eligible Building Classification',
            'fieldtype': 'Link',
            'options': 'Building Classification',
            // 'Link': 'Building Classification'
        },
	]
};
