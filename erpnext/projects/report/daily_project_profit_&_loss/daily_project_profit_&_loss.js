frappe.query_reports["Daily Project Profit & Loss"] = {
	"filters": [
		{
			fieldname: "project",
			label: __("Project"),
			fieldtype: "Link",
			options: "Project",
		},
		{
			"fieldname": "cost_center",
			"label": __("Cost Center"),
			"fieldtype": "Link",
			options: "Cost Center",
		},
		{
			"fieldname": "date",
			"label": __("Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.nowdate(),
			"reqd": 1,
		},
	],
	"formatter": function(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (column.id == "profit_loss") {
			if (data["profit_loss"] > 0) {
				value = `<p style="color: blue; font-weight: bold">${value}</p>`;
			} else if (data["profit_loss"] < 0) {
				value = `<p style="color: red; font-weight: bold">${value}</p>`;
			} else {
				value = `<p style="color: gray; font-weight: normal">${value}</p>`;
			}
		}
		return value;
	}
};
