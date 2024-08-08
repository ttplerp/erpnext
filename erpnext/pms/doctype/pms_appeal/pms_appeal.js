// Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('PMS Appeal', {
	pms_calendar: function(frm) {
		cur_frm.set_query("appeal_based_on", function(doc) {
			return {
				'filters': {
					'employee': doc.employee,
					'pms_calendar': doc.pms_calendar,
					'docstatus': 1
				}
			}
		});
	},
});
frappe.ui.form.on('Evaluate Appeal Target Item',{
	onload:(frm,cdt,cdn)=>{
		toggle_reqd_qty_quality(frm,cdt,cdn)
	},
	refresh:(frm,cdt,cdn)=>{
		toggle_reqd_qty_quality(frm,cdt,cdn)
	},
	timeline_achieved:(frm,cdt,cdn)=>{
		toggle_reqd_qty_quality(frm,cdt,cdn)
		calculate_timeline_rating(frm,cdt,cdn)
		calculate_score(frm,cdt,cdn)
	},
	quality_achieved:(frm,cdt,cdn)=>{
		calculate_qty_quality_rating(frm,cdt,cdn)
		calculate_score(frm,cdt,cdn)
	},
	quantity_achieved:(frm,cdt,cdn)=>{
		calculate_qty_quality_rating(frm,cdt,cdn)
		calculate_score(frm,cdt,cdn)
	},
	accept_zero_qtyquality:(frm,cdt,cdn)=>{
		var row = locals[cdt][cdn]
		row.quality_achieved = row.quantity_achieved = 0
		frm.refresh_field('Evaluate Appeal Target Item')
	},
	reverse_formula:(frm,cdt,cdn)=>{
		var row = locals[cdt][cdn]
		if (cint(row.reverse_formula) == 0 ){
			row.accept_zero_qtyquality = 0
			frm.refresh_field('Evaluate Appeal Target Item')
		}
	}
})
// calculate timeline rating
var calculate_timeline_rating = (frm,cdt,cdn)=>{
	let targeted_timeline = 0
	let timeline_achieved = 0
	let timeline = 0
	let weightage = 0
	let timeline_rating = 0
	var row = locals[cdt][cdn]
	targeted_timeline = row.timeline
	timeline_achieved = row.timeline_achieved
	weightage =row.weightage
	timeline = row.timeline
	if (flt(timeline_achieved)<= flt(timeline)){
		timeline_rating = weightage
	}
	else{
		timeline_rating = (flt(timeline) / flt(timeline_achieved)) * flt(weightage)
	}
	row.timeline_rating = timeline_rating
	console.log('here',row.timeline_rating)
	frm.refresh_field('Evaluate Appeal Target Item')
}
// calculate score and average
var calculate_score = (frm,cdt,cdn)=>{
	var row = locals[cdt][cdn]
	row.average_rating =(flt(row.quantity_rating)+flt(row.quality_rating)+flt(row.timeline_rating)) / 2
	if (row.average_rating){
		row.score = (row.average_rating / row.weightage) * 100
		frm.refresh_field("Evaluate Appeal Target Item")
	}
}
//calculate quality or quantity rating
var calculate_qty_quality_rating = (frm,cdt,cdn)=>{
	let achieved = 0
	let rating = 0
	let targeted = 0
	let weightage = 0
	var row = locals[cdt][cdn]
	weightage = row.weightage
	if (row.qty_quality == 'Quality') {
		achieved = row.quality_achieved
		targeted = row.quality
	}
	else if (row.qty_quality == 'Quantity') {
		achieved = row.quantity_achieved
		targeted = row.quantity
	}
	if (flt(achieved)>=flt(targeted)){
		rating = weightage
	}
	else{
		rating = flt(achieved) / flt(targeted) * flt(weightage)
	}
	if (row.qty_quality == 'Quality') 
		row.quality_rating = rating
	else if (row.qty_quality == 'Quantity') 
		row.quantity_rating = rating
	frm.refresh_field('Evaluate Appeal Target Item')
}
var toggle_reqd_qty_quality = (frm,cdt,cdn)=>{
	var row = locals[cdt][cdn]
		if (row.qty_quality == 'Quality'){
			cur_frm.fields_dict.evaluate_target_item.grid.toggle_reqd("quality_achieved", true)
			cur_frm.fields_dict.evaluate_target_item.grid.toggle_reqd("quantity_achieved", false)
		}else if (row.qty_quality == 'Quantity'){
			cur_frm.fields_dict.evaluate_target_item.grid.toggle_reqd("quality_achieved", false)
			cur_frm.fields_dict.evaluate_target_item.grid.toggle_reqd("quantity_achieved", true)
		}else{
			cur_frm.fields_dict.evaluate_target_item.grid.toggle_reqd("quality_achieved", false)
			cur_frm.fields_dict.evaluate_target_item.grid.toggle_reqd("quantity_achieved", false)
		}
}

var apply_filter=(frm)=> {
	cur_frm.set_query('pms_calendar', function () {
		return {
			'filters': {
				'docstatus': 1
			}
		};
	});
}

