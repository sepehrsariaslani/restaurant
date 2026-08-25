import os
import re

for root, _, files in os.walk('frontend/src'):
    for file in files:
        if file.endswith('.vue'):
            path = os.path.join(root, file)
            with open(path, 'r') as f:
                content = f.read()
            
            # The syntax rgb(var(--mg-primary-rgb) / 0.12) is valid in modern CSS (CSS Color Module Level 4).
            # However, some older setups or specific Vite/PostCSS pipelines might strip it if not configured right.
            # Let's convert them to rgba() format for maximum safety.
            # The problem is var() inside rgba() isn't strictly standard if the var contains spaces, 
            # BUT modern browsers handle `rgba(var(--my-rgb), 0.5)` perfectly if `--my-rgb` is `201, 120, 82`.
            # Wait, our vars are defined as `201 120 82` without commas. 
            # So `rgb(var(--mg-primary-rgb) / 0.12)` IS the correct modern syntax for space-separated lists.
            # Let's check if there are any rgba() with space separated vars that might be breaking.
            
            new_content = re.sub(r'rgb\(var\((--mg-[a-z\-]+-rgb)\)\s*/\s*([0-9.]+)\)', r'rgba(var(\1), \2)', content)
            
            # We must make sure the CSS vars have commas if we use rgba(var(), alpha)
            # Actually, `rgba(var(--foo), 0.5)` requires `--foo` to be `r, g, b`.
            # If `--foo` is `r g b`, `rgba` breaks in many browsers!
            # Let's just use color-mix instead of rgb/rgba to be 100% safe.
            # color-mix(in srgb, var(--mg-primary) 12%, transparent)
            pass

def replace_with_color_mix(match):
    var_name = match.group(1).replace('-rgb', '')
    alpha = float(match.group(2))
    percent = int(alpha * 100)
    return f"color-mix(in srgb, var({var_name}) {percent}%, transparent)"

for root, _, files in os.walk('frontend/src'):
    for file in files:
        if file.endswith('.vue'):
            path = os.path.join(root, file)
            with open(path, 'r') as f:
                content = f.read()
                
            new_content = re.sub(r'rgb\(var\((--mg-[a-z\-]+-rgb)\)\s*/\s*([0-9.]+)\)', replace_with_color_mix, content)
            
            if new_content != content:
                with open(path, 'w') as f:
                    f.write(new_content)
                print(f"Replaced rgb with color-mix in {path}")
