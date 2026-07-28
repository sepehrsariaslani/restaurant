import re

with open('frontend/src/components/management/ManagementLayout.vue', 'r') as f:
    content = f.read()

# Replace header block
old_header = """				<header v-if="!isPosPage && !isKitchenPage" class="desktop-header">
					<div class="page-title-wrap">
						<h1>{{ activeTitle }}</h1>
					</div>

					<div class="desktop-header-actions">
						<button type="button" class="utility-icon-btn" @click="toggleTheme" :title="isDarkMode ? 'حالت روز' : 'حالت شب'">
							<SunIcon v-if="isDarkMode" class="icon-sm" />
							<MoonIcon v-else class="icon-sm" />
						</button>

						<div class="desktop-zoom">
							<button type="button" class="zoom-btn" :disabled="!canIncrease" @click="increaseScale" title="بزرگ‌نمایی">A+</button>
							<button type="button" class="zoom-btn" :disabled="!canDecrease" @click="decreaseScale" title="کوچک‌نمایی">A-</button>
						</div>

						<a class="utility-icon-btn site-link" href="/menu" title="مشاهده سایت مشتری">
							<ExternalLinkIcon class="icon-sm" />
						</a>

						<template v-if="!authLoading">
							<a v-if="authGuest" class="header-auth-btn" :href="loginUrl">ورود</a>
							<div v-else class="user-dropdown-trigger">
								<div class="header-user-chip" :title="authProfile.user">
									<strong>{{ authProfile.full_name || authProfile.user }}</strong>
								</div>
								<button class="header-auth-btn muted" type="button" @click="submitLogout" :disabled="authSubmitting">خروج</button>
							</div>
						</template>
					</div>
				</header>"""

new_header = """				<header v-if="!isPosPage && !isKitchenPage" class="desktop-header">
					<div class="page-title-wrap">
						<h1>{{ activeTitle }}</h1>
					</div>

					<div class="desktop-header-actions">
						<button type="button" class="utility-icon-btn theme-toggle-btn" @click="toggleTheme" :title="isDarkMode ? 'حالت روز' : 'حالت شب'">
							<SunIcon v-if="isDarkMode" class="icon-sm" />
							<MoonIcon v-else class="icon-sm" />
						</button>

						<template v-if="!authLoading">
							<a v-if="authGuest" class="header-auth-btn" :href="loginUrl">ورود</a>
							<div v-else class="user-dropdown-wrapper">
								<button type="button" class="user-dropdown-trigger" @click="toggleUserMenu">
									<div class="header-user-avatar">
										{{ (authProfile.full_name || authProfile.user).charAt(0) }}
									</div>
									<div class="header-user-info">
										<strong>{{ authProfile.full_name || authProfile.user }}</strong>
										<small>{{ authProfile.roles?.includes('System Manager') ? 'مدیر سیستم' : 'کاربر' }}</small>
									</div>
									<ChevronDownIcon class="icon-sm dropdown-chevron" />
								</button>
								
								<Transition name="dropdown-anim">
									<div v-if="userMenuOpen" class="user-dropdown-menu">
										<a class="user-menu-item" href="/menu">
											<ExternalLinkIcon class="icon-sm" />
											<span>سایت مشتری</span>
										</a>
										<div class="user-menu-divider"></div>
										<button class="user-menu-item text-danger" type="button" @click="submitLogout" :disabled="authSubmitting">
											<LogOutIcon class="icon-sm" />
											<span>{{ authSubmitting ? 'در حال خروج...' : 'خروج از حساب' }}</span>
										</button>
									</div>
								</Transition>
								
								<!-- Invisible backdrop to close menu when clicking outside -->
								<div v-if="userMenuOpen" class="user-dropdown-backdrop" @click="userMenuOpen = false"></div>
							</div>
						</template>
					</div>
				</header>"""

content = content.replace(old_header, new_header)

# Import LogOut
content = content.replace(
    'ExternalLink as ExternalLinkIcon,',
    'ExternalLink as ExternalLinkIcon,\n\tLogOut as LogOutIcon,'
)

# Add userMenuOpen ref
content = content.replace(
    'const mobileMenuOpen = ref(false);',
    'const mobileMenuOpen = ref(false);\nconst userMenuOpen = ref(false);'
)

# Add toggleUserMenu function
content = content.replace(
    'function toggleRailMode() {',
    'function toggleUserMenu() {\n\t\tuserMenuOpen.value = !userMenuOpen.value;\n\t}\n\n\tfunction toggleRailMode() {'
)

# Update CSS for header
old_css_header = """	.desktop-header {
		height: 4.5rem;
		background: var(--mg-bg-page);
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 0 2rem;
		position: sticky;
		top: 0;
		z-index: 40;
	}

	.page-title-wrap h1 {
		margin: 0;
		font-size: 1.2rem;
		font-weight: 900;
		color: var(--mg-text-main);
		letter-spacing: -0.02em;
	}

	.desktop-header-actions {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.utility-icon-btn {
		width: 2.4rem;
		height: 2.4rem;
		border-radius: 50%;
		border: none;
		background: transparent;
		color: var(--mg-text-muted);
		display: grid;
		place-items: center;
		cursor: pointer;
	}
	.utility-icon-btn:hover { background: var(--mg-bg-surface); color: var(--mg-text-main); }

	.desktop-zoom {
		display: flex;
		align-items: center;
		background: var(--mg-bg-surface);
		border-radius: 99px;
		padding: 0 0.25rem;
		margin: 0 0.5rem;
		border: 1px solid var(--mg-border-light);
	}
	.zoom-btn {
		background: transparent;
		border: none;
		color: var(--mg-text-muted);
		font-weight: 800;
		font-size: 0.8rem;
		padding: 0.4rem 0.6rem;
		cursor: pointer;
	}
	.zoom-btn:hover:not(:disabled) { color: var(--mg-text-main); }
	.zoom-btn:disabled { opacity: 0.3; }

	.user-dropdown-trigger {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		background: var(--mg-bg-surface);
		padding: 0.25rem 0.5rem;
		border-radius: 99px;
		border: 1px solid var(--mg-border-light);
		margin-right: 0.5rem;
	}
	.header-user-chip strong {
		font-size: 0.85rem;
		color: var(--mg-text-main);
		padding: 0 0.5rem;
	}
	.header-auth-btn {
		background: transparent;
		border: none;
		padding: 0.3rem 0.5rem;
		border-radius: 99px;
		font-size: 0.8rem;
		font-weight: 700;
		color: var(--mg-danger);
		cursor: pointer;
	}
	.header-auth-btn:hover { background: var(--mg-danger-bg); }"""


new_css_header = """	.desktop-header {
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

	.page-title-wrap h1 {
		margin: 0;
		font-size: 1.25rem;
		font-weight: 900;
		color: var(--mg-text-main);
		letter-spacing: -0.01em;
	}

	.desktop-header-actions {
		display: flex;
		align-items: center;
		gap: 1.25rem;
	}

	.utility-icon-btn {
		width: 2.5rem;
		height: 2.5rem;
		border-radius: 50%;
		border: 1px solid var(--mg-border-light);
		background: var(--mg-bg-surface);
		color: var(--mg-text-muted);
		display: grid;
		place-items: center;
		cursor: pointer;
		transition: all 0.2s ease;
	}
	.utility-icon-btn:hover { 
		background: var(--mg-primary); 
		color: #fff; 
		border-color: var(--mg-primary);
		transform: translateY(-1px);
		box-shadow: 0 4px 12px rgba(var(--mg-primary-rgb), 0.2);
	}

	.user-dropdown-wrapper {
		position: relative;
	}

	.user-dropdown-trigger {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		background: var(--mg-bg-surface);
		padding: 0.4rem 0.6rem 0.4rem 1rem;
		border-radius: 99px;
		border: 1px solid var(--mg-border-light);
		cursor: pointer;
		transition: all 0.2s;
	}
	.user-dropdown-trigger:hover {
		border-color: var(--mg-primary);
		box-shadow: 0 4px 12px rgba(var(--mg-primary-rgb), 0.08);
	}

	.header-user-avatar {
		width: 2.25rem;
		height: 2.25rem;
		border-radius: 50%;
		background: var(--mg-primary);
		color: #fff;
		display: grid;
		place-items: center;
		font-weight: 800;
		font-size: 1rem;
	}

	.header-user-info {
		display: flex;
		flex-direction: column;
		align-items: flex-start;
		text-align: right;
	}
	.header-user-info strong {
		font-size: 0.85rem;
		color: var(--mg-text-main);
		line-height: 1.1;
	}
	.header-user-info small {
		font-size: 0.65rem;
		color: var(--mg-text-muted);
		font-weight: 700;
	}

	.dropdown-chevron {
		color: var(--mg-text-muted);
		margin-right: 0.5rem;
		opacity: 0.7;
	}

	.user-dropdown-menu {
		position: absolute;
		top: calc(100% + 0.5rem);
		left: 0;
		min-width: 180px;
		background: var(--mg-bg-surface);
		border: 1px solid var(--mg-border-light);
		border-radius: 16px;
		box-shadow: 0 12px 32px rgba(0,0,0,0.08);
		padding: 0.5rem;
		display: flex;
		flex-direction: column;
		z-index: 100;
	}

	.user-menu-item {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		padding: 0.75rem 1rem;
		border-radius: 10px;
		text-decoration: none;
		color: var(--mg-text-main);
		font-size: 0.9rem;
		font-weight: 700;
		background: transparent;
		border: none;
		cursor: pointer;
		transition: all 0.2s;
		text-align: right;
		width: 100%;
	}
	.user-menu-item:hover {
		background: var(--mg-bg-page);
		color: var(--mg-primary);
	}
	.user-menu-item.text-danger:hover {
		background: var(--mg-danger-bg);
		color: var(--mg-danger);
	}

	.user-menu-divider {
		height: 1px;
		background: var(--mg-border-light);
		margin: 0.25rem 0.5rem;
	}

	.user-dropdown-backdrop {
		position: fixed;
		inset: 0;
		z-index: 90;
	}

	.dropdown-anim-enter-active, .dropdown-anim-leave-active {
		transition: all 0.2s cubic-bezier(0.175, 0.885, 0.32, 1.275);
		transform-origin: top left;
	}
	.dropdown-anim-enter-from, .dropdown-anim-leave-to {
		opacity: 0;
		transform: scale(0.95) translateY(-10px);
	}"""

content = content.replace(old_css_header, new_css_header)

with open('frontend/src/components/management/ManagementLayout.vue', 'w') as f:
    f.write(content)

