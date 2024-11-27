// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Vacant Flats Report"] = {
	"filters": [
		{
            'fieldname': 'building_classification',
            'label': 'Building Classification',
            'fieldtype': 'Link',
            'options': 'Building Classification',
			
        },
	]
};
