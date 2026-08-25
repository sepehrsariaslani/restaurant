import os
import re

def repl_pos(match):
    var_name = match.group(1)
    
    if var_name in ['text', 'text-main', 'primary-text']: return 'var(--mg-text-main)'
    if var_name in ['muted', 'text-muted']: return 'var(--mg-text-muted)'
    
    if var_name in ['surface', 'card', 'white', 'bg-surface']: return 'var(--mg-bg-surface)'
    if var_name in ['soft', 'hover', 'bg-page']: return 'var(--mg-bg-page)'
    
    if var_name in ['border', 'border-light']: return 'var(--mg-border-light)'
    if var_name in ['border-strong']: return 'var(--mg-border)'
    
    if var_name in ['primary']: return 'var(--mg-primary)'
    if var_name in ['accent', 'warning']: return 'var(--mg-primary)'
    
    if var_name in ['success']: return 'var(--mg-success)'
    if var_name in ['danger']: return 'var(--mg-danger)'
    
    return match.group(0)

for root, _, files in os.walk('frontend/src'):
    for file in files:
        if file.endswith('.vue'):
            path = os.path.join(root, file)
            with open(path, 'r') as f:
                content = f.read()
            
            # Find var(--pos-<name>) or var(--pos-<name>, fallback)
            new_content = re.sub(r'var\(--pos-([a-zA-Z\-]+)(?:,\s*[^)]+)?\)', repl_pos, content)
            
            if new_content != content:
                with open(path, 'w') as f:
                    f.write(new_content)
                print(f"Fixed POS vars in {path}")
