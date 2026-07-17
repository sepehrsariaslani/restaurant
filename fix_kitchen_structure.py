import re

with open('frontend/src/pages/management/ManagementKitchenPage.vue', 'r') as f:
    content = f.read()

# I will parse the template out and replace the <template> part.
