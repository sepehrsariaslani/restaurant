import re

with open("frontend/src/pages/management/ManagementKitchenPage.vue", "r") as f:
    content = f.read()

# Make sure we use polling smartly
old_poll = """  if (pollTimer) clearInterval(pollTimer)
  pollTimer = setInterval(() => {
    if (document.visibilityState === 'visible' && isOnline.value) {
      fetchOrders()
    }
  }, 15000) // Poll every 15s"""

new_poll = """  if (pollTimer) clearInterval(pollTimer)
  pollTimer = setInterval(() => {
    if (document.visibilityState === 'visible' && isOnline.value) {
      fetchOrders()
    }
  }, 10000) // Poll every 10s for kitchen responsiveness"""

if old_poll in content:
    content = content.replace(old_poll, new_poll)
    with open("frontend/src/pages/management/ManagementKitchenPage.vue", "w") as f:
        f.write(content)
    print("Fixed polling interval")
else:
    print("Polling logic not found")
