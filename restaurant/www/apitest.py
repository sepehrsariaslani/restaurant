import json
from pathlib import Path

from restaurant.snapp_sync import fetch_snapp_orders


OUTPUT_FILE = Path(__file__).resolve().parent / "snapp_orders.json"


def export_orders_to_json():
    payload = fetch_snapp_orders()
    with open(OUTPUT_FILE, "w", encoding="utf-8") as json_file:
        json.dump(payload, json_file, ensure_ascii=False, indent=4)
    return {
        "output_file": str(OUTPUT_FILE),
        "orders_count": payload.get("orders_count", 0),
        "pages_fetched": payload.get("pages_fetched", 0),
    }


if __name__ == "__main__":
    result = export_orders_to_json()
    print(
        "Saved {orders_count} orders from {pages_fetched} page(s) into {output_file}".format(
            **result,
        )
    )
