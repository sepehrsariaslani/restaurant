import re

with open('frontend/src/components/management/ManagementLayout.vue', 'r') as f:
    content = f.read()

# Add isKitchenPage
if "isKitchenPage = computed" not in content:
    content = content.replace(
        'const isPosPage = computed(() => props.page === "management-pos");',
        'const isPosPage = computed(() => props.page === "management-pos");\nconst isKitchenPage = computed(() => props.page === "kitchen");'
    )

    content = content.replace(
        "'management-layout--pos': isPosPage,",
        "'management-layout--pos': isPosPage,\n\t\t\t'management-layout--kitchen': isKitchenPage,"
    )
    
    content = content.replace(
        ":class=\"{ 'desktop-main--fullbleed': isPosPage }\"",
        ":class=\"{ 'desktop-main--fullbleed': isPosPage || isKitchenPage }\""
    )

with open('frontend/src/components/management/ManagementLayout.vue', 'w') as f:
    f.write(content)
