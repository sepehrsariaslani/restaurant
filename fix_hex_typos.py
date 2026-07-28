import re

def fix(path):
    with open(path, 'r') as f:
        content = f.read()

    content = content.replace('var(--mg-success)22', 'var(--mg-success-bg)')
    content = content.replace('var(--mg-primary)22', 'var(--mg-bg-soft)')
    content = content.replace('var(--mg-danger)22', 'var(--mg-danger-bg)')

    with open(path, 'w') as f:
        f.write(content)

fix('frontend/src/pages/management/ManagementPosPage.vue')
fix('frontend/src/components/management/pos/PosCartPanel.vue')
