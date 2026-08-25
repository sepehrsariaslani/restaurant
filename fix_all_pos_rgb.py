import os
import re

for root, _, files in os.walk('frontend/src'):
    for file in files:
        if file.endswith('.vue'):
            path = os.path.join(root, file)
            with open(path, 'r') as f:
                content = f.read()
            
            new_content = content
            new_content = new_content.replace('--pos-primary-rgb', '--mg-primary-rgb')
            new_content = new_content.replace('--pos-accent-rgb', '--mg-primary-rgb') # mapping accent to primary
            new_content = new_content.replace('--pos-success-rgb', '--mg-success-rgb')
            new_content = new_content.replace('--pos-danger-rgb', '--mg-danger-rgb')
            new_content = new_content.replace('--pos-warning-rgb', '--mg-primary-rgb')
            
            if new_content != content:
                with open(path, 'w') as f:
                    f.write(new_content)
                print(f"Fixed RGB in {path}")
