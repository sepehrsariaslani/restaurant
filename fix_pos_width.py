import re

with open('frontend/src/components/management/ManagementLayout.vue', 'r') as f:
    layout = f.read()

# Make the wrapper for fullbleed max-width: 100%
# Currently it is:
# 	.desktop-main > :deep(*) {
# 		max-width: 1400px;
# 		margin-inline: auto;
# 	}
# We need:
#   .desktop-main--fullbleed > :deep(*) { max-width: 100%; margin-inline: 0; }

css_add = """
	.desktop-main > :deep(*) {
		max-width: 1400px;
		margin-inline: auto;
	}

	.desktop-main--fullbleed { padding: 0; }
	.desktop-main--fullbleed > :deep(*) { max-width: 100%; margin: 0; }
"""

layout = layout.replace("""	.desktop-main > :deep(*) {
		max-width: 1400px;
		margin-inline: auto;
	}

	
	.desktop-main--fullbleed { padding: 0; }""", css_add)

with open('frontend/src/components/management/ManagementLayout.vue', 'w') as f:
    f.write(layout)
