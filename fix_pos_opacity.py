import re

with open('frontend/src/pages/management/ManagementPosPage.vue', 'r') as f:
    c = f.read()

# Replace any color-mix or rgb constructs with standard var(--mg-...) 
c = re.sub(r'color:\s*rgb\(var\(--mg-primary-rgb,\s*[0-9 ]+\)\s*/\s*0\.[45678][0-9]*\)', 'color: var(--mg-text-muted)', c)
c = re.sub(r'color:\s*rgb\(var\(--mg-primary-rgb,\s*[0-9 ]+\)\s*/\s*0\.[123][0-9]*\)', 'color: var(--mg-border-light)', c)
c = re.sub(r'background:\s*rgb\(var\(--mg-primary-rgb,\s*[0-9 ]+\)\s*/\s*0\.[012][0-9]*\)', 'background: var(--mg-bg-surface)', c)
c = re.sub(r'border-color:\s*rgb\(var\(--mg-primary-rgb,\s*[0-9 ]+\)\s*/\s*0\.\d+\)', 'border-color: var(--mg-border-light)', c)
c = re.sub(r'border-bottom:\s*1px solid rgb\(var\(--mg-primary-rgb,\s*[0-9 ]+\)\s*/\s*0\.\d+\)', 'border-bottom: 1px solid var(--mg-border-light)', c)
c = re.sub(r'box-shadow:\s*0 0 0 2px rgb\(var\(--mg-primary-rgb,\s*[0-9 ]+\)\s*/\s*0\.\d+\)', 'box-shadow: 0 0 0 2px var(--mg-primary)', c)

with open('frontend/src/pages/management/ManagementPosPage.vue', 'w') as f:
    f.write(c)

