
// frappe.ui.form.on('Task', {
//     validate: function(frm) {
//         if (frm.doc.status === "Working") {
//             const dependentTasks = frm.doc.depends_on;

//             for (const dependentTask of dependentTasks) {
//                 frappe.model.with_doc("Task", dependentTask.task, function() {
//                     const dependentTaskDoc = frappe.get_doc("Task", dependentTask.task);
//                     if (dependentTaskDoc.status !== "Completed") {
//                         frappe.msgprint(`Dependent task ${dependentTask.task} must be completed before changing the status to "Working"`);
//                         frappe.validated = false;
//                         return false;
//                     }
//                 });
//             }
//         }
//     }
// });


frappe.ui.form.on('Task', {
    validate: function(frm) {
        if (frm.doc.status === "Working") {
            const dependentTasks = frm.doc.depends_on;
            
            for (let i = 0; i < dependentTasks.length; i++) {
                const dependentTask = dependentTasks[i];
                
                frappe.model.with_doc("Task", dependentTask.task, function() {
                    const dependentTaskDoc = frappe.get_doc("Task", dependentTask.task);
                    if (dependentTaskDoc.status !== "Completed") {
                        frappe.msgprint(`Dependent task ${dependentTask.task} must be completed before changing the status to "Working"`);
                        frappe.validated = false;
                        return false;
                    }
                });
            }
        }
    }
});

