// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Imprest Recoup', {
	onload: function(frm){
		frm.set_query('expense_account', 'items', function() {
			return {
				"filters": {
					"account_type": "Expense Account"
				}
			};
		});
	},
	refresh: function(frm){
		frm.set_query("project", function() {
			return {
				"filters": {
					"branch": frm.doc.branch
				}
			}
		});
	},

	"get_imprest_advance":function(frm){
		get_imprest_advance(frm)
	},

	branch: function(frm){
		frm.set_value('party_type', '');
		frm.set_value('party', '');
		frm.set_value('items', '');
		frm.refresh_field('items')
		frm.set_value('imprest_advance_list', '');
		frm.refresh_field('imprest_advance_list')

		// frm.set_query('party', function() {
		// 	return {
		// 		filters: {
		// 			"branch": frm.doc.branch
		// 		}
		// 	};
		// });
	},
	project: function(frm){
		frm.set_query("project", function() {
			return {
				"filters": {
					"branch": frm.doc.branch
				}
			}
		});
	},
	apply_gst: function(frm){
		if(frm.doc.apply_gst == 1){
			if (frm.doc.total_amount_before_gst > 0) {
				frm.set_value("gst_amount", Math.round(frm.doc.total_amount_before_gst * 0.05));
				frm.set_value("total_amount", frm.doc.total_amount_before_gst + Math.round(frm.doc.total_amount_before_gst * 0.05));
				frm.refresh_fields("gst_amount");
				frm.refresh_fields("total_amount");
			}

		}else{
			frm.set_value("gst_account", "");
			frm.refresh_fields("gst_account");
			frm.set_value("gst_amount", "");
			frm.refresh_fields("gst_amount");
			frm.set_value("total_amount", frm.doc.total_amount_before_gst);
			frm.refresh_fields("total_amount");
		}
	},
});

frappe.ui.form.on("Imprest Recoup Item", {
	amount: function(frm, cdt, cdn){
		get_imprest_advance(frm)
	},
	recoup_type: function(frm, cdt, cdn) {
		var d = locals[cdt][cdn];
		if (!frm.doc.company) {
			d.recoup_type = "";
			frappe.msgprint(__("Please set the Company"));
			this.frm.refresh_fields();
			return;
		}

		if(!d.recoup_type) {
			return;
		}
		return frappe.call({
			method: "erpnext.accounts.doctype.imprest_recoup.imprest_recoup.get_imprest_recoup_account",
			args: {
				"recoup_type": d.recoup_type,
				"company": frm.doc.company
			},
			callback: function(r) {
				if (r.message) {
					d.account = r.message.account;
				}
				frm.refresh_field("items")
				frm.refresh_fields();
			}
		});
	}
})

var get_imprest_advance = function(frm){
	frm.set_value('total_amount', 0);
	frappe.call({
		method: 'populate_imprest_advance',
		doc: frm.doc,
		callback:  () =>{
			frm.refresh_field('imprest_advance_list')
			frm.refresh_fields()
		}
	})
}

