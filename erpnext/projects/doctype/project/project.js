// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt
frappe.ui.form.on("Project", {
    onload: function(frm) {
        frm.set_query('cost_center', function(doc, cdt, cdn) {
			return {
				filters: {
					"center_category": 'Course',
					"is_disabled": 0
				}
			};
		});

        frm.set_query('branch', function(doc, cdt, cdn) {
			return {
				filters: {
					"is_disabled": 0
				}
			};
		});
    },
    refresh: function (frm) {
        frm.set_df_property("project_code", "read_only", frm.is_new() ? 0 : 1);

        if(frm.doc.settlement===1){
			frm.add_custom_button(__('Accounting Ledger'), function(){
				frappe.route_options = {
					voucher_no: frm.doc.name,
					from_date: frm.doc.posting_date,
					to_date: frm.doc.posting_date,
					company: frm.doc.company,
					group_by_voucher: false
				};
				frappe.set_route("query-report", "General Ledger");
			}, __("View"));
		}

        if (frm.doc.settlement != 1 && frm.doc.status != 'Cancelled') {
			frm.add_custom_button("Monthly Settlement", function () {
				frappe.call({
					method: "monthly_settlement",
					doc: cur_frm.doc,
                    callback: function(r){
                        console.log(r.message)
                        cur_frm.refresh()
                    }
				})
			}).addClass("btn-primary");
		}

        if(frm.doc.status != 'Capitalized' && frm.doc.status != 'Cancelled'){
            frm.add_custom_button(__("Capitalize"), function() {
                // frappe.msgprint("Custom Information");
                frm.trigger("make_project_caiptalize");
            });
        }
        
        // frappe.call({
        // 	method: "erpnext.projects.doctype.project.project.get_project_cost",
        // 	args: {
        // 		project_definition: cur_frm.doc.name
        // 	},
        // 	callback: function (r, rt) {
        // 		frm.refresh_fields()
        // 		let total_cost = 0;
        // 		frm.doc.project_sites.map((item) => {
        // 			total_cost = total_cost + item.total_cost
        // 		})
        // 		frm.doc.total_overall_project_cost = total_cost
        // 		cur_frm.refresh_fields()
    // 	},
        // });
        frm.refresh_fields();
    },
    make_project_caiptalize: function(frm) {
        var dialog = new frappe.ui.Dialog({
            title: __("Capitalize Project"),
            fields: [
                {"fieldtype": "Link", "label": __("Project Asset Item Code"),
                    "fieldname": "item_code", "options":"Item",
                    "reqd": 1,
                    // "get_query": function () {
                    //     return {
                    //         filters: [
                    //             ["Item", "disabled", "!=", 0],
                    //             ["Item", "is_fixed_asset", "=", 1],
                    //             ["Item", "is_stock_item", "!=", 0]
                    //         ]
                    //     };
                    // },
                    onchange: function(e) {
                        // console.log("Selected : ", this.value)
                        if (this.value){
                            frappe.call({
                                method: 'erpnext.projects.doctype.project.project.get_item_expense_account',
                                args:{
                                    'item_code': this.value,             
                                },
                                async: false,
                                callback: function(r){
                                    r.message.forEach(function(rec) {
                                        $("input[data-fieldname='account_name']").val(rec.expense_account);
                                        $("input[data-fieldname='item_name']").val(rec.item_name);
                                    });
                                }
                            });
                        }
                        
                    }
                },    
                {"fieldtype": "Data", "label": __("Asset Item Name"),
                    "fieldname": "item_name", "options":"",
                    "reqd": 0
                },    
                {"fieldtype": "Link", "label": __("Account"),
                    "fieldname": "account_name", "options":"Account",
                    "reqd": 0
                },    
                // {"fieldtype": "Button", "label": __("Make Capitalize"),#Jai, optioinal method
                //     "fieldname": "make_project_capitalize", "cssClass": "btn-primary"
                // },
            ]
        });
        // d.fields_dict.ht.$wrapper.html('Hello World');
        // dialog.fields_dict.item_code.$input.on('change', function(){ #this function not working
        //     // dialog.fields_dict.account_name.refresh();
        //     console.warn('im jai')
        // }); 

        dialog.set_primary_action(__('Create'), function(frm) {
            dialog.hide();
            var args = dialog.get_values();
            console.log(args)
            frappe.call({
                method: "capitalize_project_process",
                doc: cur_frm.doc,
                args: {
                    "item_code": args.item_code,
                    "item_name": args.item_name,
                    "account": args.account_name                 
                },
                callback: function (r) {
                    console.log(r.message)
                    cur_frm.reload_doc();
                    show_alert('Project Capitalizaion Done');
                }
            });
        });
        
        // dialog.fields_dict.make_project_capitalize.$input.click(function() { #Jai, optioinal method
        //     var args = dialog.get_values();
        //     console.log(args)
        // });
        dialog.show()
    }
});

/* V14 recidule Jai */
// function open_form(frm, doctype, child_doctype, parentfield) {
// 	frappe.model.with_doctype(doctype, () => {
// 		let new_doc = frappe.model.get_new_doc(doctype);

// 		// add a new row and set the project
// 		let new_child_doc = frappe.model.get_new_doc(child_doctype);
// 		new_child_doc.project = frm.doc.name;
// 		new_child_doc.parent = new_doc.name;
// 		new_child_doc.parentfield = parentfield;
// 		new_child_doc.parenttype = doctype;
// 		new_doc[parentfield] = [new_child_doc];

// 		frappe.ui.form.make_quick_entry(doctype, null, null, new_doc);
// 	});

// }
