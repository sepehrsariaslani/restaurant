import re

with open('frontend/src/pages/management/ManagementPosPage.vue', 'r') as f:
    content = f.read()

# Replace any var(--pos-something, fallback)
content = re.sub(r'var\(--pos-(surface|card|white)(,\s*[^)]+)?\)', 'var(--mg-bg-surface)', content)
content = re.sub(r'var\(--pos-text(,\s*[^)]+)?\)', 'var(--mg-text-main)', content)
content = re.sub(r'var\(--pos-muted(,\s*[^)]+)?\)', 'var(--mg-text-muted)', content)
content = re.sub(r'var\(--pos-border(,\s*[^)]+)?\)', 'var(--mg-border-light)', content)
content = re.sub(r'var\(--pos-hover(,\s*[^)]+)?\)', 'var(--mg-bg-page)', content)

with open('frontend/src/pages/management/ManagementPosPage.vue', 'w') as f:
    f.write(content)

with open('frontend/src/components/management/pos/PosCartPanel.vue', 'r') as f:
    content = f.read()

content = re.sub(r'var\(--pos-(surface|card|white)(,\s*[^)]+)?\)', 'var(--mg-bg-surface)', content)
content = re.sub(r'var\(--pos-text(,\s*[^)]+)?\)', 'var(--mg-text-main)', content)
content = re.sub(r'var\(--pos-muted(,\s*[^)]+)?\)', 'var(--mg-text-muted)', content)
content = re.sub(r'var\(--pos-border(,\s*[^)]+)?\)', 'var(--mg-border-light)', content)
content = re.sub(r'var\(--pos-hover(,\s*[^)]+)?\)', 'var(--mg-bg-page)', content)

with open('frontend/src/components/management/pos/PosCartPanel.vue', 'w') as f:
    f.write(content)

