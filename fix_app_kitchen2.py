with open('frontend/src/App.vue', 'r') as f:
    content = f.read()

# Fix routing so it is consistent.
content = content.replace(
    "if (pathname.startsWith('/management/kitchen')) return 'management-kitchen'",
    "if (pathname.startsWith('/management/kitchen')) return 'management-kitchen'"
)

# And fix App.vue template:
content = content.replace(
    "<ManagementKitchenPage v-else-if=\"page === 'kitchen'\" />",
    "<ManagementKitchenPage v-else-if=\"page === 'management-kitchen'\" />"
)

# Wait, previously I replaced management-kitchen with kitchen.
content = content.replace(
    "v-else-if=\"page === 'kitchen'\"",
    "v-else-if=\"page === 'management-kitchen'\""
)

with open('frontend/src/App.vue', 'w') as f:
    f.write(content)
    
with open('frontend/src/components/management/ManagementLayout.vue', 'r') as f:
    layout = f.read()
    
# Update ManagementLayout to expect management-kitchen
layout = layout.replace(
    'const isKitchenPage = computed(() => props.page === "kitchen");',
    'const isKitchenPage = computed(() => props.page === "management-kitchen");'
)

with open('frontend/src/components/management/ManagementLayout.vue', 'w') as f:
    f.write(layout)
