frappe.ui.form.on('POL Receive', {
    refresh: function(frm) {
        refresh_html(frm);
        if(!frm.doc.__islocal){
            if(frm.doc.journal_entry){
                frm.add_custom_button(__('Journal Entry'), function() {
                    frappe.route_options = {"name": frm.doc.journal_entry};
                    frappe.set_route("List", "Journal Entry");
                }, __("View"));
            }
        }
        if(frm.doc.docstatus==1 && frm.doc.receive_in_barrel ==1) {
            frm.add_custom_button(__('Stock Ledger'), function() {
                frappe.route_options = {
                    "voucher_no": frm.doc.name,
                    "from_date": frm.doc.posting_date,
                    "to_date": frm.doc.posting_date,
                    "company": frm.doc.company,
                };
                frappe.set_route("query-report", "Stock Ledger");
            }, __('View'));
        }
    },
    
    qty: function(frm) {
        calculate_total(frm);
        frm.events.reset_items(frm);
        frm.refresh_fields("items");
    },
    
    rate: function(frm) {
        frm.events.reset_items(frm);
        frm.refresh_fields("items");
        calculate_total(frm);
    },
    
    taxes_and_charges: function(frm) {
        if (frm.doc.taxes_and_charges) {
            frappe.call({
                method: "frappe.client.get",
                args: {
                    doctype: "Purchase Taxes and Charges Template",
                    name: frm.doc.taxes_and_charges
                },
                callback: function(r) {
                    if (r.message) {
                        // Always reset taxes when template changes
                        frm.set_value("taxes", []);
                        
                        // Add all taxes from the template
                        $.each(r.message.taxes || [], function(i, tax) {
                            var child = frm.add_child("taxes");
                            child.charge_type = tax.charge_type;
                            child.account_head = tax.account_head;
                            child.description = tax.description;
                            child.rate = tax.rate;
                            child.cost_center = tax.cost_center || frm.doc.cost_center;
                            child.category = tax.category;
                            child.add_deduct_tax = tax.add_deduct_tax;
                            child.included_in_print_rate = tax.included_in_print_rate;
                            child.row_id = tax.row_id;
                        });
                        
                        var tds_child = frm.add_child("taxes");
                        tds_child.charge_type = 'On Net Total';
                        tds_child.account_head = '21.381 - TDS - 2% Payable';
                        tds_child.description = '2 % TDS - VBPL';
                        tds_child.rate = 2;
                        tds_child.cost_center = frm.doc.cost_center || '';
                        tds_child.category = 'Total';
                        tds_child.add_deduct_tax = 'Deduct';
                        tds_child.included_in_print_rate = 0;
                        tds_child.row_id = (r.message.taxes ? r.message.taxes.length : 0) + 1;
                        
                        frm.refresh_field("taxes");
                    }
                }
            });
        } else {
            frm.set_value("taxes", []);
        }
    },
    
    apply_gst: function(frm) {
        if (!frm.doc.apply_gst) {
            frm.set_value("taxes_and_charges", null);
            frm.set_value("taxes", []);
        }
    },
    
    get_pol_expense:function(frm){
        populate_child_table(frm);
    },
    
    settle_imprest_advance: function(frm){
        set_equipment_filter(frm);
        if(frm.doc.settle_imprest_advance==0 || frm.doc.settle_imprest_advance == undefined){
            frm.set_value("party",null);
            frm.refresh_field("party");
        }
    },
    
    equipment:function(frm){
        frm.set_query("fuelbook",function(){
            return {
                filters:{
                    "equipment":frm.doc.equipment
                }
            }
        });
        get_previous_km_reading(frm);
    },
    
    reset_items:function(frm){
        frm.clear_table("items");
    },
    
    make_pol_receive_invoice: function(frm) {
        frappe.call({
            method: "make_pol_receive_invoice",
            doc:frm.doc,
            callback:function(r){
                cur_frm.reload_doc();
            }
        });
    }
});

var populate_child_table = function(frm){
    if (frm.doc.fuelbook && frm.doc.total_amount) {
        frappe.call({
            method: 'populate_child_table',
            doc: frm.doc,
            callback:  function() {
                frm.refresh_fields();
                frm.dirty();
            }
        });
    }
};

function calculate_total(frm) {
    if(frm.doc.qty && frm.doc.rate) {
        frm.set_value("total_amount", frm.doc.qty * frm.doc.rate);
    }

    if(frm.doc.qty && frm.doc.rate && frm.doc.discount_amount) {
        frm.set_value("total_amount", (frm.doc.qty * frm.doc.rate) - frm.doc.discount_amount);
    }
}   

var set_equipment_filter = function(frm){
    if (cint(frm.doc.direct_consumption) == 0){
        frm.set_query("equipment", function() {
            return {
                query: "erpnext.fleet_management.fleet_utils.get_container_filtered",
                filters:{
                    "branch":frm.doc.branch
                }
            };
        });
    }
    if (cint(frm.doc.direct_consumption) == 0 && cint(frm.doc.settle_imprest_advance) == 1) {
        frm.set_query("equipment", function(){
            return {
                filters: {
                    is_tanker: 1,
                }
            }
        });
    }
};

var get_previous_km_reading = function(frm) {
    frappe.call({
        method: "get_previous_km_reading",
        doc: frm.doc,
        callback: function (r) {
            frm.set_value("previous_km", r.message);
            frm.refresh_field("previous_km");
        }
    });
};

var refresh_html = function(frm){
    var journal_entry_status = "";
    if(frm.doc.journal_entry_status){
        journal_entry_status = '<div style="font-style: italic; font-size: 0.8em; ">* '+frm.doc.journal_entry_status+'</div>';
    }
    
    if(frm.doc.journal_entry){
        $(frm.fields_dict.journal_entry_html.wrapper).html('<label class="control-label" style="padding-right: 0px;">Journal Entry</label><br><b>'+'<a href="/desk#Form/Journal Entry/'+frm.doc.journal_entry+'">'+frm.doc.journal_entry+"</a> "+"</b>"+journal_entry_status);
    }   
};

cur_frm.set_query("taxes_and_charges", function() {
    return {
        "filters": {
            "company": cur_frm.doc.company
        }
    };
});

cur_frm.set_query("pol_type", function() {
    return {
        "filters": {
            "disabled": 0,
            "is_pol_item": 1
        }
    };
});