import re

with open('frontend/src/components/management/pos/PosCategorySidebar.vue', 'r') as f:
    content = f.read()

content = content.replace('var(--pos-border)', 'var(--mg-border-light)')
content = content.replace('var(--pos-white)', 'var(--mg-bg-surface)')
content = content.replace('var(--pos-text)', 'var(--mg-text-main)')

with open('frontend/src/components/management/pos/PosCategorySidebar.vue', 'w') as f:
    f.write(content)
