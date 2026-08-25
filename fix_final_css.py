import re

with open('frontend/src/pages/management/ManagementPosPage.vue', 'r') as f:
    content = f.read()

# Replace any color-mix or rgb constructs with standard var(--mg-...) 
content = re.sub(r'rgb\(var\(--mg-primary-rgb,\s*[0-9 ]+\)\s*/\s*0\.\d+\)', 'var(--mg-primary)', content)
content = re.sub(r'rgb\(var\(--mg-success-rgb,\s*[0-9 ]+\)\s*/\s*0\.\d+\)', 'var(--mg-success)', content)
content = re.sub(r'rgb\(var\(--mg-danger-rgb,\s*[0-9 ]+\)\s*/\s*0\.\d+\)', 'var(--mg-danger)', content)
content = re.sub(r'rgb\(var\(--mg-warning-rgb,\s*[0-9 ]+\)\s*/\s*0\.\d+\)', 'var(--mg-primary)', content)
content = re.sub(r'color-mix\(in srgb, var\(--mg-bg-page\) 92%, transparent\)', 'var(--mg-bg-page)', content)

# Clean up some messy declarations at the top
css_start = """.pos-theme {
  --mg-primary: var(--mg-primary, var(--mg-primary));
  --mg-primary: var(--mg-primary, var(--mg-primary));
  --mg-success: var(--mg-success, var(--mg-success));
  --mg-danger: var(--mg-danger, var(--mg-danger));
  --mg-primary: var(--mg-primary, var(--mg-primary));
  --mg-bg-surface: var(--mg-bg-surface, var(--mg-bg-surface, var(--mg-bg-surface)));
  --mg-text-main: var(--text, var(--mg-primary, var(--mg-primary)));
  --mg-border: color-mix(in srgb, var(--border, var(--mg-border-light)) 88%, transparent);
  --mg-bg-page: color-mix(in srgb, var(--bg-soft, var(--mg-bg-page)) 92%, transparent);
  --mg-primary-soft: rgb(var(--mg-primary-rgb, 201 120 82) / 0.12);
}"""

css_clean = """.pos-theme {
  /* Inherits directly from root .management-layout scope */
}"""

content = content.replace(css_start, css_clean)

with open('frontend/src/pages/management/ManagementPosPage.vue', 'w') as f:
    f.write(content)
