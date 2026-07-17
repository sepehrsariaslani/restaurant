import re

with open('frontend/src/components/management/ManagementLayout.vue', 'r') as f:
    content = f.read()

# Make the old sidebar code the new floating menu code if it hasn't been merged
content = content.replace('.dfm-wrapper {', '/* DFM Styles */\n.dfm-wrapper {')

with open('frontend/src/components/management/ManagementLayout.vue', 'w') as f:
    f.write(content)

