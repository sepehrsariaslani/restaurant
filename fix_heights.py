with open('frontend/src/pages/management/ManagementKitchenPage.vue', 'r') as f:
    content = f.read()

content = content.replace(
    'height: calc(100vh - 210px);',
    'height: calc(100vh - 11.5rem);'
)

with open('frontend/src/pages/management/ManagementKitchenPage.vue', 'w') as f:
    f.write(content)
