import re

with open('frontend/src/App.vue', 'r') as f:
    content = f.read()

# Replace any occurrence of 'management-kitchen' to be 'kitchen'
# Because in App.vue it expects page === 'kitchen' based on the routing but actually looks like:
# if (pathname.startsWith('/management/kitchen')) return 'kitchen'

content = content.replace(
    "v-else-if=\"page === 'management-kitchen'\"",
    "v-else-if=\"page === 'kitchen'\""
)

# And in ManagementLayout it was looking for 'kitchen' too:
# const isKitchenPage = computed(() => props.page === "kitchen");

with open('frontend/src/App.vue', 'w') as f:
    f.write(content)
