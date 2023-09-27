frappe.ui.form.on('Sales Order', {
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
                            var item_length =0
                            if (frm.doc.boq_items_cf) {
                                item_length = frm.doc.boq_items_cf.length 
                            } 
                            for (let boq_item of r.message) {
                                var new_row =frappe.model.add_child(frm.doc,"Solar BOQ Items","boq_items_cf");
                                item_length++;
                                new_row.idx = item_length;
                                new_row["item_group"]=boq_item.item_group
                                new_row["item_code"]=boq_item.item_code
                                new_row["description"]=boq_item.description
                                new_row["qty"]=boq_item.qty
                                new_row["uom"]=boq_item.uom
                                new_row["remarks"]=boq_item.remarks
                            }
                            frm.refresh_field('boq_items_cf')
                        }
                    }
                }
            });
        }
    }
});