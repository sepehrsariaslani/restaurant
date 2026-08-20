"""Bootstrap: erpnext after_install, fixtures, seed patches, perms, settings."""
import frappe


def main():
    frappe.init(site="site1.local")
    frappe.connect()

    # 1. ERPNext after_install
    from erpnext.setup.install import after_install

    after_install()
    frappe.db.commit()
    print("1. erpnext after_install OK")

    # 2. restaurant fixtures
    from frappe.utils.fixtures import sync_fixtures

    sync_fixtures("restaurant")
    frappe.db.commit()
    print("2. restaurant fixtures OK")

    # 3. core infra
    for uom in ("Nos", "Kg", "g", "L", "ml", "Box", "Pack", "Dozen"):
        if not frappe.db.exists("UOM", uom):
            frappe.get_doc({"doctype": "UOM", "uom_name": uom}).insert(ignore_permissions=True)
    if not frappe.db.exists("Price List", "Standard Selling"):
        frappe.get_doc({"doctype": "Price List", "price_list_name": "Standard Selling",
                        "selling": 1, "enabled": 1, "currency": "IRR"}).insert(ignore_permissions=True)
    if not frappe.db.exists("Price List", "Standard Buying"):
        frappe.get_doc({"doctype": "Price List", "price_list_name": "Standard Buying",
                        "buying": 1, "enabled": 1, "currency": "IRR"}).insert(ignore_permissions=True)
    if not frappe.db.exists("Item Group", "All Item Groups"):
        frappe.get_doc({"doctype": "Item Group", "item_group_name": "All Item Groups",
                        "parent_item_group": "", "is_group": 1}).insert(ignore_permissions=True)
    frappe.db.commit()
    print("3. UOMs / price lists / root Item Group OK")

    # 4. seed patches
    from restaurant.patches.v0_0.seed_restaurant_demo_data import execute as p0
    from restaurant.patches.v0_1.sync_restaurant_to_core_doctypes import execute as p1
    from restaurant.patches.v0_2.seed_veederakht_production_data import execute as p2
    from restaurant.patches.v0_3.seed_restaurant_table_demo_data import execute as p3
    from restaurant.patches.v0_3.generate_table_qr_codes import execute as p3qr
    from restaurant.patches.v0_4.seed_restaurant_web_content import execute as p4

    for name, fn in (
        ("v0_0", p0), ("v0_1", p1), ("v0_2", p2), ("v0_3", p3), ("v0_3qr", p3qr), ("v0_4", p4),
    ):
        try:
            fn()
            frappe.db.commit()
            print(f"4. patch {name} OK")
        except Exception as exc:
            frappe.db.rollback()
            print(f"4. patch {name} FAILED: {exc}")

    # 5. ensure custom fields (app creates them without commit -> broken on postgres)
    def ensure_cf(dt, fieldname, fieldtype, label, insert_after, description=None, default=None):
        if frappe.db.exists("Custom Field", {"dt": dt, "fieldname": fieldname}):
            return
        payload = {"doctype": "Custom Field", "dt": dt, "fieldname": fieldname,
                   "fieldtype": fieldtype, "label": label, "insert_after": insert_after}
        if description:
            payload["description"] = description
        if default is not None:
            payload["default"] = default
        frappe.get_doc(payload).insert(ignore_permissions=True)

    ensure_cf("Item Group", "show_on_homepage", "Check", "نمایش در صفحه اصلی", "restaurant_is_menu_category", default="1")
    ensure_cf("Item Group", "restaurant_menu_icon", "Data", "آیکون منو", "image",
              description="نام آیکون Lucide برای نمایش گروه در صفحه منو")
    ensure_cf("Item", "restaurant_item_tags", "Small Text", "تگ‌های محصول", "restaurant_allergen_tags",
              description="تگ‌ها را با کاما جدا کنید. مثال: رژیمی, پرفروش, وگان")
    from restaurant.api import setup_coming_soon_field
    try:
        setup_coming_soon_field()
    except Exception:
        pass
    frappe.db.commit()
    print("5. ensure custom fields OK")

    # 6. show_on_homepage for categories
    frappe.db.sql("update `tabItem Group` set show_on_homepage = 1 where restaurant_is_menu_category = 1 and restaurant_is_subcategory = 0")
    frappe.db.commit()
    print("6. show_on_homepage OK")

    # 6b. ERPNext masters
    for wt in ("Transit", "Store"):
        if not frappe.db.exists("Warehouse Type", wt):
            frappe.get_doc({"doctype": "Warehouse Type", "name": wt}).insert(ignore_permissions=True)
    if not frappe.db.exists("Territory", "All Territories"):
        frappe.get_doc({"doctype": "Territory", "territory_name": "All Territories",
                        "is_group": 1, "lft": 1, "rgt": 2}).insert(ignore_permissions=True)
    for cg in ("Individual", "All Customer Groups"):
        if not frappe.db.exists("Customer Group", cg):
            frappe.get_doc({"doctype": "Customer Group", "customer_group_name": cg,
                            "is_group": 1 if cg == "All Customer Groups" else 0}).insert(ignore_permissions=True)
    frappe.db.commit()
    print("6b. territories / customer groups OK")

    # 7. Selling Settings defaults
    ss = frappe.get_doc("Selling Settings")
    changed = False
    if not ss.customer_group:
        ss.customer_group = "Individual"; changed = True
    if not ss.territory:
        ss.territory = "All Territories"; changed = True
    if not ss.selling_price_list:
        ss.selling_price_list = "Standard Selling"; changed = True
    if changed:
        ss.save(ignore_permissions=True)
    frappe.db.commit()
    print("7. Selling Settings OK")

    # 8. Guest permissions
    DOCTYPES = [
        "Item", "Item Group", "Item Price", "Price List", "UOM", "BOM", "BOM Item",
        "Restaurant Table", "Restaurant Table Session", "Restaurant Table Order",
        "Restaurant Order", "Restaurant Web Settings", "Website Settings",
        "Restaurant Menu Category", "Restaurant Menu Item", "Restaurant FAQ",
        "Restaurant Hero Slide", "Restaurant About Section", "Restaurant Branch",
        "Restaurant Branch Schedule", "Restaurant Coupon", "Restaurant Delivery Zone",
        "Restaurant Customer Review", "Restaurant Modifier Group", "Restaurant Modifier Option",
        "Account", "Cost Center", "Company", "Warehouse", "Territory", "Customer Group",
        "Sales Taxes and Charges Template", "Item Tax Template", "Payment Terms Template",
        "Tax Category", "Currency", "Country", "Address", "Contact", "Customer",
        "Sales Order", "Accounts Settings", "Stock Settings", "Selling Settings",
        "Item Default", "Party Account", "Sales Taxes and Charges", "Item Tax",
        "Payment Schedule", "Sales Team", "Project", "Item Variant Attribute",
        "Item Attribute", "Item Variant", "Item Manufacturer", "Website Item",
        "Shipping Rule", "Shipping Rule Condition",
    ]
    added = 0
    for dt in DOCTYPES:
        if not frappe.db.exists("DocType", dt):
            continue
        if frappe.db.sql("select name from `tabDocPerm` where parent=%s and role=%s", (dt, "Guest")):
            continue
        frappe.permissions.add_permission(dt, "Guest")
        added += 1
    frappe.db.commit()
    print(f"8. Guest permissions granted on {added} doctypes")

    # 9. Company
    if not frappe.db.exists("Company", "Veederakht"):
        d = frappe.get_doc({"doctype": "Company", "company_name": "Veederakht", "abbr": "VEED",
                            "default_currency": "IRR", "country": "Iran", "enable_perpetual_inventory": 0})
        d.flags.ignore_mandatory = True
        try:
            d.insert(ignore_permissions=True)
            print("9. Company OK")
        except Exception as exc:
            print(f"9. Company failed: {exc}")
    frappe.db.set_single_value("Global Defaults", "default_company", "Veederakht")
    frappe.db.commit()

    print("BOOTSTRAP DONE")


if __name__ == "__main__":
    main()
