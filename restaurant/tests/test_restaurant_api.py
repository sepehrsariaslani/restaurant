import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import cint

from restaurant.api import (
    get_customer_checkout_profile,
    get_item_detail,
    get_management_dashboard,
    get_management_product_detail,
    get_management_report_product_mix,
    get_management_report_sales_summary,
    get_menu_boot,
    place_order,
    save_customer_delivery_address,
    update_management_product_settings,
)


class TestRestaurantAPI(FrappeTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.company = frappe.db.get_single_value("Global Defaults", "default_company") or frappe.db.get_value(
            "Company", {}, "name"
        )
        cls.uom = frappe.db.get_value("UOM", {}, "name") or "Nos"
        cls.warehouse = frappe.db.get_value("Warehouse", {"is_group": 0}, "name") or frappe.db.get_value(
            "Warehouse", {}, "name"
        )

        suffix = frappe.generate_hash(length=6).lower()
        cls.category_slug = f"test-core-cat-{suffix}"
        cls.subcategory_slug = f"test-core-subcat-{suffix}"
        cls.item_slug = f"test-core-item-{suffix}"

        root_group = frappe.db.get_value(
            "Item Group",
            {
                "restaurant_slug": "restaurant-menu",
                "restaurant_is_menu_category": 0,
            },
            "name",
        ) or frappe.db.get_value("Item Group", {"parent_item_group": ""}, "name")

        category = frappe.get_doc(
            {
                "doctype": "Item Group",
                "item_group_name": f"Test Core Cat {suffix}",
                "parent_item_group": root_group,
                "is_group": 1,
                "restaurant_is_menu_category": 1,
                "restaurant_is_subcategory": 0,
                "restaurant_slug": cls.category_slug,
                "restaurant_sort_order": 1,
                "restaurant_active": 1,
            }
        )
        category.insert(ignore_permissions=True)
        cls.category_group = category.name

        subcategory = frappe.get_doc(
            {
                "doctype": "Item Group",
                "item_group_name": f"Test Core Subcat {suffix}",
                "parent_item_group": cls.category_group,
                "is_group": 0,
                "restaurant_is_menu_category": 1,
                "restaurant_is_subcategory": 1,
                "restaurant_slug": cls.subcategory_slug,
                "restaurant_sort_order": 1,
                "restaurant_active": 1,
            }
        )
        subcategory.insert(ignore_permissions=True)
        cls.subcategory_group = subcategory.name

        raw_item = frappe.get_doc(
            {
                "doctype": "Item",
                "item_code": f"RAW_TEST_{suffix.upper()}",
                "item_name": f"Raw Test {suffix}",
                "item_group": cls.category_group,
                "stock_uom": cls.uom,
                "is_stock_item": 1,
                "is_sales_item": 0,
                "is_purchase_item": 1,
            }
        )
        raw_item.insert(ignore_permissions=True)
        raw_item.db_set("valuation_rate", 100000, update_modified=False)
        if frappe.db.has_column("Item", "restaurant_nutrition_kcal"):
            raw_item.db_set("restaurant_nutrition_kcal", 1650, update_modified=False)
            raw_item.db_set("restaurant_nutrition_protein_g", 310, update_modified=False)
            raw_item.db_set("restaurant_nutrition_carb_g", 0, update_modified=False)
            raw_item.db_set("restaurant_nutrition_fat_g", 36, update_modified=False)
        cls.raw_item_code = raw_item.item_code

        modifier_item = frappe.get_doc(
            {
                "doctype": "Item",
                "item_code": f"MOD_MILK_{suffix.upper()}",
                "item_name": f"Modifier Milk {suffix}",
                "item_group": cls.category_group,
                "stock_uom": cls.uom,
                "is_stock_item": 1,
                "is_sales_item": 0,
                "is_purchase_item": 1,
                "allow_alternative_item": 1,
            }
        )
        modifier_item.insert(ignore_permissions=True)
        cls.modifier_item_code = modifier_item.item_code

        menu_item = frappe.get_doc(
            {
                "doctype": "Item",
                "item_code": f"REST_TEST_{suffix.upper()}",
                "item_name": f"Menu Test {suffix}",
                "item_group": cls.subcategory_group,
                "stock_uom": cls.uom,
                "is_stock_item": 0,
                "is_sales_item": 1,
                "is_purchase_item": 0,
                "standard_rate": 500000,
                "restaurant_enabled": 1,
                "restaurant_slug": cls.item_slug,
                "restaurant_category": cls.category_group,
                "restaurant_subcategory": cls.subcategory_group,
                "restaurant_short_desc": "core item for tests",
                "restaurant_long_desc": "core item for tests",
                "restaurant_base_price": 500000,
                "restaurant_branch": "DEFAULT",
                "restaurant_allow_customization": 1,
            }
        )
        menu_item.insert(ignore_permissions=True)
        if frappe.db.has_column("Item", "restaurant_nutrition_kcal"):
            menu_item.db_set("restaurant_nutrition_kcal", 420, update_modified=False)
            menu_item.db_set("restaurant_nutrition_protein_g", 42, update_modified=False)
            menu_item.db_set("restaurant_nutrition_carb_g", 12, update_modified=False)
            menu_item.db_set("restaurant_nutrition_fat_g", 14, update_modified=False)
        cls.menu_item = menu_item.name

        bom = frappe.get_doc(
            {
                "doctype": "BOM",
                "item": menu_item.item_code,
                "company": cls.company,
                "currency": frappe.db.get_value("Company", cls.company, "default_currency"),
                "conversion_rate": 1,
                "quantity": 1,
                "is_default": 1,
                "is_active": 1,
                "items": [
                    {
                        "item_code": cls.raw_item_code,
                        "qty": 1,
                        "uom": cls.uom,
                        "rate": 100000,
                        "restaurant_customer_label": "مرغ گریل",
                        "restaurant_is_included_by_default": 1,
                        "restaurant_can_remove": 1,
                        "restaurant_is_required": 0,
                        "restaurant_is_editable_qty": 1,
                        "restaurant_min_multiplier": 0,
                        "restaurant_max_multiplier": 3,
                        "restaurant_step_multiplier": 0.5,
                        "restaurant_extra_when_added": 0,
                    }
                ],
            }
        )
        if frappe.get_meta("BOM").has_field("restaurant_modifier_rows"):
            bom.set(
                "restaurant_modifier_rows",
                [
                    {
                        "group_key": "milk-options",
                        "group_title": "Milk Options",
                        "selection_mode": "single",
                        "required": 0,
                        "min_select": 0,
                        "max_select": 1,
                        "modifier_type": "add_on",
                        "option_key": cls.modifier_item_code,
                        "option_label": "Milk Options",
                        "option_item": cls.modifier_item_code,
                        "option_qty": 1,
                        "price_delta": 15000,
                        "recipe_multiplier": 1,
                        "is_default": 0,
                        "is_active": 1,
                    }
                ],
            )
        bom.insert(ignore_permissions=True)
        bom.submit()

        menu_item.db_set("default_bom", bom.name, update_modified=False)
        if frappe.db.has_column("Item", "restaurant_requires_bom"):
            menu_item.db_set("restaurant_requires_bom", 1, update_modified=False)

        if frappe.db.exists("DocType", "Restaurant Branch Production Settings"):
            settings_name = frappe.db.get_value("Restaurant Branch Production Settings", {"branch": "DEFAULT"}, "name")
            if settings_name:
                settings = frappe.get_doc("Restaurant Branch Production Settings", settings_name)
            else:
                settings = frappe.get_doc(
                    {
                        "doctype": "Restaurant Branch Production Settings",
                        "branch": "DEFAULT",
                    }
                )

            settings.company = cls.company
            settings.raw_warehouse = cls.warehouse
            settings.kitchen_wip_warehouse = cls.warehouse
            settings.finished_goods_warehouse = cls.warehouse
            settings.pricing_markup_percent = 10
            settings.is_active = 1
            if settings.is_new():
                settings.insert(ignore_permissions=True)
            else:
                settings.save(ignore_permissions=True)

        no_bom_item = frappe.get_doc(
            {
                "doctype": "Item",
                "item_code": f"REST_NO_BOM_{suffix.upper()}",
                "item_name": f"Menu No BOM {suffix}",
                "item_group": cls.subcategory_group,
                "stock_uom": cls.uom,
                "is_stock_item": 0,
                "is_sales_item": 1,
                "is_purchase_item": 0,
                "standard_rate": 350000,
                "restaurant_enabled": 1,
                "restaurant_slug": f"test-core-no-bom-{suffix}",
                "restaurant_category": cls.category_group,
                "restaurant_subcategory": cls.subcategory_group,
                "restaurant_short_desc": "no bom test item",
                "restaurant_long_desc": "no bom test item",
                "restaurant_base_price": 350000,
                "restaurant_branch": "DEFAULT",
                "restaurant_allow_customization": 0,
            }
        )
        no_bom_item.insert(ignore_permissions=True)
        if frappe.db.has_column("Item", "restaurant_requires_bom"):
            no_bom_item.db_set("restaurant_requires_bom", 0, update_modified=False)
        cls.no_bom_item_slug = no_bom_item.restaurant_slug

        service_item = frappe.get_doc(
            {
                "doctype": "Item",
                "item_code": f"REST_SERVICE_{suffix.upper()}",
                "item_name": f"Service Item {suffix}",
                "item_group": cls.category_group,
                "stock_uom": cls.uom,
                "is_stock_item": 0,
                "is_sales_item": 1,
                "is_purchase_item": 0,
                "standard_rate": 25000,
                "restaurant_enabled": 0,
            }
        )
        service_item.insert(ignore_permissions=True)
        if frappe.db.has_column("Item", "restaurant_auto_add_to_order"):
            service_item.db_set("restaurant_auto_add_to_order", 1, update_modified=False)
        if frappe.db.has_column("Item", "restaurant_auto_add_qty"):
            service_item.db_set("restaurant_auto_add_qty", 1, update_modified=False)
        if frappe.db.has_column("Item", "restaurant_requires_bom"):
            service_item.db_set("restaurant_requires_bom", 0, update_modified=False)
        if frappe.db.has_column("Item", "restaurant_branch"):
            service_item.db_set("restaurant_branch", "DEFAULT", update_modified=False)
        cls.service_item_code = service_item.item_code

        frappe.db.commit()

    def _valid_order_items(self):
        return [
            {
                "item_slug": self.item_slug,
                "qty": 1,
                "customization": {
                    "ingredient_adjustments": [
                        {
                            "ingredient_key": "مرغ گریل",
                            "multiplier": 2,
                        }
                    ],
                    "selected_modifiers": [],
                },
            }
        ]

    def test_get_menu_boot_payload(self):
        payload = get_menu_boot()
        self.assertIn("categories", payload)
        self.assertIn("featured_items", payload)
        self.assertIn("hero_slides", payload)
        self.assertIn("about_us_sections", payload)
        self.assertIn("faq_items", payload)
        self.assertIn("currency", payload)
        self.assertIn("branding", payload)
        self.assertIsInstance(payload.get("hero_slides"), list)
        self.assertIsInstance(payload.get("about_us_sections"), list)
        self.assertIsInstance(payload.get("faq_items"), list)

    def test_get_menu_boot_filters_inactive_content_rows(self):
        if not frappe.db.exists("DocType", "Restaurant Hero Slide"):
            self.skipTest("Restaurant Hero Slide is not installed.")
        if not frappe.db.exists("DocType", "Restaurant About Section"):
            self.skipTest("Restaurant About Section is not installed.")
        if not frappe.db.exists("DocType", "Restaurant FAQ"):
            self.skipTest("Restaurant FAQ is not installed.")

        suffix = frappe.generate_hash(length=6).lower()
        item_name = frappe.db.get_value("Item", {"restaurant_enabled": 1}, "name")

        hero_active = frappe.get_doc(
            {
                "doctype": "Restaurant Hero Slide",
                "title": f"Hero Active {suffix}",
                "linked_item": item_name or "",
                "cta_label": "مشاهده",
                "sort_order": 9100,
                "is_active": 1,
            }
        ).insert(ignore_permissions=True)
        hero_inactive = frappe.get_doc(
            {
                "doctype": "Restaurant Hero Slide",
                "title": f"Hero Inactive {suffix}",
                "linked_item": item_name or "",
                "cta_label": "مشاهده",
                "sort_order": 9101,
                "is_active": 0,
            }
        ).insert(ignore_permissions=True)

        about_active = frappe.get_doc(
            {
                "doctype": "Restaurant About Section",
                "title": f"About Active {suffix}",
                "body_text": "Active about row",
                "sort_order": 9100,
                "is_active": 1,
            }
        ).insert(ignore_permissions=True)
        about_inactive = frappe.get_doc(
            {
                "doctype": "Restaurant About Section",
                "title": f"About Inactive {suffix}",
                "body_text": "Inactive about row",
                "sort_order": 9101,
                "is_active": 0,
            }
        ).insert(ignore_permissions=True)

        faq_active = frappe.get_doc(
            {
                "doctype": "Restaurant FAQ",
                "question": f"FAQ Active {suffix}?",
                "answer": "Active faq row",
                "sort_order": 9100,
                "is_active": 1,
            }
        ).insert(ignore_permissions=True)
        faq_inactive = frappe.get_doc(
            {
                "doctype": "Restaurant FAQ",
                "question": f"FAQ Inactive {suffix}?",
                "answer": "Inactive faq row",
                "sort_order": 9101,
                "is_active": 0,
            }
        ).insert(ignore_permissions=True)

        payload = get_menu_boot()
        hero_names = {row.get("name") for row in payload.get("hero_slides", [])}
        about_names = {row.get("name") for row in payload.get("about_us_sections", [])}
        faq_names = {row.get("name") for row in payload.get("faq_items", [])}

        self.assertIn(hero_active.name, hero_names)
        self.assertNotIn(hero_inactive.name, hero_names)
        self.assertIn(about_active.name, about_names)
        self.assertNotIn(about_inactive.name, about_names)
        self.assertIn(faq_active.name, faq_names)
        self.assertNotIn(faq_inactive.name, faq_names)

    def test_get_item_detail_payload(self):
        payload = get_item_detail(self.item_slug)
        self.assertEqual(payload["item"]["slug"], self.item_slug)
        self.assertTrue(any(row["key"] == "مرغ گریل" for row in payload["ingredients"]))

        ingredient = next(row for row in payload["ingredients"] if row["key"] == "مرغ گریل")
        self.assertIn("min_multiplier", ingredient)
        self.assertIn("max_multiplier", ingredient)
        self.assertIn("step_multiplier", ingredient)
        self.assertIn("base_qty", ingredient)
        self.assertIn("nutrition", payload["item"])
        self.assertIn("nutrition_kcal", ingredient)

    def test_get_item_detail_reads_modifier_options_from_bom_modifier_rows(self):
        payload = get_item_detail(self.item_slug)
        group = next((row for row in payload.get("modifier_groups", []) if row.get("title") == "Milk Options"), None)
        self.assertIsNotNone(group)
        self.assertTrue(any(opt.get("name") == self.modifier_item_code for opt in group.get("options", [])))

    def test_management_product_settings_normalize_legacy_builder_modes(self):
        item_doc = frappe.get_doc("Item", self.menu_item)
        if frappe.db.has_column("Item", "restaurant_is_customizable"):
            item_doc.db_set("restaurant_is_customizable", 1, update_modified=False)
        if frappe.db.has_column("Item", "restaurant_kitchen_print_mode"):
            item_doc.db_set("restaurant_kitchen_print_mode", "full_selections", update_modified=False)
        if frappe.db.has_column("Item", "restaurant_stock_consumption_mode"):
            item_doc.db_set("restaurant_stock_consumption_mode", "from_builder", update_modified=False)
        frappe.db.commit()

        detail = get_management_product_detail(item_doc.name)
        self.assertEqual(detail["item"]["restaurant_kitchen_print_mode"], "parent_with_components")
        self.assertEqual(
            detail["item"]["restaurant_stock_consumption_mode"],
            "consume_selected_components",
        )

        updated = update_management_product_settings(
            {
                "item_name": item_doc.name,
                "restaurant_kitchen_print_mode": "full_selections",
                "restaurant_stock_consumption_mode": "from_builder",
            }
        )
        self.assertEqual(updated["item"]["restaurant_kitchen_print_mode"], "parent_with_components")
        self.assertEqual(
            updated["item"]["restaurant_stock_consumption_mode"],
            "consume_selected_components",
        )

        reloaded = frappe.get_doc("Item", item_doc.name)
        self.assertEqual(reloaded.get("restaurant_kitchen_print_mode"), "parent_with_components")
        self.assertEqual(
            reloaded.get("restaurant_stock_consumption_mode"),
            "consume_selected_components",
        )

    def test_item_save_normalizes_legacy_builder_modes(self):
        item_doc = frappe.get_doc("Item", self.menu_item)
        if frappe.db.has_column("Item", "restaurant_is_customizable"):
            item_doc.restaurant_is_customizable = 1
        if frappe.db.has_column("Item", "restaurant_kitchen_print_mode"):
            item_doc.restaurant_kitchen_print_mode = "full_selections"
        if frappe.db.has_column("Item", "restaurant_stock_consumption_mode"):
            item_doc.restaurant_stock_consumption_mode = "from_builder"

        item_doc.save(ignore_permissions=True)

        reloaded = frappe.get_doc("Item", item_doc.name)
        self.assertEqual(reloaded.get("restaurant_kitchen_print_mode"), "parent_with_components")
        self.assertEqual(
            reloaded.get("restaurant_stock_consumption_mode"),
            "consume_selected_components",
        )

    def test_place_order_returns_production_payload(self):
        payload = place_order(
            customer_info={"name": "تست", "mobile": "09123456789"},
            order_type="takeaway",
            items=self._valid_order_items(),
            note="تست خودکار",
        )

        self.assertEqual(payload["status"], "success")
        self.assertTrue(payload["order_code"].startswith("R"))
        self.assertGreater(payload["grand_total"], 0)
        self.assertIn("production_tickets", payload)
        self.assertIn("work_orders", payload)

    def test_place_order_rejects_min_multiplier_violation(self):
        broken = self._valid_order_items()
        broken[0]["customization"]["ingredient_adjustments"] = [
            {
                "ingredient_key": "مرغ گریل",
                "multiplier": -1,
            }
        ]

        with self.assertRaises(frappe.ValidationError):
            place_order(
                customer_info={"name": "تست", "mobile": "09123456789"},
                order_type="takeaway",
                items=broken,
            )

    def test_place_order_without_bom_does_not_fail(self):
        payload = place_order(
            customer_info={"name": "بدون بوم", "mobile": "09121112222"},
            order_type="takeaway",
            items=[
                {
                    "item_slug": self.no_bom_item_slug,
                    "qty": 1,
                    "customization": {
                        "ingredient_adjustments": [],
                        "selected_modifiers": [],
                    },
                }
            ],
        )

        self.assertEqual(payload["status"], "success")
        skipped_reasons = {row.get("reason") for row in payload.get("production_skipped_items", [])}
        self.assertTrue({"production_not_required", "missing_bom"} & skipped_reasons)

    def test_place_order_includes_auto_service_items(self):
        payload = place_order(
            customer_info={"name": "اقلام همراه", "mobile": "09123334444"},
            order_type="takeaway",
            items=self._valid_order_items(),
            include_service_items=1,
        )

        self.assertEqual(payload["status"], "success")
        order_doc = frappe.get_doc("Sales Order", payload["order_id"])
        self.assertTrue(any(row.item_code == self.service_item_code for row in (order_doc.items or [])))

    def test_save_customer_delivery_address_and_checkout_profile(self):
        saved = save_customer_delivery_address(
            customer_info={"name": "مشتری نقشه", "mobile": "09128889977"},
            address_info={
                "title": "خانه",
                "phone": "09128889977",
                "address_line": "تهران، خیابان اول",
                "plaque": "12",
                "unit": "4",
                "floor": "2",
                "lat": 35.7442,
                "lng": 51.4348,
                "is_primary": 1,
            },
        )

        self.assertTrue(saved.get("address"))
        self.assertTrue(saved["address"].get("id"))

        profile = get_customer_checkout_profile("09128889977")
        self.assertEqual(cint(profile.get("customer", {}).get("exists")), 1)
        self.assertTrue(profile.get("addresses"))
        first = profile["addresses"][0]
        self.assertEqual(first.get("title"), "خانه")
        self.assertAlmostEqual(float(first.get("lat")), 35.7442, places=3)
        self.assertAlmostEqual(float(first.get("lng")), 51.4348, places=3)

    def test_place_order_with_delivery_mode_and_address_snapshot(self):
        payload = place_order(
            customer_info={"name": "ارسال تست", "mobile": "09125556677"},
            delivery_mode="delivery",
            items=self._valid_order_items(),
            delivery_address_snapshot={
                "title": "خانه",
                "phone": "09125556677",
                "address_line": "تهران، خیابان تست",
                "plaque": "21",
                "unit": "1",
                "floor": "3",
                "lat": 35.7025,
                "lng": 51.3921,
            },
        )

        self.assertEqual(payload["status"], "success")
        order_doc = frappe.get_doc("Sales Order", payload["order_id"])
        if frappe.db.has_column("Sales Order", "restaurant_order_type"):
            self.assertEqual((order_doc.get("restaurant_order_type") or "").strip().lower(), "delivery")
        if frappe.db.has_column("Sales Order", "restaurant_delivery_address"):
            self.assertIn("تهران", order_doc.get("restaurant_delivery_address") or "")

    def test_management_dashboard_and_sales_report_payload(self):
        payload = get_management_dashboard()
        self.assertIn("kpis", payload)
        self.assertIn("recent_orders", payload)
        self.assertIn("top_products", payload)

        report = get_management_report_sales_summary()
        self.assertEqual(report.get("report_key"), "sales-summary")
        self.assertIn("summary", report)
        self.assertIn("rows", report)

    def test_management_product_mix_report_payload(self):
        report = get_management_report_product_mix()
        self.assertEqual(report.get("report_key"), "product-mix")
        self.assertIn("summary", report)
        self.assertIn("rows", report)
        self.assertIn("tables", report)
