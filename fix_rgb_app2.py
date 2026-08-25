with open('frontend/src/App.vue', 'r') as f:
    content = f.read()

content = content.replace("201, 120, 82", "201 120 82")
content = content.replace("111, 123, 86", "111 123 86")
content = content.replace("166, 84, 63", "166 84 63")
content = content.replace("192, 112, 80", "192 112 80")
content = content.replace("127, 139, 84", "127 139 84")
content = content.replace("194, 91, 78", "194 91 78")

with open('frontend/src/App.vue', 'w') as f:
    f.write(content)
