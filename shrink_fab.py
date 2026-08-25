with open('frontend/src/components/management/ManagementLayout.vue', 'r') as f:
    content = f.read()

content = content.replace("width: 3.2rem;\n\t\theight: 3.2rem;", "width: 2.4rem;\n\t\theight: 2.4rem;")
content = content.replace("width: 18px;\n\t\theight: 14px;", "width: 14px;\n\t\theight: 10px;")

with open('frontend/src/components/management/ManagementLayout.vue', 'w') as f:
    f.write(content)
