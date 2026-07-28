with open('frontend/src/components/management/ManagementLayout.vue', 'r') as f:
    content = f.read()

css_addition = """
	.desktop-main--fullbleed { padding: 0; }
	
	/* Kitchen Page Specific Sidebar Tweaks */
	.management-layout--kitchen .desktop-sidebar {
		width: 5.5rem;
	}
	.management-layout--kitchen .rail-brand-text,
	.management-layout--kitchen .group-title-rail,
	.management-layout--kitchen .item-label {
		display: none;
	}
	.management-layout--kitchen .nav-item {
		justify-content: center;
		padding: 0.8rem;
	}
	.management-layout--kitchen .desktop-header {
		padding: 0 1rem;
	}
	.management-layout--kitchen .desktop-main {
		padding: 1rem;
	}
}

/* Nav Styles */
"""

content = content.replace(
    "\t.desktop-main--fullbleed { padding: 0; }\n}\n\n/* Nav Styles */", 
    css_addition
)

with open('frontend/src/components/management/ManagementLayout.vue', 'w') as f:
    f.write(content)
