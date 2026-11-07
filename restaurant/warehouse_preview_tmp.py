from collections import Counter
from restaurant.api_warehouse_recovery import _build_snapshot
import frappe


def run():
    preview = _build_snapshot("DEFAULT")
    groups = {}
    for row in preview["blockers"]:
        key = (row.get("doctype") or "نامشخص", str(row.get("reason") or "بدون شرح"))
        group = groups.setdefault(key, {"doctype": key[0], "reason": key[1][:180], "count": 0, "samples": []})
        group["count"] += 1
        if len(group["samples"]) < 3 and row.get("name"):
            group["samples"].append(row["name"])
    return {
        "summary": preview["summary"],
        "stock_document_types": dict(Counter(row["doctype"] for row in preview["vouchers"])),
        "configuration_actions": dict(Counter(row["action"] for row in preview["configuration_rows"])),
        "blocker_groups": sorted(groups.values(), key=lambda row: (-row["count"], row["doctype"], row["reason"])),
        "item_samples": [{"name": row["name"], "orders": row.get("pending_sales_order_count"), "boms": row.get("submitted_bom_count"), "references": row.get("references")} for row in preview["item_classification"][:3]],
    }


def run_settings():
    return {
        "production_settings": frappe.get_all(
            "Restaurant Branch Production Settings",
            fields=["branch", "company", "raw_warehouse", "kitchen_wip_warehouse", "finished_goods_warehouse", "is_active"],
            order_by="branch asc",
            ignore_permissions=True,
        ),
        "stock_settings_default_warehouse": frappe.db.get_single_value("Stock Settings", "default_warehouse"),
        "allow_negative_stock": frappe.db.get_single_value("Stock Settings", "allow_negative_stock"),
        "restaurant_default_warehouse": frappe.db.get_single_value("Restaurant Web Settings", "restaurant_inventory_default_warehouse"),
    }
