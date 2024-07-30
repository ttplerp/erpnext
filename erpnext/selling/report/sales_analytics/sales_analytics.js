// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Sales Analytics"] = {
	onload:function(query_report){
		if  (query_report.get_filter_values("tree_type").tree_type == "Customer"){
			// frappe.query_report.toggle_filter_display('item_code', false);
			frappe.query_report.toggle_filter_display('territory', false);
			frappe.query_report.toggle_filter_display('country', false);
			frappe.query_report.toggle_filter_display('customer_group', false);
		}else{
			// frappe.query_report.toggle_filter_display('item_code', true);
			frappe.query_report.toggle_filter_display('territory', true);
			frappe.query_report.toggle_filter_display('country', true);
			frappe.query_report.toggle_filter_display('customer_group', true);
		}
		query_report.refresh()
	},
	"filters": [
		{
			fieldname: "tree_type",
			label: __("Tree Type"),
			fieldtype: "Select",
			options: ["Customer Group", "Customer", "Item Group", "Item", "Territory", "Order Type", "Project"],
			default: "Item",
			reqd: 1,
			on_change: function(query_report){
				if  (query_report.get_filter_values("tree_type").tree_type == "Customer"){
					// frappe.query_report.toggle_filter_display('item_code', false);
					frappe.query_report.toggle_filter_display('territory', false);
					frappe.query_report.toggle_filter_display('country', false);
					frappe.query_report.toggle_filter_display('customer_group', false);
				}else{
					// frappe.query_report.toggle_filter_display('item_code', true);
					frappe.query_report.toggle_filter_display('territory', true);
					frappe.query_report.toggle_filter_display('country', true);
					frappe.query_report.toggle_filter_display('customer_group', true);
				}
				query_report.refresh()
			}
		},
		{
			fieldname: "doc_type",
			label: __("based_on"),
			fieldtype: "Select",
			options: ["Sales Order","Delivery Note","Sales Invoice"],
			default: "Sales Invoice",
			reqd: 1
		},
		{
			fieldname: "value_quantity",
			label: __("Value Or Qty"),
			fieldtype: "Select",
			options: [
				{ "value": "Value", "label": __("Value") },
				{ "value": "Quantity", "label": __("Quantity") },
			],
			default: "Quantity",
			reqd: 1
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.defaults.get_user_default("year_start_date"),
			reqd: 1
		},
		{
			fieldname:"to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.defaults.get_user_default("year_end_date"),
			reqd: 1
		},
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: "De-suung Skilling",
			reqd: 1
		},
		{
			fieldname: "range",
			label: __("Range"),
			fieldtype: "Select",
			options: [
				{ "value": "Weekly", "label": __("Weekly") },
				{ "value": "Monthly", "label": __("Monthly") },
				{ "value": "Quarterly", "label": __("Quarterly") },
				{ "value": "Yearly", "label": __("Yearly") }
			],
			default: "Monthly",
			reqd: 1
		},
		// {
		// 	fieldname: "item_code",
		// 	label: __("Material Code"),
		// 	fieldtype: "Link",
		// 	options: "Item",
		// },
		{
			fieldname: "territory",
			label: __("Territory"),
			fieldtype: "Link",
			options: "Territory",
		},
		{
			fieldname: "country",
			label: __("Country"),
			fieldtype: "Link",
			options: "Country",
		},
		{
			fieldname: "customer_type",
			label: __("Customer Type"),
			fieldtype: "Select",
			options: ["","International Customer","Company","Domestic Customer"],
		},
		{
			"fieldname":"pos_profile",
			"label": __("POS Profile"),
			"fieldtype": "Link",
			"options": "POS Profile"
		}
	],
	get_datatable_options(options) {
		return Object.assign(options, {
			checkboxColumn: true,
			events: {
				onCheckRow: function (data) {
					if (!data) return;
					const data_doctype = $(
						data[2].html
					)[0].attributes.getNamedItem("data-doctype").value;
					const tree_type = frappe.query_report.filters[0].value;
					if (data_doctype != tree_type) return;

					const row_name = data[2].content;
					const raw_data = frappe.query_report.chart.data;
					const new_datasets = raw_data.datasets;
					const element_found = new_datasets.some(
						(element, index, array) => {
							if (element.name == row_name) {
								array.splice(index, 1);
								return true;
							}
							return false;
						}
					);
					const slice_at = { Customer: 4, Item: 5 }[tree_type] || 3;

					if (!element_found) {
						new_datasets.push({
							name: row_name,
							values: data
								.slice(slice_at, data.length - 1)
								.map(column => column.content),
						});
					}

					const new_data = {
						labels: raw_data.labels,
						datasets: new_datasets,
					};
					const new_options = Object.assign({}, frappe.query_report.chart_options, {data: new_data});
					frappe.query_report.render_chart(new_options);

					frappe.query_report.raw_chart_data = new_data;
				},
			},
		});
	},
};
