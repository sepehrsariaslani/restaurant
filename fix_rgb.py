import os
import re

def repl_rgb(match):
    var_name = match.group(1)
    if 'primary' in var_name:
        return f"var(--{var_name}, 201 120 82)"
    elif 'success' in var_name:
        return f"var(--{var_name}, 111 123 86)"
    elif 'danger' in var_name:
        return f"var(--{var_name}, 166 84 63)"
    elif 'warning' in var_name:
        return f"var(--{var_name}, 201 120 82)"
    return match.group(0)

for root, _, files in os.walk('frontend/src/pages/management'):
    for file in files:
        if file.endswith('.vue'):
            path = os.path.join(root, file)
            with open(path, 'r') as f:
                content = f.read()
            new_content = re.sub(r'var\(--(mg-[a-z\-]+-rgb),\s*[0-9 ]+\)', repl_rgb, content)
            if new_content != content:
                with open(path, 'w') as f:
                    f.write(new_content)

for root, _, files in os.walk('frontend/src/components/management/pos'):
    for file in files:
        if file.endswith('.vue'):
            path = os.path.join(root, file)
            with open(path, 'r') as f:
                content = f.read()
            new_content = re.sub(r'var\(--(mg-[a-z\-]+-rgb),\s*[0-9 ]+\)', repl_rgb, content)
            if new_content != content:
                with open(path, 'w') as f:
                    f.write(new_content)

