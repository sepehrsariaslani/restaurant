with open('frontend/src/pages/management/ManagementKitchenPage.vue', 'r') as f:
    content = f.read()

content = content.replace(
    '  height: 100%;\n}',
    '  max-height: 100%;\n}'
)

with open('frontend/src/pages/management/ManagementKitchenPage.vue', 'w') as f:
    f.write(content)
