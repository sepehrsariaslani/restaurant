import re

with open('frontend/src/pages/management/ManagementPosPage.vue', 'r') as f:
    content = f.read()

def repl_hex(match):
    hex_val = match.group(0).lower()
    
    # Text
    if hex_val in ['#1a1a1a', '#111827', '#1a2233', '#374151']: return 'var(--mg-text-main)'
    if hex_val in ['#6b7280', '#9ca3af', '#7b8ca6', '#d1d5db']: return 'var(--mg-text-muted)'
    
    # Backgrounds
    if hex_val in ['#ffffff', '#fff']: return 'var(--mg-bg-surface)'
    if hex_val in ['#f3f4f6', '#f4f6fa', '#f6f8fb']: return 'var(--mg-bg-page)'
    
    # Borders
    if hex_val in ['#e5e7eb', '#d6dde8']: return 'var(--mg-border-light)'
    
    # Greens/Olive (Success)
    if hex_val in ['#16a34a', '#15803d', '#166534', '#0b7d4a', '#22c55e', '#065f46', '#20483d', '#355e52']: return 'var(--mg-success)'
    if hex_val in ['#dcfce7', '#d1fae5', '#f0fdf4', '#86efac', '#bbf7d0', '#d3e2dc', '#97b6ac']: return 'var(--mg-success-bg)'
    
    # Reds (Danger)
    if hex_val in ['#ef4444', '#dc2626', '#ab3535', '#c62828']: return 'var(--mg-danger)'
    if hex_val in ['#fee2e2', '#fef2f2', '#fecaca']: return 'var(--mg-danger-bg)'
    
    # Primary/Oranges (Accent)
    if hex_val in ['#f59e0b', '#fbbf24', '#ff9836', '#c47c00', '#92400e', '#015a72']: return 'var(--mg-primary)'
    if hex_val in ['#fffbeb', '#fef3c7']: return 'var(--mg-bg-soft)'
    
    # Blues
    if hex_val in ['#3b82f6', '#2563eb', '#1e40af']: return 'var(--mg-primary)'
    if hex_val in ['#dbeafe', '#e0e7ff', '#bfdbfe', '#93c5fd']: return 'var(--mg-bg-soft)'
    
    return match.group(0)

content = re.sub(r'#[0-9a-fA-F]{3,6}', repl_hex, content)

with open('frontend/src/pages/management/ManagementPosPage.vue', 'w') as f:
    f.write(content)
