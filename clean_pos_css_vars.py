import os
import re

for filepath in [
    'frontend/src/components/management/pos/PosCartPanel.vue',
    'frontend/src/components/management/pos/PosProductPanel.vue',
    'frontend/src/components/management/pos/PosHeaderBar.vue'
]:
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            content = f.read()

        # Remove local variable blocks that look like --pos-xxx: var(...);
        content = re.sub(r'^\s*--[a-z\-]+:\s*var\(--[a-z\-]+\);\s*$', '', content, flags=re.MULTILINE)
        
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"Cleaned vars in {filepath}")
