frappe.ui.form.on('Quotation', {
    refresh: function(frm) {
        frm.fields_dict['boq_items_cf'].grid.get_field('item_code').get_query = function(doc, cdt, cdn) {
            var child = locals[cdt][cdn];
            return {    
                filters:[
                    ['Item', 'item_group', '=', child.item_group]
                ]
            };
        };        
    },
    custom_boq_template_cf: function(frm) {
        if (frm.doc.custom_boq_template_cf ) {
            frappe.call({
                method: "soleos.soleos_api.get_boq_items",
                args: {
                    "boq_template_name": frm.doc.custom_boq_template_cf
                },
                callback: function(r) {
                    if(!r.exc && r.message) {
                        if(r.message) {
                            for (let boq_item of r.message) {
                                frm.add_child("boq_items_cf", boq_item);
                            }
                            frm.refresh_field('boq_items_cf')
                        }
                    }
                }
            });
        }
    }
});