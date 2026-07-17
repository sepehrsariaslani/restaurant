import sys

def check_frontend():
    print("Checking frontend files for requested functionality...")
    with open('frontend/src/pages/management/ManagementKitchenPage.vue', 'r') as f:
        vue = f.read()

    # 1. Check Optimistic Update Guard
    if "inFlightMutations.value.has(no.name)" in vue and "inFlightMutations.value.add(order.name)" in vue:
        print("[OK] Optimistic update race condition guarded (inFlightMutations).")
    else:
        print("[FAIL] Optimistic guard missing.")

    # 2. Check Listener Cleanup
    if "window.removeEventListener('online', handleOnline)" in vue:
        print("[OK] Event listener leak cleanup is present.")
    else:
        print("[FAIL] Listener cleanup missing.")

    # 3. Check Search Functionality
    if "it.title || it.item_name" in vue and "it.note" in vue:
        print("[OK] Search covers item titles and notes.")
    else:
        print("[FAIL] Deep search missing.")

check_frontend()
