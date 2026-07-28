import re

with open('frontend/src/components/management/ManagementLayout.vue', 'r') as f:
    layout = f.read()

# We need to move `.dfm-wrapper` inside the header, but header is NOT shown on POS and KITCHEN pages.
# Wait, user said: "به غیر از این انگاری صفحه pos هدر نداره اگر میشه اونم برای من درست بکن"
# User wants the header on POS page too!
# Let's remove `v-if="!isPosPage && !isKitchenPage"` from the desktop header, so it shows everywhere!

layout = layout.replace('<header v-if="!isPosPage && !isKitchenPage" class="desktop-header">', '<header class="desktop-header">')

# Wait, if we move the dfm-wrapper into the header, the header must have it on the right side.
# And we also need to remove the current dfm-wrapper from outside the header.

old_dfm = """			<!-- Floating Action Menu Button (FAB) -->
			<div class="dfm-wrapper">
				<button 
					type="button" 
					class="dfm-toggle-btn" 
					:class="{ 'is-open': !isRailCollapsed }" 
					@click="toggleRailMode" 
					:title="isRailCollapsed ? 'باز کردن منو' : 'بستن منو'"
				>
					<span class="dfm-burger">
						<span class="dfm-line top"></span>
						<span class="dfm-line mid"></span>
						<span class="dfm-line bot"></span>
					</span>
				</button>

				<Transition name="dfm-anim">
					<aside v-if="!isRailCollapsed" class="dfm-dropdown">
						<div class="dfm-brand-block">
							<a class="dfm-brand" href="/management" @click="toggleRailMode">
								<span class="brand-mark"><img class="brand-image" src="/NooshYar%20Image.png" alt="NooshYar" /></span>
								<span class="dfm-brand-text"><strong>نوش‌یار</strong><small>مدیریت عملیاتی</small></span>
							</a>
						</div>
						<nav class="accordion-nav dfm-nav">
							<div v-for="group in menuGroups" :key="group.key" class="nav-group" :class="{ open: isGroupOpen(group.key) }">
								<div class="group-title-rail">{{ group.title }}</div>
								<div class="group-items">
									<a v-for="item in group.items" :key="item.key" :href="item.url" :target="item.target || '_self'" class="nav-item" :class="{ active: isLinkActive(item.key) }" :title="item.label" @click="toggleRailMode">
										<span class="item-icon"><component :is="item.iconComponent" class="icon-sm" /></span>
										<span class="item-label"><strong>{{ item.label }}</strong></span>
									</a>
								</div>
							</div>
						</nav>
					</aside>
				</Transition>
				<Transition name="fade">
					<div v-if="!isRailCollapsed" class="dfm-backdrop" @click="toggleRailMode"></div>
				</Transition>
			</div>"""

# Remove it from its current position
layout = layout.replace(old_dfm, "")

# Add it into the header (before page-title-wrap)
new_header_start = """				<header class="desktop-header">
					<div class="desktop-header-start">
""" + old_dfm.replace('class="dfm-wrapper"', 'class="dfm-wrapper inline-dfm"') + """
					<div class="page-title-wrap">
						<h1>{{ activeTitle }}</h1>
					</div>
					</div>"""

layout = layout.replace("""				<header class="desktop-header">
					<div class="page-title-wrap">
						<h1>{{ activeTitle }}</h1>
					</div>""", new_header_start)

# Update the CSS for the DFM wrapper so it is relative to the header and NOT fixed on the screen edge
css_replace = """	.desktop-header {
		height: 4.5rem;
		background: var(--mg-bg-page);
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 0 2rem;
		position: sticky;
		top: 0;
		z-index: 40;
		border-bottom: 1px solid var(--mg-border-light);
	}

	.desktop-header-start {
		display: flex;
		align-items: center;
		gap: 1.5rem;
	}"""

layout = layout.replace("""	.desktop-header {
		height: 4.5rem;
		background: var(--mg-bg-page);
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 0 2rem;
		position: sticky;
		top: 0;
		z-index: 40;
		border-bottom: 1px solid var(--mg-border-light);
	}""", css_replace)

dfm_css_replace = """	/* --- Desktop Floating Menu (Integrated in Header) --- */
	.dfm-wrapper.inline-dfm {
		position: relative;
		z-index: 10000;
	}

	.dfm-dropdown {
		position: absolute;
		top: calc(100% + 1rem);
		right: 0;
"""

layout = layout.replace("""	/* --- Desktop Floating Menu (Top Right) --- */
	.dfm-wrapper {
		position: fixed;
		top: 1.25rem;
		right: 1.25rem;
		z-index: 10000;
	}

	.dfm-toggle-btn {""", """	/* --- Desktop Floating Menu (Top Right) --- */
	.dfm-wrapper.inline-dfm {
		position: relative;
		z-index: 10000;
	}

	.dfm-toggle-btn {""")

# We also need to fix `desktop-header` in kitchen.
# Before: 
#	.management-layout--kitchen .desktop-header {
#		display: none;
#	}
# We should remove that so kitchen also gets the header!
layout = layout.replace("""	.management-layout--kitchen .desktop-header {
		display: none;
	}
	.management-layout--kitchen .desktop-main {
		padding: 0;
	}""", """	.management-layout--kitchen .desktop-main {
		padding: 0;
	}""")

# Oh and wait, `padding-right: 6.5rem !important;` from earlier should be removed because it was for the fixed FAB
layout = layout.replace("""	.desktop-header {
		padding-right: 6.5rem !important; /* Make room for the top-right floating button */
	}""", "")

with open('frontend/src/components/management/ManagementLayout.vue', 'w') as f:
    f.write(layout)

