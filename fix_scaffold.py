with open('frontend/src/pages/management/ManagementKitchenPage.vue', 'r') as f:
    content = f.read()

content = content.replace(
    '<ManagementPageScaffold title="" subtitle="" :show-title="false">',
    '<div class="kds-workspace">'
)
content = content.replace(
    '</ManagementPageScaffold>',
    '</div>'
)
content = content.replace(
    "import ManagementPageScaffold from '@/components/management/ManagementPageScaffold.vue'\n",
    ""
)

# Also let's tighten up the layout in CSS
css_tweak = """
.kds-workspace {
  display: flex;
  flex-direction: column;
  height: 100%;
}
"""
content = content.replace('/* 1. Header & Toolbar */', css_tweak + '\n/* 1. Header & Toolbar */')

with open('frontend/src/pages/management/ManagementKitchenPage.vue', 'w') as f:
    f.write(content)
