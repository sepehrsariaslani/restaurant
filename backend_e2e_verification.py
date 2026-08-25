import sys
import re

with open('restaurant/api.py', 'r') as f:
    api = f.read()

def verify_stage(status, expected_function):
    if expected_function in api and f'status == "{status}"' in api:
        print(f"[PASSED] Stage '{status}' correctly triggers {expected_function}")
    else:
        print(f"[FAILED] Stage '{status}' logic is incorrect or missing {expected_function}")

verify_stage("preparing", "_start_kitchen_production(so_name)")
verify_stage("ready", "_complete_kitchen_production(so_name)")
verify_stage("delivered", "_create_delivery_note_for_sales_order(so_name, submit_doc=True)")

