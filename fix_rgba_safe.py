import os
import re

for root, _, files in os.walk('frontend/src'):
    for file in files:
        if file.endswith('.vue'):
            path = os.path.join(root, file)
            with open(path, 'r') as f:
                content = f.read()
            
            # rgb(0 0 0 / 0.45) -> rgba(0, 0, 0, 0.45)
            content = re.sub(r'rgb\(\s*0\s+0\s+0\s*/\s*([0-9.]+)\s*\)', r'rgba(0, 0, 0, \1)', content)
            # rgb(255 255 255 / 0.45) -> rgba(255, 255, 255, 0.45)
            content = re.sub(r'rgb\(\s*255\s+255\s+255\s*/\s*([0-9.]+)\s*\)', r'rgba(255, 255, 255, \1)', content)
            
            # Also rgb(15 23 42 / 0.22) etc
            content = re.sub(r'rgb\(\s*(\d+)\s+(\d+)\s+(\d+)\s*/\s*([0-9.]+)\s*\)', r'rgba(\1, \2, \3, \4)', content)
            
            with open(path, 'w') as f:
                f.write(content)
