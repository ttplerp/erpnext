// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Tenant Information', {
	// refresh: function(frm) {

	// }
	// on_load: function(frm){
	// 	if(frm.doc.__islocal){
			
	// 	}
	// },
	setup: function(frm){
		frm.set_query("block_no", function(){
			return {
				"filters":[
					["location", "=", frm.doc.locations]
				]
			};
		});
		frm.set_query("flat_no", function(){
			return {
				"filters":[
					["block_no", "=", frm.doc.block_no],
					['status', 'in', ['Surrendered', 'Unallocated']]
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
	},
	block_no: function(frm){
		cur_frm.set_value("flat_no", "");
	},
	building_category: function(frm){
		if (frm.doc.building_category == 'Pilot Housing'){
			cur_frm.set_value("percent_of_increment", "");
			cur_frm.set_value("no_of_year_for_increment", "");
			cur_frm.set_value("rental_term_year", "");
		} else {
			frappe.model.get_value('Rental Setting',{'name': 'Rental Setting'}, ['percent_of_increment', 'no_of_year_for_increment', 'rental_term_year'], function(d){
				cur_frm.set_value("percent_of_increment", d.percent_of_increment);
				cur_frm.set_value("no_of_year_for_increment", d.no_of_year_for_increment);
				cur_frm.set_value("rental_term_year", d.rental_term_year);
			});
		}
	},
	total_floor_area: function(frm){
		calculate_initial_rent(frm);
	},
	rate_per_sqft: function(frm){
		calculate_initial_rent(frm);
	},
	calculate_rent_charges: function(frm){
		frappe.call({
			method: "calculate_rent_charges",
			doc: frm.doc,
			callback: function(r){
				cur_frm.refresh();
			}
		});
	}
});

function calculate_initial_rent(frm){
	cur_frm.set_value("initial_rental_amount", 0.0);
	cur_frm.set_value("security_deposit", 0.0);
	if (frm.doc.rate_per_sqft == 0 || frm.doc.rate_per_sqft === undefined) return
	if (frm.doc.total_floor_area == 0 || frm.doc.total_floor_area === undefined) return

	cur_frm.set_value("initial_rental_amount", Math.round(frm.doc.rate_per_sqft * frm.doc.total_floor_area));
	cur_frm.set_value("security_deposit", Math.round(frm.doc.initial_rental_amount * 2));
}
