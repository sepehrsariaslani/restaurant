import re

with open("frontend/src/pages/management/ManagementKitchenPage.vue", "r") as f:
    content = f.read()

# Let's count how many times "import ManagementPageScaffold" occurs
count = content.count("import ManagementPageScaffold")
print("Occurrences of ManagementPageScaffold import:", count)
