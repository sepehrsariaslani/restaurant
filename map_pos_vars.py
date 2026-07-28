import os
import re

def repl(match):
    var_name = match.group(0)
    
    # We directly replace known pos- variables with mg- variables
    mapping = {
        '--pos-primary': '--mg-primary',
        '--pos-primary-rgb': '--mg-primary-rgb',
        '--pos-accent': '--mg-primary',
        '--pos-accent-rgb': '--mg-primary-rgb',
        '--pos-danger': '--mg-danger',
        '--pos-danger-rgb': '--mg-danger-rgb',
        '--pos-success': '--mg-success',
        '--pos-success-rgb': '--mg-success-rgb',
        '--pos-warning': '--mg-primary',
        '--pos-warning-rgb': '--mg-primary-rgb',
    }
    
    return mapping.get(var_name, var_name)

for root, _, files in os.walk('frontend/src'):
    for file in files:
        if file.endswith('.vue'):
            path = os.path.join(root, file)
            with open(path, 'r') as f:
                content = f.read()
            
            new_content = re.sub(r'--pos-[a-z\-]+(?:-rgb)?', repl, content)
            
            if new_content != content:
                with open(path, 'w') as f:
                    f.write(new_content)
                print(f"Mapped variables in {path}")
