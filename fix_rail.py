with open('frontend/src/components/management/ManagementLayout.vue', 'r') as f:
    content = f.read()

toggle_btn = """
					<button type="button" class="utility-icon-btn rail-toggle-btn" @click="toggleRailMode" :title="isRailCollapsed ? 'باز کردن منو' : 'بستن منو'">
						<PanelRightCloseIcon v-if="!isRailCollapsed" class="icon-sm" />
						<PanelRightOpenIcon v-else class="icon-sm" />
					</button>
"""

# Insert button in sidebar logo block
content = content.replace(
    '<a class="rail-brand" href="/management">',
    toggle_btn + '\n\t\t\t\t\t<a class="rail-brand" href="/management">'
)

# Insert CSS for rail-collapsed
css_add = """
	.rail-toggle-btn { margin-right: auto; }
	.rail-collapsed .desktop-sidebar { width: 5.5rem; }
	.rail-collapsed .rail-brand-text,
	.rail-collapsed .group-title-rail,
	.rail-collapsed .item-label { display: none; }
	.rail-collapsed .nav-item { justify-content: center; padding: 0.8rem; }
	
	.sidebar-logo-block { justify-content: space-between; }
"""

content = content.replace(
    '.desktop-sidebar {\n\t\twidth: 16rem;',
    '.desktop-sidebar {\n\t\twidth: 16rem;\n\t\ttransition: width 0.2s;'
)

content = content.replace(
    '/* Kitchen Page Specific Sidebar Tweaks */',
    css_add + '\n\t/* Kitchen Page Specific Sidebar Tweaks */'
)

# Remove the forced kitchen layout since we now have rail-collapsed
content = content.replace(
"""	/* Kitchen Page Specific Sidebar Tweaks */
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
	}""",
"""	/* Kitchen Page Specific Sidebar Tweaks (Use rail-collapsed mostly, but we can keep these as fallback or let the user decide.
       Actually, let's let KDS default to collapsed via JS, but user can open it) */"""
)

# In JS, default kitchen to railMode = "icons"
js_add = """
	if (isKitchenPage.value) {
		railMode.value = "icons";
	} else {
		railMode.value = ["expanded", "icons"].includes(storedRailMode)
			? storedRailMode
			: "expanded";
	}
"""

content = content.replace(
    """		railMode.value = ["expanded", "icons"].includes(storedRailMode)
			? storedRailMode
			: "expanded";""",
    js_add
)

with open('frontend/src/components/management/ManagementLayout.vue', 'w') as f:
    f.write(content)
