import os
import re

# Color replacements tailored to map specific legacy slate/blue/grey colors to the earthy token system
def replace_colors(match):
    color = match.group(0).lower()
    
    # Text colors
    if color in ['#0f172a', '#1c1411', '#1a130d', '#3d2510', '#111827', '#1f2937']:
        return 'var(--mg-text-main)'
    if color in ['#64748b', '#8a7867', '#7a6a60', '#786b61', '#7c6a5d', '#6b7280']:
        return 'var(--mg-text-muted)'
        
    # Backgrounds & Surfaces
    if color in ['#ffffff', '#fff']:
        # Don't blindly replace all white because some texts inside primary buttons might need white.
        # But we will use var(--mg-bg-surface) where appropriate, handled manually or let it be for now.
        return color
    if color in ['#f1f5f9', '#f5f0eb', '#f0ece7', '#f8fafc', '#f9fafb']:
        return 'var(--mg-bg-page)'
    if color in ['#f2f8f4']:
        return 'var(--mg-bg-surface)'
        
    # Borders
    if color in ['#e2e8f0', '#e0d8cf', '#e6dccf', '#ddd0c2', '#e5e7eb', '#ddd']:
        return 'var(--mg-border-light)'
        
    # Accents (Primary / Terracotta)
    if color in ['#8b5e34', '#6f4726', '#015a72', '#2563eb', '#3b82f6', '#ea580c']:
        return 'var(--mg-primary)'
        
    # Success (Olive)
    if color in ['#2f8f5b', '#174d32', '#166534', '#15803d', '#16a34a', '#22c55e']:
        return 'var(--mg-success)'
        
    # Danger
    if color in ['#dc2626', '#b84f4f', '#ef4444', '#fca5a5']:
        return 'var(--mg-danger)'
        
    return color

# Also replace raw rgba that matches common patterns
def replace_rgba(match):
    content = match.group(0)
    # Exclude rgba(255, 255, 255) to not break overlays
    if '255, 255, 255' in content or '255,255,255' in content: return content
    if '0, 0, 0' in content or '0,0,0' in content: return content
    return content

for directory in ['frontend/src/components/management', 'frontend/src/pages/management']:
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.vue'):
                path = os.path.join(root, file)
                with open(path, 'r') as f:
                    content = f.read()
                
                # Replace hex colors
                new_content = re.sub(r'#[0-9a-fA-F]{3,6}', replace_colors, content)
                
                # Replace specific slate variables if any
                new_content = re.sub(r'var\(--slate-\d+\)', 'var(--mg-text-muted)', new_content)
                new_content = re.sub(r'var\(--gray-\d+\)', 'var(--mg-border-light)', new_content)
                new_content = re.sub(r'var\(--border\)', 'var(--mg-border)', new_content)
                new_content = re.sub(r'var\(--surface\)', 'var(--mg-bg-surface)', new_content)
                new_content = re.sub(r'var\(--text\)', 'var(--mg-text-main)', new_content)
                new_content = re.sub(r'var\(--muted\)', 'var(--mg-text-muted)', new_content)
                
                if new_content != content:
                    with open(path, 'w') as f:
                        f.write(new_content)
                    print(f"Cleaned colors in {path}")
