import frappe
from base64 import b64decode
from frappe.model.document import Document
from frappe.twofactor import get_qr_svg_code
from frappe.utils import get_url
from frappe.utils.file_manager import save_file


class RestaurantTable(Document):
    def validate(self):
        self.table_number = (self.table_number or "").strip()
        if not self.table_number:
            frappe.throw("Table Number is required.")
        self._ensure_qr_code_token()
        self._sync_qr_target_url()
        self._ensure_qr_code_image()

    def before_insert(self):
        self._ensure_qr_code_token()

    def after_insert(self):
        if self.qr_code_image:
            return
        self._sync_qr_target_url()
        self._ensure_qr_code_image()
        if self.qr_target_url:
            self.db_set("qr_target_url", self.qr_target_url, update_modified=False)
        if self.qr_code_image:
            self.db_set("qr_code_image", self.qr_code_image, update_modified=False)

    def _ensure_qr_code_token(self):
        if self.qr_code_token:
            return

        for _ in range(10):
            token = frappe.generate_hash(length=16)
            if not frappe.db.exists("Restaurant Table", {"qr_code_token": token}):
                self.qr_code_token = token
                return

        frappe.throw("Could not generate a unique QR token for this table.")

    def _sync_qr_target_url(self):
        if not self.qr_code_token:
            return
        self.qr_target_url = get_url(f"/table/{self.qr_code_token}")
        self.qr_live_url = get_url(f"/api/method/restaurant.api.get_table_qr_svg?qr_token={self.qr_code_token}")

    def _ensure_qr_code_image(self):
        if not self.name or not self.qr_code_token or not self.qr_target_url:
            return

        token_changed = False
        if not self.is_new():
            token_changed = self.has_value_changed("qr_code_token")

        if self.qr_code_image and not token_changed:
            return

        if token_changed and self.name:
            self._delete_existing_qr_files()

        qr_svg = get_qr_svg_code(self.qr_target_url)
        qr_content = self._normalize_qr_svg_bytes(qr_svg)

        max_size = frappe.local.conf.get("max_file_size")
        if isinstance(max_size, str) and max_size.isdigit():
            frappe.local.conf.max_file_size = int(max_size)

        self._delete_existing_qr_files()

        file_name = f"restaurant-table-{self.table_number or self.name}-qr.svg"
        file_doc = save_file(
            fname=file_name,
            content=qr_content,
            dt=self.doctype,
            dn=self.name,
            is_private=0,
            df="qr_code_image",
        )
        self.qr_code_image = file_doc.file_url

    def _delete_existing_qr_files(self):
        file_names = frappe.get_all(
            "File",
            filters={
                "attached_to_doctype": self.doctype,
                "attached_to_name": self.name,
                "attached_to_field": "qr_code_image",
            },
            pluck="name",
        )
        for file_name in file_names:
            frappe.delete_doc("File", file_name, ignore_permissions=True)

    def _normalize_qr_svg_bytes(self, qr_svg):
        if isinstance(qr_svg, str):
            raw = qr_svg.encode("utf-8")
        else:
            raw = bytes(qr_svg)

        stripped = raw.strip()
        if stripped.startswith(b"<"):
            return stripped

        # frappe.twofactor.get_qr_svg_code may return base64-encoded SVG bytes.
        try:
            decoded = b64decode(stripped, validate=True)
            if decoded.strip().startswith(b"<"):
                return decoded.strip()
        except Exception:
            pass

        return stripped
