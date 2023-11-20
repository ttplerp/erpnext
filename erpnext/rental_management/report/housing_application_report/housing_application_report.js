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
				"Corporate Employee",
                "Private Employee",
                 "Others"
			]
        },
        {
            'fieldname': 'work_station',
            'label': 'Work Station',
            'fieldtype': 'Select',
            'options':[
                "Gasa",
                "Trongsa",
                "Trashigang",
                "Sarpang",
                "Tsirang",
                "Samdrup Jongkhar",
                "Dagana",
                "Zhemgang",
                "Paro",
                "Chhukha",
                "Mongar",
                "Samtse",
                "Trashi Yangtse",
                "Lhuentse",
                "Thimphu",
                "Pema Gatshel",
                "Wangdue Phodrang",
                "Haa",
                "Punakha",
                "Bumthang"
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
				"Cancelled"
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
