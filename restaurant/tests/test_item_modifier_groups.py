"""Direct Item modifier links share the normal Restaurant group resolver."""

import json
from unittest import TestCase, defaultTestLoader
from unittest.mock import Mock, patch

import frappe
from restaurant import api, snapp_sync


class TestItemModifierGroups(TestCase):
    def build(self, bom_rows=None, item_rows=None):
        item = frappe._dict(doctype="Item", name="BOWL", restaurant_modifier_groups=item_rows or [])
        group = frappe._dict(title="لوازم سرو", selection_mode="single", required=0, min_select=0, max_select=1,
            options=[frappe._dict(option_name="قاشق و چنگال", action_type="add_on", option_item="CUTLERY", option_qty=1, is_active=1)])
        bom = frappe._dict(restaurant_modifier_rows=bom_rows or []) if bom_rows else None
        with (
            patch.object(api, "_get_bom_doc", return_value=None),
            patch.object(api, "_get_modifier_source_bom_doc", return_value=bom),
            patch.object(frappe.db, "exists", side_effect=lambda dt, name: dt == "Restaurant Modifier Group"),
            patch.object(frappe, "get_doc", return_value=group),
            patch.object(api, "_resolve_modifier_option_pricing", return_value={"price_status": "ok", "unit_rate": 150000, "price_delta": 150000}),
        ):
            return api._build_modifier_groups(item)

    def test_item_without_a_bom_resolves_its_optional_group(self):
        groups, _, _ = self.build(item_rows=[frappe._dict(modifier_group="CUTLERY-GROUP")])
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0]["required"], 0)
        self.assertEqual(groups[0]["max_select"], 1)
        self.assertEqual(groups[0]["options"][0]["name"], "قاشق و چنگال")
        self.assertEqual(groups[0]["options"][0]["price_delta"], 150000)

    def test_same_group_in_bom_and_item_has_one_set_of_options(self):
        link = frappe._dict(modifier_group="CUTLERY-GROUP")
        groups, _, _ = self.build(bom_rows=[link], item_rows=[link])
        self.assertEqual(len(groups), 1)
        self.assertEqual(len(groups[0]["options"]), 1)

    def test_bom_groups_are_preserved_alongside_direct_item_groups(self):
        groups, _, _ = self.build(bom_rows=[frappe._dict(modifier_group="RICE")], item_rows=[frappe._dict(modifier_group="CUTLERY")])
        self.assertEqual({group["group_name"] for group in groups}, {"RICE", "CUTLERY"})

    def test_existing_direct_link_is_idempotent_and_does_not_save(self):
        item = Mock()
        item.meta.has_field.return_value = True
        item.get.side_effect = lambda field: [{"modifier_group": "CUTLERY"}] if field == "restaurant_modifier_groups" else None
        group = frappe._dict(is_active=1, options=[frappe._dict(is_active=1)])
        with (
            patch.object(api, "_ensure_management_access") as access,
            patch.object(frappe.db, "exists", return_value=True),
            patch.object(frappe, "get_doc", side_effect=[item, group]),
            patch.object(api, "_build_modifier_groups", return_value=([], {}, {})),
        ):
            result = api.add_management_modifier_group_to_item("BOWL", "CUTLERY")
        self.assertEqual(result["status"], "already_linked")
        access.assert_called_once()
        item.save.assert_not_called()

    def test_new_item_link_saves_only_a_native_item_child_row(self):
        item = Mock()
        item.meta.has_field.return_value = True
        item.get.return_value = []
        group = frappe._dict(is_active=1, required=0, min_select=0, max_select=1, options=[frappe._dict(is_active=1)])
        with (
            patch.object(api, "_ensure_management_access"),
            patch.object(frappe.db, "exists", return_value=True),
            patch.object(frappe, "get_doc", side_effect=[item, group]),
            patch.object(api, "_build_modifier_groups", return_value=([], {}, {})),
            patch.object(frappe.db, "commit") as commit,
            patch.object(frappe, "clear_cache"),
        ):
            result = api.add_management_modifier_group_to_item("BOWL", "CUTLERY")
        self.assertEqual(result["status"], "linked")
        self.assertEqual(item.append.call_args.args[0], "restaurant_modifier_groups")
        self.assertEqual(item.append.call_args.args[1]["modifier_group"], "CUTLERY")
        self.assertEqual(item.append.call_args.args[1]["required"], 0)
        item.save.assert_called_once_with(ignore_permissions=True)
        commit.assert_called_once()

    def test_shared_topping_mapping_does_not_remove_another_base_item(self):
        self.check_mapping("topping_id", preserve_other=True)

    def test_exclusive_variation_mapping_still_moves_to_one_base_item(self):
        self.check_mapping("variation_id", preserve_other=False)

    def test_product_group_mapping_wins_over_an_old_variation_alias(self):
        parent = {"name": "BOWL", "restaurant_external_product_id": "product-1", "restaurant_external_menu_item_id": "product-1", "restaurant_external_variation_id": ""}
        alias = {"name": "OLD-MEXICAN-BOWL", "restaurant_external_menu_item_id": "variation-2"}
        row = {"product_id": "product-1", "variation_id": "variation-2", "external_id": "variation-2"}
        self.assertIs(snapp_sync._find_mapped_local_item(row, [parent, alias]), parent)

    def test_ambiguous_parent_group_mapping_is_never_guessed(self):
        parent = {"name": "BOWL", "restaurant_external_product_id": "product-1", "restaurant_external_menu_item_id": "product-1"}
        other = {**parent, "name": "OTHER-BOWL"}
        self.assertIsNone(snapp_sync._find_mapped_local_item({"product_id": "product-1"}, [parent, other]))

    def check_mapping(self, field, preserve_other):
        fieldname = snapp_sync.FOOD_PARTNER_MODIFIER_MAPPINGS_FIELD
        old_mapping = {"lookup_field": field, "lookup_value": "9001", "parent_item": "OTHER"}
        context = {"groups": [{"name": "CUTLERY", "options": [{"name": "SPOON", "label": "قاشق و چنگال"}]}]}
        with (
            patch.object(snapp_sync, "_has_field", return_value=True),
            patch.object(snapp_sync, "get_snappfood_modifier_groups", return_value=context),
            patch.object(frappe.db, "exists", return_value=True),
            patch.object(frappe, "get_all", return_value=[{"name": "OTHER", fieldname: json.dumps([old_mapping])}, {"name": "BOWL", fieldname: "[]"}]),
            patch.object(frappe.db, "set_value") as write,
            patch.object(frappe.db, "commit"),
        ):
            snapp_sync.save_snappfood_modifier_mapping(parent_item="BOWL", group_name="CUTLERY", option_name="SPOON", **{field: "9001"})
        others = [call for call in write.call_args_list if call.args[1] == "OTHER"]
        self.assertEqual(bool(others), not preserve_other)
        target = json.loads(write.call_args.args[3])
        self.assertEqual(target[0]["parent_item"], "BOWL")


def run_item_modifier_group_contract_check():
    names = defaultTestLoader.getTestCaseNames(TestItemModifierGroups)
    for name in names:
        case = TestItemModifierGroups(name)
        getattr(case, name)()
    return {"status": "success", "count": len(names)}
