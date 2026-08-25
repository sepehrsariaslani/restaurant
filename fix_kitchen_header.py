with open('frontend/src/components/management/ManagementLayout.vue', 'r') as f:
    content = f.read()

content = content.replace(
    "v-if=\"!isPosPage\"",
    "v-if=\"!isPosPage && !isKitchenPage\""
)

with open('frontend/src/components/management/ManagementLayout.vue', 'w') as f:
    f.write(content)
