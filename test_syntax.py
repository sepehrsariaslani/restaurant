import re

with open('frontend/src/components/management/ManagementLayout.vue', 'r') as f:
    content = f.read()

# Let's ensure the JS logic is completely correct
# I need to verify that `const userMenuOpen = ref(false);` wasn't inserted multiple times or missing
if content.count('const userMenuOpen = ref(false);') > 1:
    print("Warning: Multiple userMenuOpen refs")

