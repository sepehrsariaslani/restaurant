import os
import re

for root, _, files in os.walk('frontend/src'):
    for file in files:
        if file.endswith('.vue'):
            path = os.path.join(root, file)
            with open(path, 'r') as f:
                content = f.read()
            
            # Replace unsplash strings with '/NooshYar Image.png'
            new_content = re.sub(
                r"'(https?://images\.unsplash\.com/[^']+)'",
                "'/NooshYar%20Image.png'",
                content
            )
            # Also double quote ones
            new_content = re.sub(
                r'"(https?://images\.unsplash\.com/[^"]+)"',
                "'/NooshYar%20Image.png'",
                new_content
            )
            
            if new_content != content:
                with open(path, 'w') as f:
                    f.write(new_content)
                print(f"Fixed unsplash in {path}")

