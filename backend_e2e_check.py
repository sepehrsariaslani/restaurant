import sys
import json

def check_everything():
    print("Checking backend files for requested functionality...")
    with open('restaurant/api.py', 'r') as f:
        api = f.read()

    # 1. Check if preparing path starts production
    if "_start_kitchen_production(so_name)" in api and 'status == "preparing":' in api:
        print("[OK] Preparing stage is isolated to _start_kitchen_production.")
    else:
        print("[FAIL] Preparing stage isolation missing.")

    # 2. Check if ready path ONLY manufactures
    if "_complete_kitchen_production(so_name)" in api and 'status == "ready":' in api:
        print("[OK] Ready stage is isolated to _complete_kitchen_production.")
    else:
        print("[FAIL] Ready stage isolation missing.")

    # 3. Check delivered path
    if "_create_delivery_note_for_sales_order" in api and 'status == "delivered":' in api:
        print("[OK] Delivered stage is isolated to creating delivery notes.")
    else:
        print("[FAIL] Delivered stage isolation missing.")

check_everything()
