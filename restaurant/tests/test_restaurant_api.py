from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import cint, flt

from restaurant.api import (
	_build_ticket_components,
	_extract_qty_map_from_ticket,
	_recalculate_line,
	_sync_work_order_required_items,
	compute_builder_price,
	get_customer_checkout_profile,
	get_builder_template,
	get_item_detail,
	get_related_items,
	get_management_bom_context,
	get_management_bom_doc,
	get_management_dashboard,
	get_management_modifier_group_detail,
	get_management_modifier_groups_context,
	get_management_product_detail,
	get_management_report_product_mix,
	get_management_report_sales_summary,
	get_menu_boot,
	place_order,
	save_customer_delivery_address,
	save_builder_selection,
	save_management_modifier_group,
	set_management_default_price_list,
	set_management_product_price,
	update_management_product_settings,
)


class TestRestaurantAPI(FrappeTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._created_test_price_lists = set()
        cls._cleanup_docs = []
        cls._created_test_uoms = set()
        if frappe.db.exists("DocType", "Selling Settings"):
            cls._original_selling_price_list = frappe.db.get_single_value("Selling Settings", "selling_price_list") or ""
        else:
            cls._original_selling_price_list = ""

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
        cls._remember_cleanup_doc("Item Group", category.name)

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
        cls._remember_cleanup_doc("Item Group", subcategory.name)

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
                "allow_alternative_item": 1,
            }
        )
        raw_item.insert(ignore_permissions=True)
        cls._remember_cleanup_doc("Item", raw_item.item_code)
        raw_item.db_set("valuation_rate", 100000, update_modified=False)
        if frappe.db.has_column("Item", "restaurant_nutrition_kcal"):
            raw_item.db_set("restaurant_nutrition_kcal", 1650, update_modified=False)
            raw_item.db_set("restaurant_nutrition_protein_g", 310, update_modified=False)
            raw_item.db_set("restaurant_nutrition_carb_g", 0, update_modified=False)
            raw_item.db_set("restaurant_nutrition_fat_g", 36, update_modified=False)
        cls.raw_item_code = raw_item.item_code

        alternative_item = frappe.get_doc(
            {
                "doctype": "Item",
                "item_code": f"RAW_ALT_{suffix.upper()}",
                "item_name": f"Raw Alternative {suffix}",
                "item_group": cls.category_group,
                "stock_uom": cls.uom,
                "is_stock_item": 1,
                "is_sales_item": 0,
                "is_purchase_item": 1,
                "allow_alternative_item": 1,
            }
        )
        alternative_item.insert(ignore_permissions=True)
        cls._remember_cleanup_doc("Item", alternative_item.item_code)
        cls.alternative_item_code = alternative_item.item_code

        cls._create_item_alternative(cls.raw_item_code, cls.alternative_item_code)

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
        cls._remember_cleanup_doc("Item", modifier_item.item_code)
        cls.modifier_item_code = modifier_item.item_code
        cls.modifier_group_title = f"Milk Options {suffix}"

        service_modifier_item = frappe.get_doc(
            {
                "doctype": "Item",
                "item_code": f"MOD_SERVICE_{suffix.upper()}",
                "item_name": f"Modifier Service {suffix}",
                "item_group": cls.category_group,
                "stock_uom": cls.uom,
                "is_stock_item": 0,
                "is_sales_item": 0,
                "is_purchase_item": 0,
            }
        )
        service_modifier_item.insert(ignore_permissions=True)
        cls._remember_cleanup_doc("Item", service_modifier_item.item_code)
        cls.service_modifier_item_code = service_modifier_item.item_code

        modifier_group = frappe.get_doc(
            {
                "doctype": "Restaurant Modifier Group",
                "title": cls.modifier_group_title,
                "selection_mode": "single",
                "required": 0,
                "min_select": 0,
                "max_select": 1,
                "sort_order": 1,
                "is_active": 1,
                "options": [
                    {
                        "option_name": cls.modifier_item_code,
                        "action_type": "add_on",
                        "option_item": cls.modifier_item_code,
                        "option_qty": 1,
                        "price_delta": 15000,
                        "recipe_multiplier": 1,
                        "min_qty": 1,
                        "max_qty": 1,
                        "qty_step": 1,
                        "is_default": 0,
                        "sort_order": 1,
                        "is_active": 1,
                    }
                ],
            }
        )
        modifier_group.insert(ignore_permissions=True)
        cls.modifier_group_name = modifier_group.name
        cls._remember_cleanup_doc("Restaurant Modifier Group", modifier_group.name)

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
        cls._remember_cleanup_doc("Item", menu_item.item_code)
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
                        "allow_alternative_item": 1,
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
                        "modifier_group": cls.modifier_group_name,
                        "group_key": cls.modifier_group_name,
                        "group_title": cls.modifier_group_title,
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
        cls.bom_name = bom.name
        cls._remember_cleanup_doc("BOM", bom.name)

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
        cls._remember_cleanup_doc("Item", no_bom_item.item_code)
        cls.no_bom_item_code = no_bom_item.item_code
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
        cls._remember_cleanup_doc("Item", service_item.item_code)
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

    @classmethod
    def _remember_cleanup_doc(cls, doctype, name):
        if not doctype or not name:
            return
        cls._cleanup_docs.append((doctype, name))

    @classmethod
    def tearDownClass(cls):
        try:
            cls._cleanup_test_transactions()
            for price_list_name in list(getattr(cls, "_created_test_price_lists", set())):
                if not frappe.db.exists("Price List", price_list_name):
                    continue
                for item_price_name in frappe.get_all(
                    "Item Price",
                    filters={"price_list": price_list_name},
                    pluck="name",
                ):
                    frappe.delete_doc("Item Price", item_price_name, force=1, ignore_permissions=True)
                frappe.delete_doc("Price List", price_list_name, force=1, ignore_permissions=True)

            for uom_name in list(getattr(cls, "_created_test_uoms", set())):
                if frappe.db.exists("UOM", uom_name):
                    frappe.delete_doc("UOM", uom_name, force=1, ignore_permissions=True)

            for doctype, name in reversed(getattr(cls, "_cleanup_docs", [])):
                if not frappe.db.exists(doctype, name):
                    continue
                if doctype == "BOM":
                    doc = frappe.get_doc(doctype, name)
                    if cint(doc.docstatus) == 1:
                        doc.cancel()
                frappe.delete_doc(doctype, name, force=1, ignore_permissions=True)
            frappe.db.commit()
        finally:
            super().tearDownClass()

    @classmethod
    def _cleanup_test_transactions(cls):
        item_codes = [
            code
            for code in {
                getattr(cls, "menu_item", ""),
                getattr(cls, "no_bom_item_code", ""),
                getattr(cls, "service_item_code", ""),
            }
            if code
        ]
        if not item_codes:
            return

        sales_order_names = set(
            frappe.get_all(
                "Sales Order Item",
                filters={"item_code": ["in", item_codes]},
                pluck="parent",
                ignore_permissions=True,
            )
        )

        work_order_names = set(
            frappe.get_all(
                "Work Order",
                filters={"production_item": ["in", item_codes]},
                pluck="name",
                ignore_permissions=True,
            )
        )

        ticket_names = set(
            frappe.get_all(
                "Restaurant Production Ticket",
                filters={"menu_item": ["in", item_codes]},
                pluck="name",
                ignore_permissions=True,
            )
        ) if frappe.db.exists("DocType", "Restaurant Production Ticket") else set()

        for work_order_name in work_order_names:
            if frappe.db.exists("Work Order", work_order_name):
                frappe.delete_doc("Work Order", work_order_name, force=1, ignore_permissions=True)
        for ticket_name in ticket_names:
            if frappe.db.exists("Restaurant Production Ticket", ticket_name):
                frappe.delete_doc("Restaurant Production Ticket", ticket_name, force=1, ignore_permissions=True)
        for sales_order_name in sales_order_names:
            if frappe.db.exists("Sales Order", sales_order_name):
                frappe.delete_doc("Sales Order", sales_order_name, force=1, ignore_permissions=True)

    def tearDown(self):
        super().tearDown()
        if frappe.db.exists("DocType", "Selling Settings"):
            frappe.db.set_single_value(
                "Selling Settings",
                "selling_price_list",
                self._original_selling_price_list or "",
            )

        for price_list_name in list(self._created_test_price_lists):
            if not frappe.db.exists("Price List", price_list_name):
                self._created_test_price_lists.discard(price_list_name)
                continue
            for item_price_name in frappe.get_all(
                "Item Price",
                filters={"price_list": price_list_name},
                pluck="name",
            ):
                frappe.delete_doc("Item Price", item_price_name, force=1, ignore_permissions=True)
            frappe.delete_doc("Price List", price_list_name, force=1, ignore_permissions=True)
            self._created_test_price_lists.discard(price_list_name)
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

    def _update_primary_modifier_option(self, **overrides):
        group_doc = frappe.get_doc("Restaurant Modifier Group", self.modifier_group_name)
        option_row = (group_doc.options or [None])[0]
        self.assertIsNotNone(option_row)

        original = {
            "option_name": option_row.option_name,
            "action_type": option_row.action_type,
            "option_item": option_row.option_item,
            "option_uom": option_row.option_uom,
            "option_qty": option_row.option_qty,
            "price_delta": option_row.price_delta,
            "recipe_multiplier": option_row.recipe_multiplier,
            "min_qty": option_row.min_qty,
            "max_qty": option_row.max_qty,
            "qty_step": option_row.qty_step,
            "is_default": option_row.is_default,
            "sort_order": option_row.sort_order,
            "is_active": option_row.is_active,
        }

        for fieldname, value in overrides.items():
            setattr(option_row, fieldname, value)

        group_doc.save(ignore_permissions=True)
        if "option_uom" in overrides and option_row.name:
            frappe.db.set_value(
                "Restaurant Modifier Option",
                option_row.name,
                "option_uom",
                overrides.get("option_uom") or "",
                update_modified=False,
            )
        frappe.db.commit()
        return original

    def _restore_primary_modifier_option(self, original):
        group_doc = frappe.get_doc("Restaurant Modifier Group", self.modifier_group_name)
        option_row = (group_doc.options or [None])[0]
        if not option_row:
            return
        for fieldname, value in (original or {}).items():
            setattr(option_row, fieldname, value)
        group_doc.save(ignore_permissions=True)
        if "option_uom" in (original or {}) and option_row.name:
            frappe.db.set_value(
                "Restaurant Modifier Option",
                option_row.name,
                "option_uom",
                (original or {}).get("option_uom") or "",
                update_modified=False,
            )
        frappe.db.commit()

    def _ensure_uom(self, uom_name):
        uom_name = (uom_name or "").strip()
        if not uom_name:
            return ""
        if frappe.db.exists("UOM", uom_name):
            return uom_name
        frappe.get_doc(
            {
                "doctype": "UOM",
                "uom_name": uom_name,
                "enabled": 1,
            }
        ).insert(ignore_permissions=True)
        self._created_test_uoms.add(uom_name)
        frappe.db.commit()
        return uom_name

    def _ensure_test_price_list(self, suffix):
        price_list_name = f"Modifier Price List {suffix}"
        if not frappe.db.exists("Price List", price_list_name):
            price_list = frappe.get_doc(
                {
                    "doctype": "Price List",
                    "price_list_name": price_list_name,
                    "enabled": 1,
                    "selling": 1,
                    "currency": frappe.db.get_value("Company", self.company, "default_currency") or "IRR",
                }
            )
            price_list.insert(ignore_permissions=True)
        else:
            price_list = frappe.get_doc("Price List", price_list_name)
        self._created_test_price_lists.add(price_list.name)
        set_management_default_price_list(price_list.name)
        return price_list

    def _set_builder_item_flags(self, item_code, template_name):
        updates = {}
        if frappe.db.has_column("Item", "restaurant_is_customizable"):
            updates["restaurant_is_customizable"] = 1
        if frappe.db.has_column("Item", "restaurant_builder_active"):
            updates["restaurant_builder_active"] = 1
        if frappe.db.has_column("Item", "restaurant_builder_template"):
            updates["restaurant_builder_template"] = template_name
        if frappe.db.has_column("Item", "restaurant_allow_direct_add"):
            updates["restaurant_allow_direct_add"] = 0
        if frappe.db.has_column("Item", "restaurant_requires_bom"):
            updates["restaurant_requires_bom"] = 1
        if updates:
            frappe.db.set_value("Item", item_code, updates, update_modified=False)

    def _make_builder_product_fixture(self, suffix):
        base_component = frappe.get_doc(
            {
                "doctype": "Item",
                "item_code": f"BUILDER_BASE_{suffix.upper()}",
                "item_name": f"Builder Base {suffix}",
                "item_group": self.category_group,
                "stock_uom": self.uom,
                "is_stock_item": 1,
                "is_sales_item": 0,
                "is_purchase_item": 1,
            }
        )
        base_component.insert(ignore_permissions=True)
        self._remember_cleanup_doc("Item", base_component.item_code)

        template = frappe.get_doc(
            {
                "doctype": "Product Builder Template",
                "title": f"Protein Bowl {suffix}",
                "slug": f"protein-bowl-{suffix}",
                "is_active": 1,
                "show_price_live": 1,
                "steps": [
                    {
                        "step_title": "پروتئین",
                        "step_key": "protein",
                        "sort_order": 0,
                        "selection_mode": "multiple",
                        "min_select": 1,
                        "max_select": 3,
                        "is_required": 1,
                        "show_step_price": 1,
                        "options": [
                            {
                                "option_label": "مرغ",
                                "option_key": "chicken",
                                "sort_order": 0,
                                "item": self.raw_item_code,
                                "portion_qty": 120,
                                "portion_uom": self.uom,
                                "min_portions": 0,
                                "max_portions": 3,
                                "portion_step": 1,
                                "price_type": "fixed",
                                "is_available": 1,
                            },
                            {
                                "option_label": "میگو",
                                "option_key": "shrimp",
                                "sort_order": 1,
                                "item": self.alternative_item_code,
                                "portion_qty": 120,
                                "portion_uom": self.uom,
                                "min_portions": 0,
                                "max_portions": 3,
                                "portion_step": 1,
                                "price_type": "fixed",
                                "is_available": 1,
                            },
                        ],
                    },
                    {
                        "step_title": "افزودنی خدماتی",
                        "step_key": "service_addon",
                        "sort_order": 1,
                        "selection_mode": "multiple",
                        "min_select": 0,
                        "max_select": 1,
                        "is_required": 0,
                        "show_step_price": 1,
                        "options": [
                            {
                                "option_label": "سس ویژه",
                                "option_key": "service_sauce",
                                "sort_order": 0,
                                "item": self.service_modifier_item_code,
                                "portion_qty": 1,
                                "portion_uom": self.uom,
                                "min_portions": 0,
                                "max_portions": 1,
                                "portion_step": 1,
                                "price_type": "fixed",
                                "is_available": 1,
                            }
                        ],
                    },
                ],
            }
        )
        template.insert(ignore_permissions=True)
        self._remember_cleanup_doc("Product Builder Template", template.name)

        item_code = f"REST_BUILDER_{suffix.upper()}"
        item_slug = f"builder-item-{suffix}"
        builder_item = frappe.get_doc(
            {
                "doctype": "Item",
                "item_code": item_code,
                "item_name": f"Builder Item {suffix}",
                "item_group": self.subcategory_group,
                "stock_uom": self.uom,
                "is_stock_item": 0,
                "is_sales_item": 1,
                "is_purchase_item": 0,
                "standard_rate": 500000,
                "restaurant_enabled": 1,
                "restaurant_slug": item_slug,
                "restaurant_category": self.category_group,
                "restaurant_subcategory": self.subcategory_group,
                "restaurant_short_desc": "builder test item",
                "restaurant_long_desc": "builder test item",
                "restaurant_base_price": 500000,
                "restaurant_branch": "DEFAULT",
            }
        )
        builder_item.insert(ignore_permissions=True)
        self._remember_cleanup_doc("Item", builder_item.item_code)
        self._set_builder_item_flags(builder_item.item_code, template.name)

        bom = frappe.get_doc(
            {
                "doctype": "BOM",
                "item": builder_item.item_code,
                "company": self.company,
                "currency": frappe.db.get_value("Company", self.company, "default_currency"),
                "conversion_rate": 1,
                "quantity": 1,
                "is_default": 1,
                "is_active": 1,
                "items": [
                    {
                        "item_code": base_component.item_code,
                        "qty": 1,
                        "uom": self.uom,
                        "rate": 0,
                    }
                ],
            }
        )
        bom.insert(ignore_permissions=True)
        bom.submit()
        self._remember_cleanup_doc("BOM", bom.name)
        frappe.db.set_value("Item", builder_item.item_code, "default_bom", bom.name, update_modified=False)
        frappe.db.commit()

        return {
            "template": template,
            "item_code": builder_item.item_code,
            "item_slug": item_slug,
            "base_component_code": base_component.item_code,
            "bom_name": bom.name,
        }

    @classmethod
    def _create_item_alternative(cls, item_code, alternative_item_code):
        item_code = (item_code or "").strip()
        alternative_item_code = (alternative_item_code or "").strip()
        if not item_code or not alternative_item_code:
            return
        if not frappe.db.exists("DocType", "Item Alternative"):
            return

        meta = frappe.get_meta("Item Alternative")
        payload = {"doctype": "Item Alternative"}

        if meta.get_field("item_code"):
            payload["item_code"] = item_code
        if meta.get_field("alternative_item"):
            payload["alternative_item"] = alternative_item_code
        elif meta.get_field("alternative_item_code"):
            payload["alternative_item_code"] = alternative_item_code
        elif meta.get_field("item_code") and not meta.get_field("parent"):
            payload["item_code"] = alternative_item_code

        if meta.get_field("parent") and meta.get_field("parenttype"):
            payload["parent"] = item_code
            payload["parenttype"] = "Item"
        if meta.get_field("parentfield"):
            payload["parentfield"] = "item_alternatives"

        doc = frappe.get_doc(payload)
        doc.insert(ignore_permissions=True)
        cls._remember_cleanup_doc("Item Alternative", doc.name)
        frappe.db.commit()

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

    def test_get_management_bom_context_payload(self):
        payload = get_management_bom_context()
        self.assertIn("companies", payload)
        self.assertIn("default_company", payload)
        self.assertIn("default_currency", payload)
        self.assertIsInstance(payload.get("companies"), list)
        self.assertTrue(payload.get("default_company"))

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

    def test_get_item_detail_includes_ingredient_alternative_options(self):
        payload = get_item_detail(self.item_slug)
        ingredient = next(row for row in payload["ingredients"] if row["key"] == "مرغ گریل")
        self.assertEqual(int(ingredient.get("is_replaceable") or 0), 1)
        alternatives = ingredient.get("alternative_options") or []
        self.assertTrue(any(row.get("alternative_item") == self.alternative_item_code for row in alternatives))

    def test_get_item_detail_resolves_alternative_price_delta_from_default_item_price(self):
        price_list = self._ensure_test_price_list(frappe.generate_hash(length=6).lower())
        set_management_product_price(
            {
                "item_name": self.raw_item_code,
                "price_list": price_list.name,
                "price_list_rate": 12000,
            }
        )
        set_management_product_price(
            {
                "item_name": self.alternative_item_code,
                "price_list": price_list.name,
                "price_list_rate": 18000,
            }
        )

        payload = get_item_detail(self.item_slug)
        ingredient = next(row for row in payload["ingredients"] if row["key"] == "مرغ گریل")
        option = next(
            (row for row in (ingredient.get("alternative_options") or []) if row.get("alternative_item") == self.alternative_item_code),
            None,
        )
        self.assertIsNotNone(option)
        self.assertEqual(option.get("price_status"), "ok")
        self.assertEqual(option.get("price_source"), "item_price")
        self.assertEqual(option.get("price_item_code"), self.alternative_item_code)
        self.assertEqual(option.get("price_list"), price_list.name)
        self.assertEqual(option.get("comparison_base_price"), 12000)
        self.assertEqual(option.get("alternative_price"), 18000)
        self.assertEqual(option.get("price_delta"), 6000)

    def test_get_related_items_returns_same_menu_context(self):
        rows = get_related_items(self.item_slug, limit=6)
        slugs = {row.get("slug") for row in rows}
        self.assertIn(self.no_bom_item_slug, slugs)
        self.assertNotIn(self.item_slug, slugs)

    def test_get_management_bom_doc_includes_alternative_summary(self):
        payload = get_management_bom_doc(self.bom_name)
        item_row = next(row for row in payload.get("items", []) if row.get("item_code") == self.raw_item_code)
        self.assertEqual(int(item_row.get("allow_alternative_item") or 0), 1)
        self.assertGreaterEqual(int(item_row.get("alternatives_count") or 0), 1)
        self.assertTrue(
            any(
                row.get("alternative_item") == self.alternative_item_code
                for row in (item_row.get("alternatives") or [])
            )
        )

    def test_get_item_detail_reads_modifier_options_from_bom_modifier_rows(self):
        price_list = self._ensure_test_price_list(frappe.generate_hash(length=6).lower())
        set_management_product_price(
            {
                "item_name": self.modifier_item_code,
                "price_list": price_list.name,
                "price_list_rate": 15000,
            }
        )
        payload = get_item_detail(self.item_slug)
        group = next(
            (row for row in payload.get("modifier_groups", []) if row.get("title") == self.modifier_group_title),
            None,
        )
        self.assertIsNotNone(group)
        self.assertTrue(any(opt.get("name") == self.modifier_item_code for opt in group.get("options", [])))

    def test_get_item_detail_keeps_single_modifier_baseline_without_linked_item(self):
        suffix = frappe.generate_hash(length=6).lower()
        price_list = self._ensure_test_price_list(suffix)
        set_management_product_price(
            {
                "item_name": self.modifier_item_code,
                "price_list": price_list.name,
                "price_list_rate": 25000,
            }
        )

        group_doc = frappe.get_doc("Restaurant Modifier Group", self.modifier_group_name)
        original_meta = {
            "selection_mode": group_doc.selection_mode,
            "required": group_doc.required,
            "min_select": group_doc.min_select,
            "max_select": group_doc.max_select,
            "sort_order": group_doc.sort_order,
            "is_active": group_doc.is_active,
        }
        original_options = [
            {
                "option_name": row.option_name,
                "action_type": row.action_type,
                "option_item": row.option_item,
                "option_uom": row.option_uom,
                "option_qty": row.option_qty,
                "price_delta": row.price_delta,
                "recipe_multiplier": row.recipe_multiplier,
                "min_qty": row.min_qty,
                "max_qty": row.max_qty,
                "qty_step": row.qty_step,
                "is_default": row.is_default,
                "sort_order": row.sort_order,
                "is_active": row.is_active,
            }
            for row in (group_doc.options or [])
        ]

        try:
            group_doc.selection_mode = "single"
            group_doc.required = 1
            group_doc.min_select = 1
            group_doc.max_select = 1
            group_doc.set(
                "options",
                [
                    {
                        "option_name": "سرد",
                        "action_type": "add_on",
                        "option_item": "",
                        "option_uom": "",
                        "option_qty": 1,
                        "price_delta": 0,
                        "recipe_multiplier": 1,
                        "min_qty": 1,
                        "max_qty": 1,
                        "qty_step": 1,
                        "is_default": 1,
                        "sort_order": 1,
                        "is_active": 1,
                    },
                    {
                        "option_name": self.modifier_item_code,
                        "action_type": "add_on",
                        "option_item": self.modifier_item_code,
                        "option_uom": self.uom,
                        "option_qty": 1,
                        "price_delta": 0,
                        "recipe_multiplier": 1,
                        "min_qty": 1,
                        "max_qty": 1,
                        "qty_step": 1,
                        "is_default": 0,
                        "sort_order": 2,
                        "is_active": 1,
                    },
                ],
            )
            group_doc.save(ignore_permissions=True)
            frappe.db.commit()

            payload = get_item_detail(self.item_slug)
            group = next(
                (row for row in payload.get("modifier_groups", []) if row.get("title") == self.modifier_group_title),
                None,
            )
            self.assertIsNotNone(group)
            baseline = next((row for row in group.get("options", []) if row.get("name") == "سرد"), None)
            self.assertIsNotNone(baseline)
            self.assertEqual(baseline.get("price_delta"), 0)
            self.assertEqual(baseline.get("price_status"), "ok")
            self.assertEqual(baseline.get("price_source"), "manual")
        finally:
            restore_doc = frappe.get_doc("Restaurant Modifier Group", self.modifier_group_name)
            for fieldname, value in original_meta.items():
                setattr(restore_doc, fieldname, value)
            restore_doc.set("options", original_options)
            restore_doc.save(ignore_permissions=True)
            frappe.db.commit()

    def test_get_item_detail_falls_back_to_latest_bom_with_modifier_rows(self):
        replacement_bom = frappe.get_doc(
            {
                "doctype": "BOM",
                "item": self.menu_item,
                "company": self.company,
                "currency": frappe.db.get_value("Company", self.company, "default_currency"),
                "conversion_rate": 1,
                "quantity": 1,
                "is_default": 1,
                "is_active": 1,
                "items": [
                    {
                        "item_code": self.raw_item_code,
                        "qty": 1,
                        "uom": self.uom,
                        "rate": 100000,
                        "restaurant_customer_label": "مرغ گریل",
                        "restaurant_is_included_by_default": 1,
                        "restaurant_can_remove": 1,
                        "restaurant_is_required": 0,
                        "restaurant_is_editable_qty": 1,
                        "allow_alternative_item": 1,
                        "restaurant_min_multiplier": 0,
                        "restaurant_max_multiplier": 3,
                        "restaurant_step_multiplier": 0.5,
                        "restaurant_extra_when_added": 0,
                    }
                ],
            }
        )
        replacement_bom.insert(ignore_permissions=True)
        replacement_bom.submit()
        self._remember_cleanup_doc("BOM", replacement_bom.name)
        frappe.db.commit()

        payload = get_item_detail(self.item_slug)
        group = next(
            (row for row in payload.get("modifier_groups", []) if row.get("title") == self.modifier_group_title),
            None,
        )
        self.assertIsNotNone(group)
        self.assertTrue(any(opt.get("name") == self.modifier_item_code for opt in group.get("options", [])))

    def test_get_item_detail_resolves_modifier_price_from_default_item_price(self):
        suffix = frappe.generate_hash(length=6).lower()
        price_list = self._ensure_test_price_list(suffix)
        set_management_product_price(
            {
                "item_name": self.modifier_item_code,
                "price_list": price_list.name,
                "price_list_rate": 22000,
            }
        )

        payload = get_item_detail(self.item_slug)
        group = next(
            (row for row in payload.get("modifier_groups", []) if row.get("title") == self.modifier_group_title),
            None,
        )
        self.assertIsNotNone(group)
        option = next((row for row in group.get("options", []) if row.get("name") == self.modifier_item_code), None)
        self.assertIsNotNone(option)
        self.assertEqual(option.get("price_delta"), 22000)
        self.assertEqual(option.get("price_status"), "ok")
        self.assertEqual(option.get("price_source"), "item_price")
        self.assertEqual(option.get("price_item_code"), self.modifier_item_code)
        self.assertEqual(option.get("price_list"), price_list.name)

    def test_get_item_detail_uses_modifier_price_delta_when_option_item_has_no_item_price(self):
        suffix = frappe.generate_hash(length=6).lower()
        price_list = self._ensure_test_price_list(suffix)
        original = self._update_primary_modifier_option(price_delta=500000)
        try:
            payload = get_item_detail(self.item_slug)
            group = next(
                (row for row in payload.get("modifier_groups", []) if row.get("title") == self.modifier_group_title),
                None,
            )
            self.assertIsNotNone(group)
            option = next((row for row in group.get("options", []) if row.get("name") == self.modifier_item_code), None)
            self.assertIsNotNone(option)
            self.assertEqual(option.get("price_delta"), 500000)
            self.assertEqual(option.get("resolved_price_delta"), 500000)
            self.assertEqual(option.get("price_status"), "ok")
            self.assertEqual(option.get("price_source"), "modifier_fallback")
            self.assertEqual(option.get("price_item_code"), self.modifier_item_code)
            self.assertEqual(option.get("price_list"), price_list.name)
        finally:
            self._restore_primary_modifier_option(original)

    def test_get_item_detail_resolves_weighted_modifier_base_price_from_default_item_price(self):
        suffix = frappe.generate_hash(length=6).lower()
        price_list = self._ensure_test_price_list(suffix)
        set_management_product_price(
            {
                "item_name": self.modifier_item_code,
                "price_list": price_list.name,
                "price_list_rate": 2200,
            }
        )

        original = self._update_primary_modifier_option(
            option_uom=self.uom,
            option_qty=15,
            min_qty=0,
            max_qty=60,
            qty_step=15,
        )
        try:
            payload = get_item_detail(self.item_slug)
            group = next(
                (row for row in payload.get("modifier_groups", []) if row.get("title") == self.modifier_group_title),
                None,
            )
            self.assertIsNotNone(group)
            option = next((row for row in group.get("options", []) if row.get("name") == self.modifier_item_code), None)
            self.assertIsNotNone(option)
            self.assertEqual(option.get("option_qty"), 15)
            self.assertEqual(option.get("qty_step"), 15)
            self.assertEqual(option.get("min_qty"), 0)
            self.assertEqual(option.get("max_qty"), 60)
            self.assertEqual(option.get("stock_uom"), self.uom)
            self.assertEqual(option.get("option_uom"), self.uom)
            self.assertEqual(option.get("unit_rate"), 2200)
            self.assertEqual(option.get("conversion_factor"), 1)
            self.assertEqual(option.get("base_price"), 33000)
            self.assertEqual(option.get("price_delta"), 33000)
        finally:
            self._restore_primary_modifier_option(original)

    def test_get_item_detail_omits_disabled_modifier_option_items(self):
        modifier_doc = frappe.get_doc("Item", self.modifier_item_code)
        try:
            modifier_doc.disabled = 1
            modifier_doc.save(ignore_permissions=True)
            frappe.db.commit()

            payload = get_item_detail(self.item_slug)
            group = next(
                (row for row in payload.get("modifier_groups", []) if row.get("title") == self.modifier_group_title),
                None,
            )
            self.assertIsNone(group)
        finally:
            frappe.db.set_value("Item", self.modifier_item_code, "disabled", 0, update_modified=False)
            frappe.db.commit()

    def test_management_modifier_context_excludes_disabled_option_items(self):
        modifier_doc = frappe.get_doc("Item", self.modifier_item_code)
        try:
            modifier_doc.disabled = 1
            modifier_doc.save(ignore_permissions=True)
            frappe.db.commit()

            context = get_management_modifier_groups_context()
            item_values = [row.get("value") for row in context.get("item_options", [])]
            self.assertNotIn(self.modifier_item_code, item_values)
        finally:
            frappe.db.set_value("Item", self.modifier_item_code, "disabled", 0, update_modified=False)
            frappe.db.commit()

    def test_get_item_detail_hides_modifier_option_when_default_price_is_missing(self):
        suffix = frappe.generate_hash(length=6).lower()
        price_list = self._ensure_test_price_list(suffix)

        item_price_name = frappe.db.get_value(
            "Item Price",
            {"item_code": self.modifier_item_code, "price_list": price_list.name},
            "name",
        )
        if item_price_name:
            frappe.delete_doc("Item Price", item_price_name, force=1, ignore_permissions=True)
            frappe.db.commit()

        payload = get_item_detail(self.item_slug)
        group = next(
            (row for row in payload.get("modifier_groups", []) if row.get("title") == self.modifier_group_title),
            None,
        )
        self.assertIsNone(group)

    def test_place_order_rejects_modifier_when_default_price_is_missing(self):
        suffix = frappe.generate_hash(length=6).lower()
        price_list = self._ensure_test_price_list(suffix)

        item_price_name = frappe.db.get_value(
            "Item Price",
            {"item_code": self.modifier_item_code, "price_list": price_list.name},
            "name",
        )
        if item_price_name:
            frappe.delete_doc("Item Price", item_price_name, force=1, ignore_permissions=True)
            frappe.db.commit()

        broken = self._valid_order_items()
        broken[0]["customization"]["selected_modifiers"] = [
            {
                "group": self.modifier_group_title,
                "option": self.modifier_item_code,
                "qty": 1,
            }
        ]

        with self.assertRaises(frappe.ValidationError):
            place_order(
                customer_info={"name": "مودیفایر بدون قیمت", "mobile": "09124445555"},
                order_type="takeaway",
                items=broken,
            )

    def test_get_item_detail_hides_modifier_option_when_uom_conversion_is_missing(self):
        suffix = frappe.generate_hash(length=6).lower()
        price_list = self._ensure_test_price_list(suffix)
        missing_uom = self._ensure_uom(f"Missing Modifier UOM {suffix}")
        set_management_product_price(
            {
                "item_name": self.modifier_item_code,
                "price_list": price_list.name,
                "price_list_rate": 2200,
            }
        )
        original = self._update_primary_modifier_option(
            option_uom=missing_uom,
            option_qty=15,
            min_qty=0,
            max_qty=60,
            qty_step=15,
        )
        try:
            payload = get_item_detail(self.item_slug)
            group = next(
                (row for row in payload.get("modifier_groups", []) if row.get("title") == self.modifier_group_title),
                None,
            )
            self.assertIsNone(group)

            detail = get_management_modifier_group_detail(self.modifier_group_name)
            self.assertEqual(detail["options"][0].get("price_status"), "missing_conversion")
        finally:
            self._restore_primary_modifier_option(original)

    def test_recalculate_line_uses_actual_modifier_qty_for_pricing(self):
        suffix = frappe.generate_hash(length=6).lower()
        price_list = self._ensure_test_price_list(suffix)
        set_management_product_price(
            {
                "item_name": self.modifier_item_code,
                "price_list": price_list.name,
                "price_list_rate": 2200,
            }
        )
        original = self._update_primary_modifier_option(
            option_uom=self.uom,
            option_qty=15,
            min_qty=0,
            max_qty=60,
            qty_step=15,
        )
        try:
            menu_doc = frappe.get_doc("Item", self.menu_item)
            line_calc = _recalculate_line(
                menu_doc,
                1,
                {
                    "ingredient_adjustments": [],
                    "selected_modifiers": [
                        {
                            "group": self.modifier_group_title,
                            "option": self.modifier_item_code,
                            "qty": 30,
                        }
                    ],
                },
                branch_markup_percent=0,
            )
            self.assertEqual(line_calc["pricing_breakdown"]["modifier_delta_total"], 66000)
            self.assertEqual(line_calc["normalized_customization"]["selected_modifiers"][0]["qty"], 30)
            modifier_component = next(
                row for row in line_calc["ingredient_components"] if row.get("source_type") == "modifier_add_on"
            )
            self.assertEqual(modifier_component.get("selected_base_qty"), 30)
            self.assertEqual(modifier_component.get("selected_multiplier"), 1)
        finally:
            self._restore_primary_modifier_option(original)

    def test_recalculate_line_uses_default_item_price_for_ingredient_alternative_delta(self):
        price_list = self._ensure_test_price_list(frappe.generate_hash(length=6).lower())
        set_management_product_price(
            {
                "item_name": self.raw_item_code,
                "price_list": price_list.name,
                "price_list_rate": 12000,
            }
        )
        set_management_product_price(
            {
                "item_name": self.alternative_item_code,
                "price_list": price_list.name,
                "price_list_rate": 18000,
            }
        )

        menu_doc = frappe.get_doc("Item", self.menu_item)
        line_calc = _recalculate_line(
            menu_doc,
            1,
            {
                "ingredient_adjustments": [],
                "selected_alternatives": [
                    {
                        "ingredient_key": "مرغ گریل",
                        "alternative_item": self.alternative_item_code,
                    }
                ],
                "selected_modifiers": [],
            },
            branch_markup_percent=0,
        )
        self.assertEqual(line_calc["pricing_breakdown"]["ingredient_delta_total"], 6000)
        self.assertEqual(line_calc["unit_price"], 506000)
        self.assertEqual(
            line_calc["normalized_customization"]["selected_alternatives"][0]["alternative_item"],
            self.alternative_item_code,
        )

    def test_recalculate_line_uses_default_item_price_for_ingredient_quantity_delta(self):
        price_list = self._ensure_test_price_list(frappe.generate_hash(length=6).lower())
        set_management_product_price(
            {
                "item_name": self.raw_item_code,
                "price_list": price_list.name,
                "price_list_rate": 12000,
            }
        )

        menu_doc = frappe.get_doc("Item", self.menu_item)

        increased_line = _recalculate_line(
            menu_doc,
            1,
            {
                "ingredient_adjustments": [
                    {
                        "ingredient_key": "مرغ گریل",
                        "multiplier": 2,
                    }
                ],
                "selected_modifiers": [],
            },
            branch_markup_percent=0,
        )
        self.assertEqual(increased_line["pricing_breakdown"]["ingredient_delta_total"], 12000)
        self.assertEqual(increased_line["unit_price"], 512000)

        removed_line = _recalculate_line(
            menu_doc,
            1,
            {
                "ingredient_adjustments": [
                    {
                        "ingredient_key": "مرغ گریل",
                        "multiplier": 0,
                    }
                ],
                "selected_modifiers": [],
            },
            branch_markup_percent=0,
        )
        self.assertEqual(removed_line["pricing_breakdown"]["ingredient_delta_total"], -12000)
        self.assertEqual(removed_line["unit_price"], 488000)

    def test_get_item_detail_includes_item_price_metadata_for_ingredients(self):
        price_list = self._ensure_test_price_list(frappe.generate_hash(length=6).lower())
        set_management_product_price(
            {
                "item_name": self.raw_item_code,
                "price_list": price_list.name,
                "price_list_rate": 12000,
            }
        )

        payload = get_item_detail(self.item_slug)
        ingredient = next(row for row in payload["ingredients"] if row["key"] == "مرغ گریل")
        self.assertEqual(ingredient.get("price_source"), "item_price")
        self.assertEqual(float(ingredient.get("unit_rate") or 0), 12000.0)
        self.assertEqual(float(ingredient.get("base_price") or 0), 12000.0)
        self.assertEqual(ingredient.get("price_status"), "ok")
        self.assertEqual(ingredient.get("price_item_code"), self.raw_item_code)

    def test_build_ticket_components_puts_weighted_modifier_qty_into_qty_map(self):
        suffix = frappe.generate_hash(length=6).lower()
        price_list = self._ensure_test_price_list(suffix)
        set_management_product_price(
            {
                "item_name": self.modifier_item_code,
                "price_list": price_list.name,
                "price_list_rate": 2200,
            }
        )
        original = self._update_primary_modifier_option(
            option_uom=self.uom,
            option_qty=15,
            min_qty=0,
            max_qty=60,
            qty_step=15,
        )
        try:
            menu_doc = frappe.get_doc("Item", self.menu_item)
            bom_doc = frappe.get_doc("BOM", self.bom_name)
            line_calc = _recalculate_line(
                menu_doc,
                1,
                {
                    "ingredient_adjustments": [],
                    "selected_modifiers": [
                        {
                            "group": self.modifier_group_title,
                            "option": self.modifier_item_code,
                            "qty": 45,
                        }
                    ],
                },
                branch_markup_percent=0,
            )
            _components, qty_map = _build_ticket_components(
                menu_doc,
                bom_doc,
                line_calc,
                1,
                1,
                self.warehouse,
            )
            self.assertEqual(float(qty_map.get(self.modifier_item_code) or 0), 45.0)
        finally:
            self._restore_primary_modifier_option(original)

    def test_build_ticket_components_expands_modifier_item_bom_components(self):
        suffix = frappe.generate_hash(length=6).lower()
        component_item = frappe.get_doc(
            {
                "doctype": "Item",
                "item_code": f"MOD_RAW_{suffix.upper()}",
                "item_name": f"Modifier Raw {suffix}",
                "item_group": self.category_group,
                "stock_uom": self.uom,
                "is_stock_item": 1,
                "is_sales_item": 0,
                "is_purchase_item": 1,
            }
        )
        component_item.insert(ignore_permissions=True)
        self._remember_cleanup_doc("Item", component_item.item_code)

        modifier_bom = frappe.get_doc(
            {
                "doctype": "BOM",
                "item": self.modifier_item_code,
                "company": self.company,
                "currency": frappe.db.get_value("Company", self.company, "default_currency"),
                "conversion_rate": 1,
                "quantity": 1,
                "is_default": 1,
                "is_active": 1,
                "items": [
                    {
                        "item_code": component_item.item_code,
                        "qty": 2,
                        "uom": self.uom,
                        "rate": 1000,
                    }
                ],
            }
        )
        modifier_bom.insert(ignore_permissions=True)
        modifier_bom.submit()
        self._remember_cleanup_doc("BOM", modifier_bom.name)
        frappe.db.commit()

        suffix = frappe.generate_hash(length=6).lower()
        price_list = self._ensure_test_price_list(suffix)
        set_management_product_price(
            {
                "item_name": self.modifier_item_code,
                "price_list": price_list.name,
                "price_list_rate": 22000,
            }
        )

        menu_doc = frappe.get_doc("Item", self.menu_item)
        bom_doc = frappe.get_doc("BOM", self.bom_name)
        line_calc = _recalculate_line(
            menu_doc,
            1,
            {
                "ingredient_adjustments": [],
                "selected_modifiers": [
                    {
                        "group": self.modifier_group_title,
                        "option": self.modifier_item_code,
                        "qty": 1,
                    }
                ],
            },
            branch_markup_percent=0,
        )

        components, qty_map = _build_ticket_components(
            menu_doc,
            bom_doc,
            line_calc,
            1,
            1,
            self.warehouse,
        )
        self.assertEqual(float(qty_map.get(component_item.item_code) or 0), 2.0)
        self.assertNotIn(self.modifier_item_code, qty_map)
        self.assertTrue(
            any(
                row.get("item_code") == component_item.item_code
                and row.get("source_type") == "modifier_bom_item"
                for row in (components or [])
            )
        )

    def test_extract_qty_map_and_work_order_sync_skip_non_stock_components(self):
        ticket_doc = frappe._dict(
            {
                "qty": 1,
                "components": [
                    {
                        "item_code": self.modifier_item_code,
                        "final_qty": 30,
                    },
                    {
                        "item_code": self.service_modifier_item_code,
                        "final_qty": 10,
                    },
                ],
            }
        )
        qty_map = _extract_qty_map_from_ticket(ticket_doc, target_qty=1)
        self.assertEqual(float(qty_map.get(self.modifier_item_code) or 0), 30.0)
        self.assertNotIn(self.service_modifier_item_code, qty_map)

        work_order = frappe.get_doc(
            {
                "doctype": "Work Order",
                "production_item": self.menu_item,
                "bom_no": self.bom_name,
                "company": self.company,
                "qty": 1,
                "source_warehouse": self.warehouse,
                "wip_warehouse": self.warehouse,
                "fg_warehouse": self.warehouse,
                "use_multi_level_bom": 0,
                "skip_transfer": 1,
            }
        ).insert(ignore_permissions=True)
        self._remember_cleanup_doc("Work Order", work_order.name)

        _sync_work_order_required_items(work_order.name, qty_map=qty_map, source_warehouse=self.warehouse)
        required_codes = set(
            frappe.get_all(
                "Work Order Item",
                filters={"parent": work_order.name, "parentfield": "required_items"},
                pluck="item_code",
                ignore_permissions=True,
            )
        )
        self.assertIn(self.modifier_item_code, required_codes)
        self.assertNotIn(self.service_modifier_item_code, required_codes)

    def test_management_modifier_group_save_and_detail(self):
        suffix = frappe.generate_hash(length=6).lower()
        price_list = self._ensure_test_price_list(suffix)
        set_management_product_price(
            {
                "item_name": self.modifier_item_code,
                "price_list": price_list.name,
                "price_list_rate": 18000,
            }
        )
        context = get_management_modifier_groups_context()
        self.assertEqual(context.get("default_price_list"), price_list.name)

        saved = save_management_modifier_group(
            {
                "title": f"Modifier Group {suffix}",
                "selection_mode": "multi",
                "required": 0,
                "min_select": 0,
                "max_select": 3,
                "description": "test group",
                "sort_order": 4,
                "is_active": 1,
                "options": [
                    {
                        "option_name": f"Option {suffix}",
                        "action_type": "add_on",
                        "option_item": self.modifier_item_code,
                        "option_qty": 1,
                        "recipe_multiplier": 1,
                        "is_default": 0,
                        "is_active": 1,
                        "sort_order": 1,
                    }
                ],
            }
        )
        self.assertTrue(saved.get("name"))

        detail = get_management_modifier_group_detail(saved.get("name"))
        self.assertEqual(detail.get("title"), f"Modifier Group {suffix}")
        self.assertEqual(detail.get("default_price_list"), price_list.name)
        self.assertEqual(len(detail.get("options") or []), 1)
        self.assertEqual(detail["options"][0].get("option_item"), self.modifier_item_code)

    def test_modifier_context_prefers_selling_settings_price_list(self):
        primary_suffix = frappe.generate_hash(length=6).lower()
        fallback_suffix = frappe.generate_hash(length=6).lower()
        primary_price_list = self._ensure_test_price_list(primary_suffix)
        fallback_price_list = self._ensure_test_price_list(fallback_suffix)

        if frappe.db.exists("DocType", "Selling Settings"):
            original_setting = frappe.db.get_single_value("Selling Settings", "selling_price_list") or ""
        else:
            self.skipTest("Selling Settings is not installed.")

        try:
            frappe.db.set_single_value("Selling Settings", "selling_price_list", primary_price_list.name)
            if frappe.db.has_column("Price List", "restaurant_is_default_selling"):
                frappe.db.sql(
                    "update `tabPrice List` set restaurant_is_default_selling = 0 where selling = 1"
                )
                frappe.db.set_value(
                    "Price List",
                    fallback_price_list.name,
                    "restaurant_is_default_selling",
                    1,
                    update_modified=False,
                )
            frappe.db.commit()

            payload = get_management_modifier_groups_context()
            self.assertEqual(payload.get("default_price_list"), primary_price_list.name)
        finally:
            frappe.db.set_single_value("Selling Settings", "selling_price_list", original_setting)
            frappe.db.commit()

    def test_set_management_default_price_list_updates_selling_settings(self):
        if not frappe.db.exists("DocType", "Selling Settings"):
            self.skipTest("Selling Settings is not installed.")

        price_list = self._ensure_test_price_list(frappe.generate_hash(length=6).lower())
        original_setting = frappe.db.get_single_value("Selling Settings", "selling_price_list") or ""

        try:
            payload = set_management_default_price_list(price_list.name)
            self.assertEqual(payload.get("default_price_list"), price_list.name)
            self.assertEqual(
                frappe.db.get_single_value("Selling Settings", "selling_price_list"),
                price_list.name,
            )
        finally:
            frappe.db.set_single_value("Selling Settings", "selling_price_list", original_setting)
            frappe.db.commit()

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

    def test_update_management_product_settings_normalizes_builder_option_nutrition_json(self):
        if not frappe.db.exists("DocType", "Product Builder Template"):
            self.skipTest("Product Builder Template is not installed.")

        updated = update_management_product_settings(
            {
                "item_name": self.menu_item,
                "restaurant_is_customizable": 1,
                "restaurant_builder_active": 1,
                "product_builder_config": {
                    "title": f"Builder {frappe.generate_hash(length=6).lower()}",
                    "steps": [
                        {
                            "step_title": "Milk",
                            "step_key": "milk-step",
                            "selection_mode": "single",
                            "min_select": 1,
                            "max_select": 1,
                            "is_required": 1,
                            "show_step_price": 1,
                            "options": [
                                {
                                    "option_key": "skim",
                                    "option_label": "Skim Milk",
                                    "base_price_delta": 0,
                                    "price_type": "fixed",
                                    "price_percentage": 0,
                                    "is_default": 1,
                                    "is_available": 1,
                                    "max_qty": 1,
                                    "nutrition": {"kcal": 12, "protein_g": 1},
                                }
                            ],
                        }
                    ],
                },
            }
        )
        template_name = (updated.get("item", {}) or {}).get("restaurant_builder_template")
        self.assertTrue(template_name)
        option_rows = frappe.get_all(
            "Product Builder Option",
            filters={"parenttype": "Product Builder Step"},
            fields=["nutrition_json"],
            ignore_permissions=True,
        )
        self.assertTrue(any((row.get("nutrition_json") or "").strip() for row in option_rows))

    def test_update_management_product_settings_skips_builder_save_when_config_unchanged(self):
        if not frappe.db.exists("DocType", "Product Builder Template"):
            self.skipTest("Product Builder Template is not installed.")

        builder_payload = {
            "title": f"Builder Stable {frappe.generate_hash(length=6).lower()}",
            "steps": [
                {
                    "step_title": "Milk",
                    "step_key": "milk-step",
                    "selection_mode": "single",
                    "min_select": 1,
                    "max_select": 1,
                    "is_required": 1,
                    "show_step_price": 1,
                    "options": [
                        {
                            "option_key": "skim",
                            "option_label": "Skim Milk",
                            "base_price_delta": 0,
                            "price_type": "fixed",
                            "price_percentage": 0,
                            "is_default": 1,
                            "is_available": 1,
                            "max_qty": 1,
                            "nutrition": {"kcal": 12},
                        }
                    ],
                }
            ],
        }
        update_management_product_settings(
            {
                "item_name": self.menu_item,
                "restaurant_is_customizable": 1,
                "restaurant_builder_active": 1,
                "product_builder_config": builder_payload,
            }
        )

        with patch("restaurant.api._build_item_specific_builder_template", side_effect=AssertionError("builder save should be skipped")):
            updated = update_management_product_settings(
                {
                    "item_name": self.menu_item,
                    "description": "updated without builder change",
                    "restaurant_is_customizable": 1,
                    "product_builder_config": builder_payload,
                }
            )

        self.assertEqual(updated["item"]["description"], "updated without builder change")

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

    def test_get_builder_template_resolves_portion_pricing_from_default_price_list(self):
        suffix = frappe.generate_hash(length=6).lower()
        fixture = self._make_builder_product_fixture(suffix)
        price_list = self._ensure_test_price_list(suffix)
        set_management_product_price(
            {"item_name": self.raw_item_code, "price_list": price_list.name, "price_list_rate": 1000}
        )
        set_management_product_price(
            {"item_name": self.alternative_item_code, "price_list": price_list.name, "price_list_rate": 2000}
        )
        set_management_product_price(
            {
                "item_name": self.service_modifier_item_code,
                "price_list": price_list.name,
                "price_list_rate": 15000,
            }
        )

        payload = get_builder_template(item_code=fixture["item_code"])
        self.assertEqual(payload.get("status"), "success")
        template = payload["data"]["template"]
        protein_step = next(row for row in template["steps"] if row["step_key"] == "protein")
        chicken = next(row for row in protein_step["options"] if row["option_key"] == "chicken")
        shrimp = next(row for row in protein_step["options"] if row["option_key"] == "shrimp")

        self.assertEqual(chicken.get("price_source"), "item_price")
        self.assertEqual(chicken.get("price_status"), "ok")
        self.assertEqual(chicken.get("portion_qty"), 120)
        self.assertEqual(chicken.get("portion_uom"), self.uom)
        self.assertEqual(chicken.get("price_delta"), 120000)
        self.assertEqual(chicken.get("resolved_price_delta"), 120000)
        self.assertEqual(chicken.get("unit_rate"), 1000)
        self.assertEqual(chicken.get("price_list"), price_list.name)
        self.assertEqual(shrimp.get("price_delta"), 240000)

    def test_compute_builder_price_enforces_stage_portion_capacity_and_persists_rows(self):
        suffix = frappe.generate_hash(length=6).lower()
        fixture = self._make_builder_product_fixture(suffix)
        price_list = self._ensure_test_price_list(suffix)
        set_management_product_price(
            {"item_name": self.raw_item_code, "price_list": price_list.name, "price_list_rate": 1000}
        )
        set_management_product_price(
            {"item_name": self.alternative_item_code, "price_list": price_list.name, "price_list_rate": 2000}
        )

        payload = compute_builder_price(
            fixture["item_code"],
            [
                {"step_key": "protein", "option_key": "chicken", "qty": 2},
                {"step_key": "protein", "option_key": "shrimp", "qty": 1},
            ],
        )
        self.assertEqual(payload.get("status"), "success")
        data = payload["data"]
        self.assertEqual(data.get("base_price"), 500000)
        self.assertEqual(data.get("options_total"), 480000)
        self.assertEqual(data.get("final_price"), 980000)
        self.assertEqual(len(data.get("builder_portion_rows") or []), 2)
        first_row = data["builder_portion_rows"][0]
        self.assertEqual(first_row.get("portion_count"), 2)
        self.assertEqual(first_row.get("resolved_stock_qty"), 240)
        self.assertEqual(first_row.get("total_price"), 240000)

        invalid_payload = compute_builder_price(
            fixture["item_code"],
            [
                {"step_key": "protein", "option_key": "chicken", "qty": 2},
                {"step_key": "protein", "option_key": "shrimp", "qty": 2},
            ],
        )
        self.assertEqual(invalid_payload.get("status"), "error")
        self.assertIn("maximum", (invalid_payload.get("error") or {}).get("message", "").lower())

        saved = save_builder_selection(
            template=fixture["template"].name,
            item=fixture["item_code"],
            base_price=500000,
            selections=[
                {"step_key": "protein", "option_key": "chicken", "qty": 2},
                {"step_key": "protein", "option_key": "shrimp", "qty": 1},
            ],
        )
        self.assertEqual(saved.get("status"), "success")
        selection_doc = frappe.get_doc("Product Builder Selection", saved["data"]["selection_id"])
        self.assertEqual(int(selection_doc.options_total or 0), 480000)
        first = selection_doc.selections[0]
        self.assertEqual(flt(first.get("portion_count") or 0), 2)
        self.assertEqual(flt(first.get("portion_qty") or 0), 120)
        self.assertEqual(flt(first.get("resolved_stock_qty") or 0), 240)
        self.assertEqual(flt(first.get("total_price") or 0), 240000)

    def test_builder_selection_components_join_base_bom_and_skip_non_stock_deduction(self):
        suffix = frappe.generate_hash(length=6).lower()
        fixture = self._make_builder_product_fixture(suffix)
        price_list = self._ensure_test_price_list(suffix)
        set_management_product_price(
            {"item_name": self.raw_item_code, "price_list": price_list.name, "price_list_rate": 1000}
        )
        set_management_product_price(
            {
                "item_name": self.service_modifier_item_code,
                "price_list": price_list.name,
                "price_list_rate": 15000,
            }
        )

        custom_item = frappe.get_doc("Item", fixture["item_code"])
        line_calc = _recalculate_line(
            custom_item,
            1,
            {
                "builder_selection": {
                    "template": fixture["template"].name,
                    "selections": [
                        {"step_key": "protein", "option_key": "chicken", "qty": 2},
                        {"step_key": "service_addon", "option_key": "service_sauce", "qty": 1},
                    ],
                }
            },
        )
        bom_doc = frappe.get_doc("BOM", fixture["bom_name"])
        components, qty_map = _build_ticket_components(
            custom_item,
            bom_doc,
            line_calc,
            1,
            1,
            self.warehouse,
        )

        self.assertTrue(any(row.get("item_code") == fixture["base_component_code"] for row in components))
        self.assertTrue(any(row.get("item_code") == self.raw_item_code for row in components))
        self.assertTrue(any(row.get("item_code") == self.service_modifier_item_code for row in components))
        self.assertIn(fixture["base_component_code"], qty_map)
        self.assertIn(self.raw_item_code, qty_map)
        self.assertNotIn(self.service_modifier_item_code, qty_map)
