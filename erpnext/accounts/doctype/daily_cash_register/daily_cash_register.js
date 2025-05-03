// Copyright (c) 2025, Frappe Technologies Pvt. Ltd.
// For license information, please see license.txt
frappe.ui.form.on('Daily Cash Register', {
    onload(frm) {
        frm.set_query('cash_account', () => ({
            filters: {
                account_type: 'Cash',
                is_group: 0,
                disabled: 0
            }
        }));
    },
    refresh(frm) {
        if (frm.doc.docstatus === 0 && !frm.is_new()) {
            frm.page.clear_primary_action();
            frm.page.set_primary_action(__('Submit'), () => frm.save('Submit'));
        }
    },
    cash_account(frm) {
        if (frm.doc.cash_account) {
            validate_cash_account_date(frm);
            reset_cash_register_fields(frm);
        }
    },
    date(frm) {
        if (frm.doc.cash_account && frm.doc.date) {
            validate_cash_account_date(frm);
            reset_cash_register_fields(frm);
        }
    },
    last_closed_on(frm) {
        if (frm.doc.cash_account && frm.doc.date && frm.doc.last_closed_on) {
            validate_cash_account_date(frm);
            reset_cash_register_fields(frm);
        }
    },

    validate(frm) {
        if (toFloat(frm.doc.closing_balance) < 0) {
            frappe.validated = false;
            frappe.msgprint(__('Closing Balance cannot be negative.'));
        }
        if (!isValidForClosing(frm)) {
            frappe.validated = false;
            return;
        }
    },

    custody: calculate_closing_balance,
    returns: calculate_closing_balance,
    opening_balance: calculate_closing_balance,
    total_cash_counted_and_verified: calculate_over_short,

    fetch_gl_entries(frm) {
        const { cash_account, date, last_closed_on } = frm.doc;
        frappe.call({
            method: 'erpnext.accounts.doctype.daily_cash_register.daily_cash_register.fetch_gl_entries',
            args: { cash_account, last_closed_on, date },
            callback({ message }) {
                if (!message) return;

                frm.clear_table('cash_in_entries');
                (message.cash_in_entries || []).forEach(row => {
                    frm.add_child('cash_in_entries', {
                        date: row.posting_date,
                        voucher_type: row.voucher_type,
                        voucher_no: row.voucher_no,
                        amount: row.debit,
                        remarks: row.remarks
                    });
                });
                frm.refresh_field('cash_in_entries');

                frm.clear_table('cash_out_entries');
                (message.cash_out_entries || []).forEach(row => {
                    frm.add_child('cash_out_entries', {
                        date: row.posting_date,
                        voucher_type: row.voucher_type,
                        voucher_no: row.voucher_no,
                        amount: row.credit,
                        remarks: row.remarks
                    });
                });
                frm.refresh_field('cash_out_entries');

                const summary = message.summary || {};
                frm.set_value('custody', toFloat(summary.total_cash_in));
                frm.set_value('returns', toFloat(summary.total_cash_out));
                frm.set_value('opening_balance', toFloat(summary.closing_balance));

                calculate_closing_balance(frm);
            }
        });
    }
});

// --- Helper Functions ---
function validate_cash_account_date(frm) {
     
    frappe.call({
        method: 'erpnext.accounts.doctype.daily_cash_register.daily_cash_register.get_last_transaction_date',
        args: { cash_account: frm.doc.cash_account },
        callback({message}) {
            const last_date = message?.message;
            if (last_date) {
                const last_closed_date_str = frappe.datetime.obj_to_str(
                    typeof message === "string" ? frappe.datetime.str_to_obj(last_date) : last_date
                );

                frm.set_value('last_closed_on', last_closed_date_str);
                frm.set_value('transaction_count',1);
                
                if (frm.doc.date && frappe.datetime.str_to_obj(last_closed_date_str) > frappe.datetime.str_to_obj(frm.doc.date)) {
                    frappe.msgprint(__('The date must be greater than the "last closed date" ({0}).', [last_closed_date_str]));
                    frm.set_value('date','');
                    frappe.validated = false;
                } else { 
                    check_cash_closure(frm, last_closed_date_str);
                }
            } else {  
                //console.log(frm.doc.last_closed_on)
                if (frm.doc.date && frappe.datetime.str_to_obj(frm.doc.last_closed_on) > frappe.datetime.str_to_obj(frm.doc.date)) {
                    frappe.msgprint(__('The date must be greater than the last closed date ({0}).', [frm.doc.last_closed_on]));
                    frm.set_value('date','');
                    frappe.validated = false;
                }
                frm.set_value('transaction_count', 0);
            }
        }
    });
}

function check_cash_closure(frm, lastClosedDate) {
    frappe.call({
        method: 'erpnext.accounts.doctype.daily_cash_register.daily_cash_register.is_cash_closed',
        args: {
            cash_account: frm.doc.cash_account,
            last_closed_on: lastClosedDate,
            date: frm.doc.date
        },
        callback({ message }) {
            if (message === true) {
                frappe.msgprint(__('Cash has already been closed for this date and cash account.'));
                frm.set_value('date', '');
                frappe.validated = false;
            }
        }
    });
}

// Reusable reset function
function reset_cash_register_fields(frm) {
    if (
        frm.doc.opening_balance ||
        frm.doc.closing_balance ||
        frm.doc.returns ||
        frm.doc.custody ||
        frm.doc.total_cash_counted_and_verified
    ) {
    frm.set_value('opening_balance', 0);
    frm.set_value('closing_balance', 0);
    frm.set_value('returns', 0);
    frm.set_value('custody', 0);
    frm.set_value('total_cash_counted_and_verified', 0);
    }
}

function toFloat(val) {
    return parseFloat(val) || 0;
}

function calculate_closing_balance(frm) {
    const opening = toFloat(frm.doc.opening_balance);
    const custody = toFloat(frm.doc.custody);
    const returns = toFloat(frm.doc.returns);

    const closing = (custody === 0 && returns === 0)
        ? opening
        : opening + custody - returns;

    frm.set_value('closing_balance', closing);
    calculate_over_short(frm);
}

function calculate_over_short(frm) {
    const closing = toFloat(frm.doc.closing_balance);
    const net = toFloat(frm.doc.total_cash_counted_and_verified);
    const over_short = closing - net;

    frm.set_value('over_short', over_short);

    const wrapper = frm.fields_dict.over_short.$wrapper;
    wrapper.find('.short-msg').remove();

    if (over_short < 0) {
        wrapper.prepend($(`<div class="short-msg" style="color: red; margin-bottom: 5px;">
            ⚠️ Short of cash by ${Math.abs(over_short).toFixed(2)}
        </div>`));
    }
}

function isValidForClosing(frm) {
    const custody = toFloat(frm.doc.custody);
    const returns = toFloat(frm.doc.returns);
    const opening_balance = toFloat(frm.doc.opening_balance);
    const transaction_count = parseInt(frm.doc.transaction_count || "0", 10);
    console.log("Testing",transaction_count);
    if (transaction_count > 0) {
        if (custody <= 0 && returns <= 0) {
            frappe.msgprint(__('No Cash In and Cash Out for selected date. Your cash balance remain same.'));
            return false;
        }
    } else {
        if (opening_balance <= 0) {
            frappe.msgprint(__('Opening Balance must be greater than zero for the first transaction.'));
            return false;
        }
    }
    return true;
}

