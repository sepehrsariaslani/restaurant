import re

with open('frontend/src/components/management/ManagementLayout.vue', 'r') as f:
    layout = f.read()

# We need to make sure the style block is closed properly.
# The error was: CssSyntaxError: ... Unclosed block at line 1162 (or similar)
# Looking at the diff above, we replaced `.desktop-main--fullbleed { padding: 0; }\n}` 
# which closed the `@media (min-width: 1024px) {` block!
# Oh, that's why!

# So we need to re-add `}` at the end of the DFM changes.
css_fix = """
	.dfm-anim-enter-from, .dfm-anim-leave-to {
		opacity: 0;
		transform: scale(0.9) translateY(20px);
	}

	/* Desktop layout content takes full width now */
	.desktop-sidebar { display: none; }
}

/* Nav Styles */
"""

layout = layout.replace(
"""	.dfm-anim-enter-from, .dfm-anim-leave-to {
		opacity: 0;
		transform: scale(0.9) translateY(20px);
	}

	/* Desktop layout content takes full width now */
	.desktop-sidebar { display: none; }

/* Nav Styles */""", css_fix)

with open('frontend/src/components/management/ManagementLayout.vue', 'w') as f:
    f.write(layout)
