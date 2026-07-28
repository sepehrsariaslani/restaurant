import re

with open('frontend/src/App.vue', 'r') as f:
    content = f.read()

# Fix the kitchen page route
content = content.replace(
    "<KitchenDisplayPage v-else-if=\"page === 'kitchen' || page === 'management-kitchen'\" />",
    ""
)

with open('frontend/src/App.vue', 'w') as f:
    f.write(content)
