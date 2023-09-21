// Copyright (c) 2023, GreyCube Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on("BOQ Template", "refresh", function(frm) {
    frm.fields_dict['boq_template_details'].grid.get_field('item_code').get_query = function(doc, cdt, cdn) {
        var child = locals[cdt][cdn];
        return {    
            filters:[
                ['Item', 'item_group', '=', child.item_group]
            ]
        };
    };
});