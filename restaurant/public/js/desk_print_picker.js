(() => {
    const FORM_PATCH_FLAG = "__restaurant_print_picker_form_patched";
    const VIEW_PATCH_FLAG = "__restaurant_print_picker_view_patched";
    const ROUTE_OPTION_KEY = "restaurant_selected_print_format";

    function getAvailableFormats(doctype) {
        if (!doctype || !frappe.meta || !frappe.meta.get_print_formats) {
            return [];
        }

        const formats = frappe.meta.get_print_formats(doctype) || [];
        return formats.filter((row) => typeof row === "string" && row.trim());
    }

    function getSelectedRouteFormat() {
        if (!frappe.route_options) {
            return "";
        }
        return frappe.route_options[ROUTE_OPTION_KEY] || "";
    }

    function clearSelectedRouteFormat() {
        if (!frappe.route_options) {
            return;
        }
        delete frappe.route_options[ROUTE_OPTION_KEY];
    }

    function showUnsavedWarning(frm) {
        if (!frm || !frm.is_dirty || !frm.is_dirty()) {
            return;
        }

        frappe.toast({
            message: __(
                "This document has unsaved changes which might not appear in final PDF. <br> Consider saving the document before printing."
            ),
            indicator: "yellow",
        });
    }

    function openPrintRoute(frm, selectedFormat) {
        frappe.route_options = frappe.route_options || {};
        frappe.route_options.frm = frm;
        frappe.route_options[ROUTE_OPTION_KEY] = selectedFormat;
        frappe.set_route("print", frm.doctype, frm.doc.name);
    }

    function patchFormPrototype() {
        const formProto = frappe.ui && frappe.ui.form && frappe.ui.form.Form && frappe.ui.form.Form.prototype;
        if (!formProto || formProto[FORM_PATCH_FLAG]) {
            return;
        }

        const originalPrintDoc = formProto.print_doc;
        formProto.print_doc = function () {
            const formats = getAvailableFormats(this.doctype);
            if (!Array.isArray(formats) || formats.length <= 1 || !this || !this.doc || !this.doc.name) {
                return originalPrintDoc.call(this);
            }

            const fallbackDefault = formats[0];
            const configuredDefault = this.meta && this.meta.default_print_format;
            const selectedDefault = formats.includes(configuredDefault) ? configuredDefault : fallbackDefault;

            frappe.prompt(
                [
                    {
                        fieldtype: "Select",
                        fieldname: "print_format",
                        label: __("فرمت چاپ"),
                        options: formats.join("\n"),
                        default: selectedDefault,
                        reqd: 1,
                    },
                ],
                (values) => {
                    const selectedFormat = (values && values.print_format) || selectedDefault;
                    showUnsavedWarning(this);
                    openPrintRoute(this, selectedFormat);
                },
                __("انتخاب فرمت چاپ"),
                __("ادامه")
            );
        };

        formProto[FORM_PATCH_FLAG] = true;
    }

    function patchPrintViewPrototype() {
        const printViewProto =
            frappe.ui && frappe.ui.form && frappe.ui.form.PrintView && frappe.ui.form.PrintView.prototype;
        if (!printViewProto || printViewProto[VIEW_PATCH_FLAG]) {
            return !!printViewProto;
        }

        const originalSetDefaultPrintFormat = printViewProto.set_default_print_format;
        printViewProto.set_default_print_format = function () {
            originalSetDefaultPrintFormat.call(this);

            const selectedFormat = getSelectedRouteFormat();
            if (!selectedFormat) {
                return;
            }

            const doctype = this.frm && this.frm.doctype;
            const formats = getAvailableFormats(doctype);
            if (!formats.includes(selectedFormat)) {
                clearSelectedRouteFormat();
                return;
            }

            this.print_format_selector.val(selectedFormat);
            clearSelectedRouteFormat();
        };

        printViewProto[VIEW_PATCH_FLAG] = true;
        return true;
    }

    function ensureViewPatchWithRetry() {
        let attempts = 0;
        const intervalId = setInterval(() => {
            attempts += 1;
            if (patchPrintViewPrototype() || attempts >= 25) {
                clearInterval(intervalId);
            }
        }, 120);
    }

    function bootPatches() {
        patchFormPrototype();
        patchPrintViewPrototype();
    }

    bootPatches();

    if (frappe.router && frappe.router.on) {
        frappe.router.on("change", () => {
            bootPatches();
            if (getSelectedRouteFormat()) {
                ensureViewPatchWithRetry();
            }
        });
    }
})();
