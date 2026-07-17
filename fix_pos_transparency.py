import re

with open('frontend/src/pages/management/ManagementPosPage.vue', 'r') as f:
    content = f.read()

# Remove the broken .pos-theme variables block entirely. 
broken_theme = """
.pos-theme {
  --mg-primary: var(--mg-primary, var(--mg-primary));
  --mg-primary: var(--mg-primary, var(--mg-primary));
  --mg-success: var(--mg-success, var(--mg-success));
  --mg-danger: var(--mg-danger, var(--mg-danger));
  --mg-primary: var(--mg-primary, var(--mg-primary));
  --mg-bg-surface: var(--mg-bg-surface, var(--mg-bg-surface, var(--mg-bg-surface)));
  --mg-text-main: var(--text, var(--mg-primary, var(--mg-primary)));
  --mg-border: color-mix(in srgb, var(--border, var(--mg-border-light)) 88%, transparent);
  --mg-bg-page: color-mix(in srgb, var(--bg-soft, var(--mg-bg-page)) 92%, transparent);
  --mg-primary-soft: rgb(var(--mg-primary-rgb, 255 152 54) / 0.12);
}
"""

if broken_theme in content:
    content = content.replace(broken_theme, "")
else:
    content = re.sub(r'\.pos-theme\s*\{[^}]*\}', '', content)

with open('frontend/src/pages/management/ManagementPosPage.vue', 'w') as f:
    f.write(content)
