with open('frontend/src/App.vue', 'r') as f:
    content = f.read()

# Remove all those added blocks
bad_block = """
  --mg-primary-rgb: 201 120 82;
  --mg-success-rgb: 111 123 86;
  --mg-danger-rgb: 166 84 63;

  --mg-primary-rgb: 192 112 80;
  --mg-success-rgb: 127 139 84;
  --mg-danger-rgb: 194 91 78;
"""
content = content.replace(bad_block, "")

light_block = """  --mg-success-bg: #E2E6D7;
  --mg-primary-rgb: 201 120 82;
  --mg-success-rgb: 111 123 86;
  --mg-danger-rgb: 166 84 63;"""
content = content.replace("  --mg-success-bg: #E2E6D7;", light_block)

dark_block = """  --mg-success-bg: #2E3321;
  --mg-primary-rgb: 192 112 80;
  --mg-success-rgb: 127 139 84;
  --mg-danger-rgb: 194 91 78;"""
content = content.replace("  --mg-success-bg: #2E3321;", dark_block)

with open('frontend/src/App.vue', 'w') as f:
    f.write(content)
