frappe.ui.form.on('Insurance and Registration', {
    refresh: function(frm) {

        frm.set_df_property("posting_date","reqd",1)
        frm.remove_custom_button(__('Post Bluebook Fitness & Emission JE'));

        if (!frm.doc.__islocal && !frm.doc.reference) {

            frm.add_custom_button(__('Post Insurance and Registration JE'), function() {

                frappe.confirm(
                    __('Are you sure you want to create Journal Entry?'),
                    function() {

                        frappe.call({
                            method: "erpnext.fleet_management.doctype.insurance_and_registration.insurance_and_registration.post_je",
                            args: {
                                docname: frm.doc.name
                            },
                            freeze: true,
                            freeze_message: __("Creating Journal Entry..."),
                            callback: function(r) {
                                if (!r.exc) {
                                    frappe.show_alert({
                                        message: __("Journal Entry created successfully"),
                                        indicator: "green"
                                    });

                                    frm.reload_doc();
                                }
                            }
                        });

                    }
                );

            });
        }
    },
    
    // posting_date: function(frm) {
    //     // Update all dates in child tables if needed
    // },
    
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
                        // Get the GST account from the tax template
                        if (r.message.taxes && r.message.taxes.length > 0) {
                            let gst_account = r.message.taxes[0].account_head;
                            frm.set_value('gst_account', gst_account);
                            frm.refresh_field('gst_account');
                            
                            // Calculate GST amount based on net_total
                            frm.trigger('calculate_totals');
                        }
                    }
                }
            });
        }
    },
    
    apply_gst: function(frm) {
        frm.trigger('calculate_totals');
    },
    
    net_total: function(frm) {
        frm.trigger('calculate_totals');
    },
    
    calculate_totals: function(frm) {
        // Calculate net_total first
        let net_total = 0;
        
        // Sum from items table (Bluebook and Emission)
        if (frm.doc.items && frm.doc.items.length > 0) {
            frm.doc.items.forEach(item => {
                net_total += flt(item.amount || 0);
                net_total += flt(item.penalty_amount || 0);
            });
        }
        
        // Sum from claim_item table
        if (frm.doc.claim_item && frm.doc.claim_item.length > 0) {
            frm.doc.claim_item.forEach(claim => {
                net_total += flt(claim.claim_amount || 0);
            });
        }
        
        // Sum from insurance_item table
        if (frm.doc.insurance_item && frm.doc.insurance_item.length > 0) {
            frm.doc.insurance_item.forEach(insurance => {
                net_total += flt(insurance.total_amount || 0);
            });
        }
        
        // Sum from registration_item table (if applicable)
        if (frm.doc.registration_item && frm.doc.registration_item.length > 0) {
            frm.doc.registration_item.forEach(reg => {
                net_total += flt(reg.registration_amount || 0);
            });
        }
        
        // Set the net_total
        frm.set_value('net_total', net_total);
        
        // Calculate GST if apply_gst is checked and taxes_and_charges is selected
        if (frm.doc.apply_gst && frm.doc.taxes_and_charges) {
            frappe.call({
                method: "frappe.client.get",
                args: {
                    doctype: "Purchase Taxes and Charges Template",
                    name: frm.doc.taxes_and_charges
                },
                callback: function(r) {
                    if (r.message && r.message.taxes && r.message.taxes.length > 0) {
                        // Calculate GST based on the tax rate
                        let tax_rate = flt(r.message.taxes[0].rate || 0);
                        let gst_amount = (net_total * tax_rate) / 100;
                        
                        frm.set_value('gst_amount', gst_amount);
                        frm.refresh_field('gst_amount');
                    }
                }
            });
        } else {
            frm.set_value('gst_amount', 0);
            frm.refresh_field('gst_amount');
        }
    }
});

// Add events for child table changes
frappe.ui.form.on('Bluebook and Emission', {
    amount: function(frm, cdt, cdn) {
        frm.trigger('calculate_totals');
    },
    penalty_amount: function(frm, cdt, cdn) {
        frm.trigger('calculate_totals');
    },
    items_remove: function(frm, cdt, cdn) {
        frm.trigger('calculate_totals');
    }
});

frappe.ui.form.on('Claim Details', {
    claim_amount: function(frm, cdt, cdn) {
        frm.trigger('calculate_totals');
    },
    claim_item_remove: function(frm, cdt, cdn) {
        frm.trigger('calculate_totals');
    }
});

frappe.ui.form.on('Insurance Details', {
    total_amount: function(frm, cdt, cdn) {
        frm.trigger('calculate_totals');
    },
    insurance_item_remove: function(frm, cdt, cdn) {
        frm.trigger('calculate_totals');
    }
});

frappe.ui.form.on('Registration Details', {
    registration_amount: function(frm, cdt, cdn) {
        frm.trigger('calculate_totals');
    },
    registration_item_remove: function(frm, cdt, cdn) {
        frm.trigger('calculate_totals');
    }
});
