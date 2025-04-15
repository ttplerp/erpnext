// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Non Capitalized Asset Movement', {
	setup: function(frm) {
		frm.set_query("to_employee", "items", (doc) => {
			return {
				filters: {
					company: doc.company,
				},
			};
		});
		frm.set_query("from_employee", "items", (doc) => {
			return {
				filters: {
					company: doc.company,
				},
			};
		});
		frm.set_query("asset", "items", (doc) => {
			return {
				filters: {
					branch: doc.branch,
				},
			};
		});

		// frm.set_query("asset", "items", () => {
		// 	return {
		// 		filters: {
		// 			status: ["not in", ["Draft"]],
		// 		},
		// 	};
		// });
	},

	onload: (frm) => {
		frm.ignore_doctypes_on_cancel_all = ["Unvalued Asset"];
		frm.trigger("set_required_fields");
	},
	
	refresh: function(frm) {
		if (frm.doc.docstatus != 1 && !frm.is_new()) {
			frm.add_custom_button(__("Get Asset"), function () {
				frm.events.get_asset_details(frm);
			}).toggleClass("btn-primary", !(frm.doc.items || []).length);
		}
	},

	get_asset_details: function (frm) {
		return frappe
			.call({
				doc: frm.doc,
				method: "fill_asset_details",
				freeze: true,
				freeze_message: __("Fetching Asset"),
			})
			.then((r) => {
				if (r.docs?.[0]?.items) {
					frm.dirty();
					frm.save();
				}

				frm.refresh();
				frm.scroll_to_field("items");
			});
	},

	purpose: (frm) => {
		frm.trigger("set_required_fields");
	},

	set_required_fields: (frm, cdt, cdn) => {
		let fieldnames_to_be_altered;
		if (frm.doc.purpose === "Transfer") {
			fieldnames_to_be_altered = {
				target_location: { read_only: 0, reqd: 1 },
				source_location: { read_only: 1, reqd: 1 },
				from_employee: { read_only: 1, reqd: 0 },
				to_employee: { read_only: 1, reqd: 0 },
			};
		} else if (frm.doc.purpose === "Receipt") {
			fieldnames_to_be_altered = {
				target_location: { read_only: 0, reqd: 1 },
				source_location: { read_only: 1, reqd: 0 },
				from_employee: { read_only: 0, reqd: 0 },
				to_employee: { read_only: 1, reqd: 0 },
			};
		} else if (frm.doc.purpose === "Issue") {
			fieldnames_to_be_altered = {
				target_location: { read_only: 1, reqd: 0 },
				source_location: { read_only: 1, reqd: 0 },
				from_employee: { read_only: 1, reqd: 0 },
				to_employee: { read_only: 0, reqd: 1 },
			};
		}
		if (fieldnames_to_be_altered) {
			Object.keys(fieldnames_to_be_altered).forEach((fieldname) => {
				let property_to_be_altered = fieldnames_to_be_altered[fieldname];
				Object.keys(property_to_be_altered).forEach((property) => {
					let value = property_to_be_altered[property];
					frm.fields_dict["items"].grid.update_docfield_property(fieldname, property, value);
				});
			});
			frm.refresh_field("items");
		}
	},
});

frappe.ui.form.on("Non Capitalized Asset Movement Item", {
	asset: function (frm, cdt, cdn) {
		// on manual entry of an asset auto sets their source location / employee
		const asset_name = locals[cdt][cdn].asset;
		console.log(asset_name)
		if (asset_name) {
			frappe.db
				.get_doc("Non Capitalized Asset", asset_name)
				.then((asset_doc) => {
					if (asset_doc.location)
						frappe.model.set_value(cdt, cdn, "source_location", asset_doc.location);
					if (asset_doc.custodian)
						frappe.model.set_value(cdt, cdn, "from_employee", asset_doc.custodian);
				})
				.catch((err) => {
					console.log(err); // eslint-disable-line
				});
		}
	},
});
