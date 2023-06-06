// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Rental Payment', {
	refresh: function(frm) {
		if(frm.doc.docstatus > 0) {
			frm.add_custom_button(__('Ledger'), function() {
				frappe.route_options = {
					"voucher_no": frm.doc.name,
					"from_date": frm.doc.posting_date,
					"to_date": moment(frm.doc.modified).format('YYYY-MM-DD'),
					"company": frm.doc.company,
					// "finance_book": frm.doc.finance_book,
					"group_by": '',
					"show_cancelled_entries": frm.doc.docstatus === 2
				};
				frappe.set_route("query-report", "General Ledger");
			}, __('View'));
		}

	// 	if(frm.doc.docstatus == 0){
	// 		if (!frm.is_new() && !(frm.doc.get_rental_bill && frm.doc.calc_penalty)){
				// DeMorgan's Law, !(A AND B) = !A OR !B
				// !A AND !(B AND C) = (!A AND !B) OR (!A AND !C)
				// frm.page.clear_actions_menu();
				// frm.page.clear_primary_action();
				// if (!frm.doc.get_rental_bill){
				// 	frm.page.add_action_item(__("Get Rental Bills"),
				// 		function() {
				// 			frm.events.get_rental_bills(frm);
				// 		}
				// 	);
				// }
				// if (!frm.doc.calc_penalty){
				// 	frm.page.add_action_item(__("Calc. Penalty"),
				// 		function() {
				// 			frm.events.calculate_penalty(frm);
				// 		}
				// 	);
				// }

			// } else if (frm.doc.get_rental_bill && frm.doc.calc_penalty){
			// 	frm.page.clear_actions_menu();
			// 	frm.page.clear_primary_action();
			// 	frm.page.add_action_item(__('Submit'), function() {
			// 		frm.save('Submit').then(()=>{
			// 			frm.page.clear_actions_menu();
			// 			frm.page.clear_primary_action();
			// 			frm.refresh();
			// 			frm.events.refresh(frm);
			// 		});
			// 	});

				// frm.page.add_action_item(__('Cancel'), function() {
				// 	frm.save('Cancel').then(()=>{
				// 		frm.page.clear_actions_menu();
				// 		frm.page.clear_primary_action();
				// 		frm.refresh();
				// 		frm.events.refresh(frm);
				// 	});
				// });

	// 		} else {
	// 			cur_frm.page.clear_actions();
	// 		}
	// 	}

	},
	onload: function(frm){
		frm.set_query("bank_account", function() {
			var account_types = ["Bank", "Cash"]
			return {
				"filters": [
					["account_type", "in", account_types],
				]
			};
		});
		
		frm.set_query("debit_account", function() {
			var root_types = ["Liability"]
			return {
				"filters": [
					["root_type", "in", root_types],
				]
			};
		});
	},
	setup: function (frm) {
		frm.set_query("dzongkhag", function () {
			return {
				"filters": [
					["is_dzongkhag", "=", 1]
				]
			};
		});
		frm.set_query("tenant_department", function(){
			return {
				"filters": [
					["ministry_agency", "=", frm.doc.ministry_and_agency]
				]
			};
		});
		frm.set_query("tenant", function(){
			return {
				"filters": [
					["docstatus", "=", 1],
					["status", "=", "Allocated"],
				]
			};
		});
		frm.set_query("tenant", "items", function() {
			return {
				filters: [
					["docstatus", "=", 1],
					["status", "=", "Allocated"],
					["branch", "=", frm.doc.branch],
				]
			}
		});
	},
	get_rental_bills: function (frm) {
		frm.set_value("number_of_rental_bill", 0);
		frm.refresh_field("number_of_rental_bill");
		return frappe.call({
			doc: frm.doc,
			method: 'get_rental_bills',
			callback: function(r) {
				if (r.message){
					frm.set_value("number_of_rental_bill", r.message['number_of_rental_bill']);
					frm.set_value("total_bill_amount", r.message['total_bill_amount']);
					frm.set_value("total_rent_received", r.message['total_rent_amt']);
					frm.set_value("total_amount_received", r.message['total_bill_amount'] - r.message['rent_write_off_amount']);
					frm.set_value("rent_write_off_amount", r.message['rent_write_off_amount']);
					frm.refresh_field("number_of_rental_bill");
					frm.refresh_field("total_bill_amount");
					frm.refresh_field("total_rent_received");
					frm.refresh_field("total_amount_received");
					frm.refresh_field("rent_write_off_amount");
					frm.refresh_field("items");
					frm.dirty();
				}
			},
			freeze: true,
			freeze_message: '<span style="color:white; background-color: red; padding: 10px 50px; border-radius: 5px;">Fetching Rental Bills...</span>'
		});
	},

});

frappe.ui.form.on('Rental Payment Item', {
	deduct_from_security_deposit: function(frm, cdt, cdn){
		var row = locals[cdt][cdn];
		if (row.deduct_from_security_deposit){
			return frappe.call({
				method: "get_security_deposit",
				doc:frm.doc,
				args:{
					'customer': row.customer,
				},
				callback: function(r){
					console.log(r.message)
					frappe.model.set_value(cdt, cdn, "security_deposit", r.message ?? 0.00)
				}
			});
		} else {
			frappe.model.set_value(cdt, cdn, "security_deposit", 0.00)
		}
	}
});