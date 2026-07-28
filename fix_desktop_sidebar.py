import re

with open('frontend/src/components/management/ManagementLayout.vue', 'r') as f:
    layout = f.read()

# Replace desktop layout with floating menu approach
old_desktop_layout = """		<!-- Desktop Layout -->
		<div class="desktop-layout">
			<!-- Sidebar -->
			<aside class="desktop-sidebar">
				<div class="sidebar-logo-block">
					
					<button type="button" class="utility-icon-btn rail-toggle-btn" @click="toggleRailMode" :title="isRailCollapsed ? 'باز کردن منو' : 'بستن منو'">
						<PanelRightCloseIcon v-if="!isRailCollapsed" class="icon-sm" />
						<PanelRightOpenIcon v-else class="icon-sm" />
					</button>

					<a class="rail-brand" href="/management">
						<span class="rail-brand-mark"><img class="brand-image brand-image-lg" src="/NooshYar%20Image.png" alt="NooshYar" /></span>
						<span class="rail-brand-text"><strong>نوش‌یار</strong><small>مدیریت عملیاتی</small></span>
					</a>
				</div>

				<nav class="accordion-nav desktop-nav">
					<div v-for="group in menuGroups" :key="group.key" class="nav-group" :class="{ open: isGroupOpen(group.key) }">
						<div class="group-title-rail">{{ group.title }}</div>
						<div class="group-items">
							<a v-for="item in group.items" :key="item.key" :href="item.url" :target="item.target || '_self'" class="nav-item" :class="{ active: isLinkActive(item.key) }" :title="item.label">
								<span class="item-icon"><component :is="item.iconComponent" class="icon-sm" /></span>
								<span class="item-label"><strong>{{ item.label }}</strong></span>
							</a>
						</div>
					</div>
				</nav>
			</aside>"""

new_desktop_layout = """		<!-- Desktop Layout -->
		<div class="desktop-layout">
			
			<!-- Floating Action Menu Button (FAB) -->
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
			</div>
"""

layout = layout.replace(old_desktop_layout, new_desktop_layout)

# Update CSS for Floating Menu
css_changes = """
	.desktop-main--fullbleed { padding: 0; }
	
	/* --- Desktop Floating Menu --- */
	.dfm-wrapper {
		position: fixed;
		bottom: 1.5rem;
		left: 1.5rem;
		z-index: 9999;
	}

	.dfm-toggle-btn {
		width: 3.5rem;
		height: 3.5rem;
		border-radius: 50%;
		background: var(--mg-primary);
		color: #fff;
		border: none;
		display: flex;
		align-items: center;
		justify-content: center;
		cursor: pointer;
		box-shadow: 0 10px 24px rgb(var(--mg-primary-rgb) / 0.35);
		transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
		position: relative;
		z-index: 10000;
	}
	
	.dfm-toggle-btn::before {
		content: '';
		position: absolute;
		inset: -4px;
		border-radius: 50%;
		border: 1px solid var(--mg-primary);
		opacity: 0;
		animation: dfm-pulse 3s infinite;
	}

	@keyframes dfm-pulse {
		0% { transform: scale(0.9); opacity: 0; }
		50% { transform: scale(1.1); opacity: 0.3; }
		100% { transform: scale(1.3); opacity: 0; }
	}

	.dfm-toggle-btn:hover {
		transform: scale(1.05) translateY(-2px);
		box-shadow: 0 14px 28px rgb(var(--mg-primary-rgb) / 0.45);
	}

	.dfm-burger {
		width: 22px;
		height: 18px;
		position: relative;
	}
	.dfm-line {
		display: block;
		width: 100%;
		height: 2.5px;
		background: #fff;
		border-radius: 2px;
		position: absolute;
		left: 0;
		transition: all 0.3s ease;
	}
	.dfm-line.top { top: 0; }
	.dfm-line.mid { top: 50%; transform: translateY(-50%); }
	.dfm-line.bot { bottom: 0; }

	.dfm-toggle-btn.is-open {
		background: var(--mg-bg-surface);
		color: var(--mg-primary);
		box-shadow: 0 8px 24px rgba(0,0,0,0.1);
	}
	.dfm-toggle-btn.is-open .dfm-line { background: var(--mg-primary); }
	.dfm-toggle-btn.is-open .dfm-line.top { top: 50%; transform: translateY(-50%) rotate(45deg); }
	.dfm-toggle-btn.is-open .dfm-line.mid { opacity: 0; }
	.dfm-toggle-btn.is-open .dfm-line.bot { bottom: 50%; transform: translateY(50%) rotate(-45deg); }

	.dfm-dropdown {
		position: absolute;
		bottom: 4.5rem;
		left: 0;
		width: 17rem;
		background: var(--mg-bg-surface);
		border: 1px solid var(--mg-border-light);
		border-radius: 20px;
		box-shadow: 0 24px 48px rgba(0,0,0,0.15);
		display: flex;
		flex-direction: column;
		max-height: calc(100vh - 6rem);
		z-index: 9999;
		overflow: hidden;
	}

	.dfm-brand-block {
		padding: 1.25rem 1.25rem;
		border-bottom: 1px solid var(--mg-border-light);
		background: var(--mg-bg-page);
	}

	.dfm-brand {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		text-decoration: none;
		color: var(--mg-text-main);
	}
	
	.dfm-brand-text { display: grid; }
	.dfm-brand-text strong { font-weight: 900; font-size: 1.1rem; letter-spacing: -0.01em; }
	.dfm-brand-text small { font-size: 0.75rem; color: var(--mg-text-muted); margin-top: 0.1rem; }

	.dfm-nav {
		padding: 1rem;
		overflow-y: auto;
		gap: 1.25rem;
	}

	.dfm-backdrop {
		position: fixed;
		inset: 0;
		background: rgba(0,0,0,0.2);
		backdrop-filter: blur(2px);
		z-index: 9998;
	}

	.dfm-anim-enter-active, .dfm-anim-leave-active {
		transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
		transform-origin: bottom left;
	}
	.dfm-anim-enter-from, .dfm-anim-leave-to {
		opacity: 0;
		transform: scale(0.9) translateY(20px);
	}

	/* Desktop layout content takes full width now */
	.desktop-sidebar { display: none; }
"""

# Re-inject the CSS part
# Find the line: .desktop-main--fullbleed { padding: 0; }
layout = re.sub(
    r'\.desktop-main--fullbleed \{ padding: 0; \}.*?/\* Nav Styles \*/',
    css_changes + '\n/* Nav Styles */',
    layout,
    flags=re.DOTALL
)

# And make sure desktop-content takes full width instead of flex: 1 with a sidebar.
# Actually, since .desktop-sidebar is hidden, desktop-content naturally takes 100%.

# Wait, initial state of railMode is "expanded". We should change it to "icons" meaning closed.
layout = layout.replace(
    'const railMode = ref("expanded");',
    'const railMode = ref("icons");'
)

# And the watcher for isKitchenPage shouldn't mess it up.
layout = layout.replace(
"""	if (isKitchenPage.value) {
		railMode.value = "icons";
	} else {
		railMode.value = ["expanded", "icons"].includes(storedRailMode)
			? storedRailMode
			: "expanded";
	}""",
"""	railMode.value = "icons"; // Default to closed for all pages with floating menu"""
)

with open('frontend/src/components/management/ManagementLayout.vue', 'w') as f:
    f.write(layout)
