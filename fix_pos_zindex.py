import re

with open('frontend/src/components/management/pos/PosCartPanel.vue', 'r') as f:
    content = f.read()

# Make sure z-index is high enough to be above everything in Management layout
content = content.replace(
    'z-index: 300;',
    'z-index: 9999;'
)

with open('frontend/src/components/management/pos/PosCartPanel.vue', 'w') as f:
    f.write(content)
