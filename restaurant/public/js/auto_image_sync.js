// Auto-sync item image from File attachments after upload
(function() {
    // Monkey-patch frappe.upload to auto-sync image to parent Item
    if (frappe.upload && !frappe.upload._patched) {
        const originalUpload = frappe.upload.upload;
        frappe.upload.upload = function(opts) {
            const result = originalUpload.apply(this, arguments);
            // After successful upload, sync image to parent Item
            if (opts && opts.args && opts.args.attached_to_doctype === 'Item' && opts.args.attached_to_name) {
                setTimeout(function() {
                    if (opts.file_url) {
                        frappe.call({
                            method: 'frappe.client.set_value',
                            args: {
                                doctype: 'Item',
                                name: opts.args.attached_to_name,
                                fieldname: 'image',
                                value: opts.file_url
                            },
                            callback: function(r) {
                                console.log('Auto-synced image for', opts.args.attached_to_name);
                            }
                        });
                    }
                }, 500);
            }
            return result;
        };
        frappe.upload._patched = true;
    }
})();
