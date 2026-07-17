import re

with open('frontend/src/pages/management/ManagementPosPage.vue', 'r') as f:
    content = f.read()

# Remove the broken .pos-theme variables block entirely. 
# It shouldn't be defining --mg variables to themselves!
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
  --mg-primary-soft: var(--mg-primary);
}
"""

if broken_theme in content:
    content = content.replace(broken_theme, "")
else:
    # Use regex to strip it
    content = re.sub(r'\.pos-theme\s*\{[^}]*\}', '.pos-theme {}', content)

# I should also fix ManagementPosPage.vue where `--mg-bg-surface, var(--mg-bg-surface)` occurs:
content = re.sub(r'var\(--mg-bg-surface,\s*var\(--mg-bg-surface\)\)', 'var(--mg-bg-surface)', content)
content = re.sub(r'var\(--mg-text-main,\s*var\(--mg-text-main\)\)', 'var(--mg-text-main)', content)

with open('frontend/src/pages/management/ManagementPosPage.vue', 'w') as f:
    f.write(content)
