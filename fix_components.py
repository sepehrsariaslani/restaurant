import os
import re

def update_file(filepath, mapping):
    with open(filepath, "r") as f:
        content = f.read()
    for old, new in mapping:
        content = content.replace(old, new)
    with open(filepath, "w") as f:
        f.write(content)
        
mapping = [
    ("var(--border, #e2e8f0)", "var(--mg-border-light)"),
    ("var(--bg-card, #fff)", "var(--mg-bg-surface)"),
    ("var(--text-primary, #0f172a)", "var(--mg-text-main)"),
    ("var(--text-muted, #64748b)", "var(--mg-text-muted)"),
    ("var(--bg-soft, #f1f5f9)", "var(--mg-bg-soft)"),
    ("var(--module-50, rgb(139 94 52 / 0.075))", "var(--mg-primary)"),
]

update_file("frontend/src/components/management/ManagementSurfaceCard.vue", mapping)
update_file("frontend/src/components/management/ManagementPageScaffold.vue", mapping)

print("Updated tokens in SurfaceCard and PageScaffold")
