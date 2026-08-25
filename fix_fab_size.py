with open('frontend/src/components/management/ManagementLayout.vue', 'r') as f:
    content = f.read()

content = content.replace("width: 3.8rem;\n\t\theight: 3.8rem;", "width: 3.2rem;\n\t\theight: 3.2rem;")
content = content.replace("width: 22px;\n\t\theight: 16px;", "width: 18px;\n\t\theight: 14px;")

with open('frontend/src/components/management/ManagementLayout.vue', 'w') as f:
    f.write(content)
