import re

# 1. ManagementLayout.vue
with open('frontend/src/components/management/ManagementLayout.vue', 'r') as f:
    layout = f.read()

layout = layout.replace(
    'const isKitchenPage = computed(() => props.page === "kitchen");',
    'const isKitchenPage = computed(() => props.page === "management-kitchen");'
)

with open('frontend/src/components/management/ManagementLayout.vue', 'w') as f:
    f.write(layout)

# 2. App.vue
with open('frontend/src/App.vue', 'r') as f:
    app_vue = f.read()

app_vue = app_vue.replace(
    "<KitchenDisplayPage v-else-if=\"page === 'kitchen' || page === 'management-kitchen'\" />",
    "<KitchenDisplayPage v-else-if=\"page === 'kitchen'\" />"
)

with open('frontend/src/App.vue', 'w') as f:
    f.write(app_vue)

print("Frontend routing fixed.")
