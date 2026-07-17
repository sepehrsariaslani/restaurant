import re

with open('frontend/src/components/management/ManagementLayout.vue', 'r') as f:
    content = f.read()

# Wait, my regex replaced the wrong thing. Let's fix it by replacing the whole header section

header_start = content.find('<header class="desktop-header">')
header_end = content.find('</header>', header_start) + len('</header>')

new_header = """				<header class="desktop-header">
					<div class="desktop-header-start">
						<div class="page-title-wrap">
							<h1>{{ activeTitle }}</h1>
						</div>
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

						<!-- Menu Toggle Button (FAB inline) -->
						<div class="dfm-wrapper inline-dfm">
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
					</div>
				</header>"""

content = content[:header_start] + new_header + content[header_end:]

# And let's fix the CSS
css_fix = """	/* --- Desktop Floating Menu (Integrated in Header) --- */
	.dfm-wrapper.inline-dfm {
		position: relative;
		z-index: 10000;
	}

	.dfm-dropdown {
		position: absolute;
		top: calc(100% + 1.25rem);
		left: 0;
		width: 17rem;
		background: color-mix(in srgb, var(--mg-bg-surface) 96%, transparent);
		backdrop-filter: blur(16px);
		-webkit-backdrop-filter: blur(16px);
		border: 1px solid var(--mg-border-light);
		border-radius: 20px;
		box-shadow: 0 32px 64px rgba(0,0,0,0.15);
		display: flex;
		flex-direction: column;
		max-height: calc(100vh - 6rem);
		z-index: 10000;
		overflow: hidden;
	}
"""

content = re.sub(r'/\* --- Desktop Floating Menu.*\.dfm-dropdown \{[^}]*\}', css_fix, content, flags=re.DOTALL)

with open('frontend/src/components/management/ManagementLayout.vue', 'w') as f:
    f.write(content)
