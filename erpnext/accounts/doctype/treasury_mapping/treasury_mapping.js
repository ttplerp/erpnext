// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Treasury Mapping', {
    refresh: function(frm) {
        const setQueryForField = (fieldname) => {
            frm.fields_dict['accounts_mapping'].grid.get_field(fieldname).get_query = function() {
                return {
                    filters: {
                        'is_group': 0
                    }
                }
            };
        };

        const fields = ['debit_account', 'credit_account', 'tds_account', 'interest_account'];

        fields.forEach(setQueryForField);
    }
});

