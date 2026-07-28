import re

# 1. ManagementKitchenPage.vue (remove scaffold, use div.kds-workspace)
with open('frontend/src/pages/management/ManagementKitchenPage.vue', 'r') as f:
    kitchen_page = f.read()

kitchen_page = kitchen_page.replace(
    '<ManagementPageScaffold title="" subtitle="" :show-title="false">',
    '<div class="kds-workspace">'
)
kitchen_page = kitchen_page.replace(
    '</ManagementPageScaffold>',
    '</div>'
)
kitchen_page = kitchen_page.replace(
    "import ManagementPageScaffold from '@/components/management/ManagementPageScaffold.vue'\n",
    ""
)

# Update height logic to flex
css_tweak = """
.kds-workspace {
  display: flex;
  flex-direction: column;
  height: 100vh;
  padding: 1rem;
  overflow: hidden;
}
"""
kitchen_page = kitchen_page.replace('/* 1. Header & Toolbar */', css_tweak + '\n/* 1. Header & Toolbar */')

# Make kds-board flex: 1 and kds-column height: 100%
kitchen_page = kitchen_page.replace(
    'height: calc(100vh - 210px);',
    'height: 100%;'
)
kitchen_page = kitchen_page.replace(
    '.kds-board {',
    '.kds-board {\n  flex: 1;\n  overflow: hidden;\n'
)

with open('frontend/src/pages/management/ManagementKitchenPage.vue', 'w') as f:
    f.write(kitchen_page)

# 2. ManagementLayout.vue (Rail sidebar for kitchen, and remove desktop header for kitchen)
with open('frontend/src/components/management/ManagementLayout.vue', 'r') as f:
    layout = f.read()

if "isKitchenPage = computed" not in layout:
    layout = layout.replace(
        'const isPosPage = computed(() => props.page === "management-pos");',
        'const isPosPage = computed(() => props.page === "management-pos");\nconst isKitchenPage = computed(() => props.page === "kitchen");'
    )
    
    layout = layout.replace(
        "'management-layout--pos': isPosPage,",
        "'management-layout--pos': isPosPage,\n\t\t\t'management-layout--kitchen': isKitchenPage,"
    )
    
    layout = layout.replace(
        ":class=\"{ 'desktop-main--fullbleed': isPosPage }\"",
        ":class=\"{ 'desktop-main--fullbleed': isPosPage || isKitchenPage }\""
    )

    layout = layout.replace(
        "v-if=\"!isPosPage\"",
        "v-if=\"!isPosPage && !isKitchenPage\""
    )

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
		display: none;
	}
	.management-layout--kitchen .desktop-main {
		padding: 0;
	}
}

/* Nav Styles */
"""
    layout = layout.replace(
        "\t.desktop-main--fullbleed { padding: 0; }\n}\n\n/* Nav Styles */", 
        css_addition
    )

with open('frontend/src/components/management/ManagementLayout.vue', 'w') as f:
    f.write(layout)

