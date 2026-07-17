import re

with open('frontend/src/components/management/ManagementLayout.vue', 'r') as f:
    layout = f.read()

# Make the POS page Full Bleed! Right now the layout forces max-width 1400px.
old_css = """	.desktop-main > :deep(*) {
		max-width: 1400px;
		margin-inline: auto;
	}

	.desktop-main--fullbleed { padding: 0; }"""

new_css = """	.desktop-main > :deep(*) {
		max-width: 1400px;
		margin-inline: auto;
	}

	.desktop-main--fullbleed { padding: 0; }
	.desktop-main--fullbleed > :deep(*) { max-width: 100%; margin: 0; }"""

layout = layout.replace(old_css, new_css)

# Also fix the size of the FAB menu button.
# User asked: "بازم دکمه ای که منو رو باز میکنه کوچیک بکن خیلییی باید از اینی که دارم کوچیک تر هم بشه برای من نصف بشه طول و عرضش"
layout = layout.replace('width: 3.2rem;\n\t\theight: 3.2rem;', 'width: 2.2rem;\n\t\theight: 2.2rem;')
layout = layout.replace('width: 18px;\n\t\theight: 14px;', 'width: 14px;\n\t\theight: 12px;')

with open('frontend/src/components/management/ManagementLayout.vue', 'w') as f:
    f.write(layout)
