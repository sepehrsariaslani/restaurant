frappe.ui.form.on('Item', {
    refresh(frm) {
        // When form is loaded, check if image is empty but attachments exist
        if (!frm.doc.image) {
            frappe.call({
                method: 'frappe.client.get_list',
                args: {
                    doctype: 'File',
                    filters: {
                        attached_to_doctype: 'Item',
                        attached_to_name: frm.doc.name,
                        is_private: 0
                    },
                    fields: ['file_url'],
                    order_by: 'creation asc',
                    limit: 1
                },
                callback(r) {
                    if (r.message && r.message.length > 0 && r.message[0].file_url) {
                        frm.set_value('image', r.message[0].file_url);
                    }
                }
            });
        }
    }
});
