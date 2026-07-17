import re

with open('frontend/src/pages/management/ManagementPosPage.vue', 'r') as f:
    content = f.read()

# simple check for assignments without declaration in <script setup>
in_script = False
lines = content.split('\n')
for i, line in enumerate(lines):
    if '<script setup>' in line:
        in_script = True
    elif '</script>' in line:
        in_script = False
    
    if in_script:
        line_clean = line.strip()
        # assignment like `foo = bar` where foo is not `value`, `form.field`, etc.
        m = re.match(r'^([a-zA-Z0-9_]+)\s*=', line_clean)
        if m:
            var_name = m.group(1)
            # check if it's already declared
            if not re.search(r'\b(const|let|var|function)\s+' + var_name + r'\b', content):
                # Also filter out common global or reactive assignments if they are refs (wait, refs use .value)
                # Filter out standard assignments
                print(f"Line {i+1}: {line_clean}")
