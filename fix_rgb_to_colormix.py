import os
import re

def repl_rgb(match):
    var_name = match.group(1) # e.g., --mg-primary-rgb
    alpha_str = match.group(2) # e.g., 0.12
    
    # Extract base var name without -rgb
    base_var = var_name.replace('-rgb', '')
    
    # Calculate percentage
    try:
        alpha_float = float(alpha_str)
        percent = int(alpha_float * 100)
    except ValueError:
        percent = 100
        
    return f"color-mix(in srgb, var({base_var}) {percent}%, transparent)"

for root, _, files in os.walk('frontend/src'):
    for file in files:
        if file.endswith('.vue'):
            path = os.path.join(root, file)
            with open(path, 'r') as f:
                content = f.read()
            
            # Match rgb(var(--mg-primary-rgb) / 0.12)
            new_content = re.sub(r'rgb\(var\((--mg-[a-z\-]+-rgb)\)\s*/\s*([0-9.]+)\)', repl_rgb, content)
            
            # Also match rgb(var(--mg-primary-rgb)) -> var(--mg-primary)
            new_content = re.sub(r'rgb\(var\((--mg-[a-z\-]+-rgb)\)\)', lambda m: f"var({m.group(1).replace('-rgb', '')})", new_content)
            
            if new_content != content:
                with open(path, 'w') as f:
                    f.write(new_content)
                print(f"Fixed rgb()/alpha in {path}")
