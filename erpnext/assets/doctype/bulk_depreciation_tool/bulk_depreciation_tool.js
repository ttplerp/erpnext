// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Bulk Depreciation Tool', {
    onload: function(frm) {
        if (!frm.doc.__islocal) return;
        
        if (!frm.doc.from_date) {
            let from_date = frappe.datetime.add_months(frappe.datetime.get_today(), -1);
            frm.set_value('from_date', from_date);
        }
        if (!frm.doc.to_date) {
            frm.set_value('to_date', frappe.datetime.get_today());
        }
    },

    refresh: function(frm) {
        if (frm.doc.__islocal) {
            if (!frm.doc.from_date) {
                let from_date = frappe.datetime.add_months(frappe.datetime.get_today(), -1);
                frm.set_value('from_date', from_date);
            }
            if (!frm.doc.to_date) {
                frm.set_value('to_date', frappe.datetime.get_today());
            }
        }

        frm.page.clear_inner_toolbar();

        if (frm.doc.docstatus == 0) {
            frm.page.add_inner_button(__('Fetch Assets'), function() {
                frm.trigger('fetch_assets');
            });
            
            frm.page.add_inner_button(__('Run Depreciation'), function() {
                frm.trigger('run_depreciation');
            });
            
            frm.add_custom_button(__('Fetch Assets'), function() {
                frm.trigger('fetch_assets');
            });
            
            frm.add_custom_button(__('Run Depreciation'), function() {
                frm.trigger('run_depreciation');
            });
        }

        // Show stats with branch info
        if (frm.doc.total_assets > 0) {
            let assets_without_branch = 0;
            if (frm.doc.assets) {
                assets_without_branch = frm.doc.assets.filter(a => a.branch === 'No Branch Set' || !a.branch).length;
            }
            
            frm.dashboard.add_indicator(__('Total Assets: {0}', [frm.doc.total_assets]));
            frm.dashboard.add_indicator(__('Pending Amount: {0}', [frm.doc.total_pending_amount]));
            
            if (assets_without_branch > 0) {
                frm.dashboard.add_indicator(__('Assets Without Branch: {0}', [assets_without_branch]), 'orange');
            }
            
            if (frm.doc.success_count > 0) {
                frm.dashboard.add_indicator(__('Success: {0}', [frm.doc.success_count]), 'green');
            }
            if (frm.doc.failed_count > 0) {
                frm.dashboard.add_indicator(__('Failed: {0}', [frm.doc.failed_count]), 'red');
            }
        }

        if (frm.doc.error_log) {
            frm.dashboard.add_indicator(__('Has Errors'), 'red');
            
            frm.page.add_inner_button(__('View Errors'), function() {
                frappe.msgprint({
                    title: __('Error Log'),
                    message: `<pre style="max-height: 400px; overflow-y: auto; white-space: pre-wrap;">${frm.doc.error_log}</pre>`,
                    indicator: 'red'
                });
            });
        }
    },

    run_depreciation: function(frm) {
        if (!frm.doc.assets || frm.doc.assets.length === 0) {
            frappe.msgprint(__('No assets found. Please click "Fetch Assets" first.'));
            return;
        }

        if (frm.doc.total_assets === 0) {
            frappe.msgprint(__('No pending assets to process.'));
            return;
        }

        // Check if any assets don't have branch
        let assets_without_branch = frm.doc.assets.filter(a => a.branch === 'No Branch Set' || !a.branch);
        if (assets_without_branch.length > 0) {
            frappe.confirm(
                __(`{0} assets don't have a branch set. They will be automatically assigned a default branch. Continue?`, 
                    [assets_without_branch.length]),
                function() {
                    frm.trigger('process_depreciation');
                }
            );
        } else {
            frm.trigger('process_depreciation');
        }
    },

    process_depreciation: function(frm) {
        frappe.call({
            method: 'process_depreciation',
            doc: frm.doc,
            freeze: true,
            freeze_message: __('Processing depreciation entries...'),
            callback: function(r) {
                frm.reload_doc();
                if (r.message) {
                    frappe.msgprint({
                        title: __('Processing Complete'),
                        message: __(
                            `Successfully processed {0} entries. Failed: {1}`,
                            [r.message.success || 0, r.message.failed || 0]
                        ),
                        indicator: r.message.failed > 0 ? 'orange' : 'green'
                    });
                }
            },
            error: function(r) {
                frappe.msgprint({
                    title: __('Error'),
                    message: __('Failed to process depreciation. Please check the error logs.'),
                    indicator: 'red'
                });
            }
        });
    },

    fetch_assets: function(frm) {
        if (!frm.doc.from_date || !frm.doc.to_date) {
            frappe.msgprint(__('Please select From Date and To Date'));
            return;
        }

        if (!frm.doc.company) {
            frappe.msgprint(__('Please select Company'));
            return;
        }

        frappe.call({
            method: 'fetch_pending_assets',
            doc: frm.doc,
            freeze: true,
            freeze_message: __('Fetching assets...'),
            callback: function(r) {
                frm.refresh_field('assets');
                frm.refresh_field('total_assets');
                frm.refresh_field('total_pending_amount');
                
                if (frm.doc.total_assets > 0) {
                    let assets_without_branch = frm.doc.assets.filter(a => a.branch === 'No Branch Set' || !a.branch).length;
                    let message = __(`Found {0} assets with pending depreciation entries`, [frm.doc.total_assets]);
                    if (assets_without_branch > 0) {
                        message += __(`\n{0} assets don't have a branch set.`, [assets_without_branch]);
                    }
                    frappe.msgprint({
                        title: __('Assets Found'),
                        message: message,
                        indicator: assets_without_branch > 0 ? 'orange' : 'green'
                    });
                } else {
                    frappe.msgprint({
                        title: __('No Assets Found'),
                        message: __(`No assets with pending depreciation entries in the date range {0} to {1}`,
                            [frm.doc.from_date, frm.doc.to_date]),
                        indicator: 'orange'
                    });
                }
            },
            error: function(r) {
                frappe.msgprint({
                    title: __('Error'),
                    message: __('Failed to fetch assets. Please check the error logs.'),
                    indicator: 'red'
                });
            }
        });
    },

    from_date: function(frm) {
        if (frm.doc.from_date && frm.doc.to_date && frm.doc.company && frm.doc.docstatus == 0) {
            frm.trigger('fetch_assets');
        }
    },

    to_date: function(frm) {
        if (frm.doc.from_date && frm.doc.to_date && frm.doc.company && frm.doc.docstatus == 0) {
            frm.trigger('fetch_assets');
        }
    },

    company: function(frm) {
        if (frm.doc.assets && frm.doc.assets.length > 0) {
            frm.doc.assets = [];
            frm.refresh_field('assets');
            frm.set_value('total_assets', 0);
            frm.set_value('total_pending_amount', 0);
        }
        
        if (frm.doc.from_date && frm.doc.to_date && frm.doc.company && frm.doc.docstatus == 0) {
            frm.trigger('fetch_assets');
        }
    }
});

frappe.listview_settings['Bulk Depreciation Tool'] = {
    onload: function(listview) {
        listview.page.add_menu_item(__('New Bulk Depreciation'), function() {
            frappe.new_doc('Bulk Depreciation Tool');
        });
    }
};