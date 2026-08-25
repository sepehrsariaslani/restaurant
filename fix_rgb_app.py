with open('frontend/src/App.vue', 'r') as f:
    content = f.read()

# Add light mode rgb variables
light_rgb = """
  --mg-primary-rgb: 201, 120, 82;
  --mg-success-rgb: 111, 123, 86;
  --mg-danger-rgb: 166, 84, 63;
  --mg-shadow-sm:"""

content = content.replace("  --mg-shadow-sm:", light_rgb)

# Add dark mode rgb variables
dark_rgb = """
  --mg-primary-rgb: 192, 112, 80;
  --mg-success-rgb: 127, 139, 84;
  --mg-danger-rgb: 194, 91, 78;
  --mg-shadow-sm:"""

content = content.replace("  --mg-shadow-sm:", dark_rgb)

with open('frontend/src/App.vue', 'w') as f:
    f.write(content)
