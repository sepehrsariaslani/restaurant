<template>
	<aside
		v-if="variant === 'desktop'"
		class="management-navbar management-navbar--desktop"
		:class="{ 'is-collapsed': isCollapsed }"
		aria-label="ناوبری مدیریت"
	>
		<div class="navbar-brand-row">
			<a href="/management" class="navbar-brand" :title="isCollapsed ? 'رفتن به داشبورد' : undefined">
				<span class="navbar-brand-mark">
					<img src="/NooshYar%20Image.png" alt="" />
				</span>
				<span v-if="!isCollapsed" class="navbar-brand-copy">
					<strong>نوش‌یار</strong>
					<small>{{ brandName }}</small>
				</span>
			</a>
			<button
				type="button"
				class="navbar-collapse-button"
				:aria-label="isCollapsed ? 'باز کردن نوار ناوبری' : 'جمع کردن نوار ناوبری'"
				:title="isCollapsed ? 'باز کردن نوار ناوبری' : 'جمع کردن نوار ناوبری'"
				@click="toggleCollapsed"
			>
				<PanelRightOpen v-if="isCollapsed" :size="18" aria-hidden="true" />
				<PanelRightClose v-else :size="18" aria-hidden="true" />
			</button>
		</div>

		<nav v-if="isCollapsed" class="navbar-icon-list" aria-label="دسترسی سریع">
			<a
				v-for="item in flatLinks"
				:key="item.key"
				:href="item.url"
				:target="item.target || '_self'"
				:rel="item.target === '_blank' ? 'noopener noreferrer' : undefined"
				class="navbar-icon-link"
				:class="{ active: item.key === activeKey }"
				:title="item.label"
				:aria-label="item.label"
				:aria-current="item.key === activeKey ? 'page' : undefined"
			>
				<component :is="item.iconComponent" :size="18" aria-hidden="true" />
			</a>
		</nav>

		<nav v-else class="navbar-groups" aria-label="بخش‌های مدیریت">
			<section v-for="group in groupsWithItems" :key="group.key" class="navbar-group">
				<button
					type="button"
					class="navbar-group-trigger"
					:aria-expanded="String(isGroupOpen(group.key))"
					@click="toggleGroup(group.key)"
				>
					<component :is="group.icon" class="navbar-group-icon" aria-hidden="true" />
					<span>{{ group.title }}</span>
					<ChevronDown class="navbar-chevron" :class="{ open: isGroupOpen(group.key) }" :size="15" aria-hidden="true" />
				</button>
				<Transition name="navbar-accordion">
					<div v-show="isGroupOpen(group.key)" class="navbar-group-links">
						<a
							v-for="item in group.items"
							:key="item.key"
							:href="item.url"
							:target="item.target || '_self'"
							:rel="item.target === '_blank' ? 'noopener noreferrer' : undefined"
							class="navbar-link"
							:class="{ active: item.key === activeKey }"
							:aria-current="item.key === activeKey ? 'page' : undefined"
						>
							<component :is="item.iconComponent" class="navbar-link-icon" aria-hidden="true" />
							<span>{{ item.label }}</span>
						</a>
					</div>
				</Transition>
			</section>
		</nav>
	</aside>

	<template v-else>
		<nav v-if="showMobileBar" class="management-mobile-nav" aria-label="دسترسی‌های اصلی مدیریت">
			<a
				v-for="item in primaryLinks"
				:key="item.key"
				:href="item.url"
				:target="item.target || '_self'"
				:rel="item.target === '_blank' ? 'noopener noreferrer' : undefined"
				class="management-mobile-nav-link"
				:class="{ active: item.key === activeKey }"
				:aria-current="item.key === activeKey ? 'page' : undefined"
			>
				<component :is="item.iconComponent" :size="20" aria-hidden="true" />
				<span>{{ item.shortLabel || item.label }}</span>
			</a>
		</nav>

		<Transition name="navbar-fade">
			<button
				v-if="mobileOpen"
				type="button"
				class="management-mobile-nav-scrim"
				aria-label="بستن منو"
				@click="closeMobileMenu"
			/>
		</Transition>
		<Transition name="navbar-drawer">
			<aside
				v-if="mobileOpen"
				class="management-mobile-drawer"
				dir="rtl"
				role="dialog"
				aria-modal="true"
				aria-label="منوی مدیریت"
			>
				<div class="management-mobile-drawer-head">
					<a href="/management" class="navbar-brand">
						<span class="navbar-brand-mark"><img src="/NooshYar%20Image.png" alt="" /></span>
						<span class="navbar-brand-copy"><strong>نوش‌یار</strong><small>{{ brandName }}</small></span>
					</a>
					<button type="button" class="navbar-close-button" aria-label="بستن منو" @click="closeMobileMenu">
						<X :size="20" aria-hidden="true" />
					</button>
				</div>

				<nav class="management-mobile-drawer-groups" aria-label="همه بخش‌های مدیریت">
					<section v-for="group in groupsWithItems" :key="group.key" class="navbar-group">
						<button
							type="button"
							class="navbar-group-trigger"
							:aria-expanded="String(isGroupOpen(group.key))"
							@click="toggleGroup(group.key)"
						>
							<component :is="group.icon" class="navbar-group-icon" aria-hidden="true" />
							<span>{{ group.title }}</span>
							<ChevronDown class="navbar-chevron" :class="{ open: isGroupOpen(group.key) }" :size="15" aria-hidden="true" />
						</button>
						<div v-show="isGroupOpen(group.key)" class="navbar-group-links">
							<a
								v-for="item in group.items"
								:key="item.key"
								:href="item.url"
								:target="item.target || '_self'"
								:rel="item.target === '_blank' ? 'noopener noreferrer' : undefined"
								class="navbar-link"
								:class="{ active: item.key === activeKey }"
								:aria-current="item.key === activeKey ? 'page' : undefined"
								@click="closeMobileMenu"
							>
								<component :is="item.iconComponent" class="navbar-link-icon" aria-hidden="true" />
								<span>{{ item.label }}</span>
							</a>
						</div>
					</section>
				</nav>

				<div class="management-mobile-drawer-utilities">
					<a href="/menu" class="drawer-utility-link" @click="closeMobileMenu">
						<ExternalLink :size="17" aria-hidden="true" />
						سایت مشتری
					</a>
					<button type="button" class="drawer-utility-link" @click="$emit('toggle-theme')">
						<component :is="isDarkMode ? Sun : Moon" :size="17" aria-hidden="true" />
						{{ isDarkMode ? 'حالت روز' : 'حالت شب' }}
					</button>
					<button
						type="button"
						class="drawer-utility-link drawer-utility-link--danger"
						:disabled="authSubmitting"
						@click="$emit('logout')"
					>
						<LogOut :size="17" aria-hidden="true" />
						{{ authSubmitting ? 'در حال خروج...' : 'خروج از حساب' }}
					</button>
				</div>
			</aside>
		</Transition>
	</template>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { ChevronDown, ExternalLink, LogOut, Moon, PanelRightClose, PanelRightOpen, Sun, X } from 'lucide-vue-next'

const props = defineProps({
	variant: { type: String, default: 'desktop' },
	groups: { type: Array, default: () => [] },
	primaryLinks: { type: Array, default: () => [] },
	activeKey: { type: String, default: '' },
	activeGroupKey: { type: String, default: '' },
	brandName: { type: String, default: 'پنل مدیریت' },
	isDarkMode: { type: Boolean, default: false },
	authSubmitting: { type: Boolean, default: false },
	mobileOpen: { type: Boolean, default: false },
	showMobileBar: { type: Boolean, default: true },
})

const emit = defineEmits(['update:mobileOpen', 'toggle-theme', 'logout'])
const collapsedStorageKey = 'restaurant.management.navbar.collapsed'
const isCollapsed = ref(false)
const storageReady = ref(false)
const openGroups = ref({})

const groupsWithItems = computed(() => props.groups.filter((group) => group.items?.length))
const flatLinks = computed(() => groupsWithItems.value.flatMap((group) => group.items))

function isGroupOpen(key) {
	return Boolean(openGroups.value[key])
}

function toggleGroup(key) {
	openGroups.value = { ...openGroups.value, [key]: !openGroups.value[key] }
}

function toggleCollapsed() {
	isCollapsed.value = !isCollapsed.value
}

function closeMobileMenu() {
	emit('update:mobileOpen', false)
}

function handleKeydown(event) {
	if (event.key === 'Escape' && props.mobileOpen) closeMobileMenu()
}

onMounted(() => {
	if (props.variant === 'desktop' && typeof window !== 'undefined') {
		try {
			isCollapsed.value = window.localStorage.getItem(collapsedStorageKey) === 'true'
		} catch {
			isCollapsed.value = false
		}
		storageReady.value = true
	}
})

watch(isCollapsed, (value) => {
	if (props.variant !== 'desktop' || !storageReady.value || typeof window === 'undefined') return
	try {
		window.localStorage.setItem(collapsedStorageKey, String(value))
	} catch {
		// Keep the navigation usable when browser storage is unavailable.
	}
})

watch(
	() => props.activeGroupKey,
	(key) => {
		if (key) openGroups.value = { ...openGroups.value, [key]: true }
	},
	{ immediate: true },
)

watch(
	() => props.mobileOpen,
	(open) => {
		if (typeof window === 'undefined') return
		if (open) window.addEventListener('keydown', handleKeydown)
		else window.removeEventListener('keydown', handleKeydown)
	},
)

onBeforeUnmount(() => {
	if (typeof window !== 'undefined') window.removeEventListener('keydown', handleKeydown)
})
</script>

<style scoped>
.management-navbar--desktop {
	--navbar-width: 17rem;
	position: relative;
	width: var(--navbar-width);
	min-width: var(--navbar-width);
	height: 100dvh;
	min-height: 0;
	display: flex;
	flex-direction: column;
	overflow: hidden;
	background: var(--mg-bg-surface);
	border-left: 1px solid var(--mg-border-light);
	transition: width 200ms ease, min-width 200ms ease;
}

.management-navbar--desktop.is-collapsed {
	--navbar-width: 4.5rem;
}

.navbar-brand-row {
	min-height: 3.5rem;
	display: flex;
	align-items: center;
	gap: 0.5rem;
	padding: 0 0.75rem;
	border-bottom: 1px solid var(--mg-border-light);
}

.navbar-brand {
	min-width: 0;
	flex: 1;
	display: flex;
	align-items: center;
	gap: 0.65rem;
	color: var(--mg-text-main);
	text-decoration: none;
}

.navbar-brand-mark {
	width: 2.1rem;
	height: 2.1rem;
	flex: 0 0 auto;
	display: grid;
	place-items: center;
	overflow: hidden;
	border-radius: 0.75rem;
	background: var(--mg-bg-page);
}

.navbar-brand-mark img {
	width: 100%;
	height: 100%;
	object-fit: contain;
}

.navbar-brand-copy {
	min-width: 0;
	display: grid;
	line-height: 1.3;
}

.navbar-brand-copy strong { font-size: 0.9rem; font-weight: 900; }
.navbar-brand-copy small { overflow: hidden; color: var(--mg-text-muted); font-size: 0.67rem; text-overflow: ellipsis; white-space: nowrap; }

.navbar-collapse-button,
.navbar-close-button {
	width: 2.5rem;
	height: 2.5rem;
	flex: 0 0 auto;
	display: grid;
	place-items: center;
	border: 0;
	border-radius: 0.75rem;
	background: transparent;
	color: var(--mg-text-muted);
	cursor: pointer;
}

.navbar-collapse-button:hover,
.navbar-close-button:hover { background: var(--mg-bg-page); color: var(--mg-text-main); }

.navbar-groups,
.navbar-icon-list {
	min-height: 0;
	flex: 1;
	overflow-y: auto;
	overscroll-behavior: contain;
	padding: 0.75rem 0.65rem 1rem;
}

.navbar-group { margin-block-end: 0.25rem; }

.navbar-group-trigger {
	width: 100%;
	min-height: 2.75rem;
	display: flex;
	align-items: center;
	gap: 0.65rem;
	padding: 0.5rem 0.65rem;
	border: 0;
	border-radius: 0.8rem;
	background: transparent;
	color: var(--mg-text-muted);
	font: inherit;
	font-size: 0.83rem;
	font-weight: 800;
	text-align: right;
	cursor: pointer;
	transition: background 160ms ease, color 160ms ease;
}

.navbar-group-trigger:hover { background: var(--mg-bg-page); color: var(--mg-text-main); }
.navbar-group-icon { width: 1.05rem; height: 1.05rem; flex: 0 0 auto; color: var(--mg-primary); }
.navbar-group-trigger span { min-width: 0; flex: 1; }
.navbar-chevron { flex: 0 0 auto; transition: transform 160ms ease; }
.navbar-chevron.open { transform: rotate(180deg); }

.navbar-group-links {
	display: grid;
	gap: 0.15rem;
	overflow: hidden;
	padding-block: 0.2rem 0.45rem;
}

.navbar-link {
	min-width: 0;
	min-height: 2.5rem;
	display: flex;
	align-items: center;
	gap: 0.6rem;
	padding: 0.45rem 0.7rem;
	border-radius: 0.7rem;
	color: var(--mg-text-muted);
	font-size: 0.79rem;
	font-weight: 650;
	text-decoration: none;
	transition: background 160ms ease, color 160ms ease;
}

.navbar-link span { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.navbar-link:hover { background: var(--mg-bg-page); color: var(--mg-text-main); }
.navbar-link.active { background: var(--mg-primary-soft, var(--mg-bg-page)); color: var(--mg-primary); font-weight: 850; }
.navbar-link-icon { width: 1rem; height: 1rem; flex: 0 0 auto; opacity: 0.82; }

.navbar-icon-list { display: grid; align-content: start; justify-items: center; gap: 0.3rem; padding-inline: 0.5rem; }
.navbar-icon-link {
	width: 2.75rem;
	height: 2.75rem;
	display: grid;
	place-items: center;
	border-radius: 0.85rem;
	color: var(--mg-text-muted);
	text-decoration: none;
	transition: background 160ms ease, color 160ms ease;
}
.navbar-icon-link:hover { background: var(--mg-bg-page); color: var(--mg-text-main); }
.navbar-icon-link.active { background: var(--mg-primary-soft, var(--mg-bg-page)); color: var(--mg-primary); }

.management-mobile-nav,
.management-mobile-drawer,
.management-mobile-nav-scrim { display: none; }

.navbar-group-trigger:focus-visible,
.navbar-link:focus-visible,
.navbar-icon-link:focus-visible,
.navbar-collapse-button:focus-visible,
.navbar-close-button:focus-visible,
.management-mobile-nav-link:focus-visible,
.drawer-utility-link:focus-visible {
	outline: 3px solid var(--mg-primary);
	outline-offset: 2px;
}

.navbar-accordion-enter-active,
.navbar-accordion-leave-active { max-height: 50rem; transition: max-height 180ms ease, opacity 180ms ease; }
.navbar-accordion-enter-from,
.navbar-accordion-leave-to { max-height: 0; opacity: 0; }

@media (max-width: 1023px) {
	.management-navbar--desktop { display: none; }
	.management-mobile-nav {
		position: relative;
		z-index: 50;
		min-height: calc(4.25rem + env(safe-area-inset-bottom));
		display: grid;
		grid-template-columns: repeat(5, minmax(0, 1fr));
		align-items: center;
		gap: 0.15rem;
		padding: 0.35rem max(0.45rem, env(safe-area-inset-left)) calc(0.35rem + env(safe-area-inset-bottom)) max(0.45rem, env(safe-area-inset-right));
		border-top: 1px solid var(--mg-border-light);
		background: color-mix(in srgb, var(--mg-bg-surface) 96%, transparent);
		box-shadow: var(--mg-shadow-sm);
		backdrop-filter: blur(16px);
	}
	.management-mobile-nav-link {
		min-width: 0;
		min-height: 3.25rem;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 0.2rem;
		border-radius: 0.85rem;
		color: var(--mg-text-muted);
		font-size: 0.62rem;
		font-weight: 750;
		text-decoration: none;
	}
	.management-mobile-nav-link span { max-width: 100%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
	.management-mobile-nav-link.active { background: var(--mg-primary-soft, var(--mg-bg-page)); color: var(--mg-primary); }
	.management-mobile-nav-scrim {
		position: fixed;
		z-index: 100;
		inset: 0;
		width: 100%;
		height: 100%;
		display: block;
		border: 0;
		background: color-mix(in srgb, var(--mg-text-main) 48%, transparent);
		backdrop-filter: blur(2px);
	}
	.management-mobile-drawer {
		position: fixed;
		z-index: 110;
		inset-block: 0;
		inset-inline-start: 0;
		width: min(88vw, 22rem);
		display: flex;
		flex-direction: column;
		background: var(--mg-bg-surface);
		box-shadow: var(--mg-shadow-md);
	}
	.management-mobile-drawer-head {
		min-height: 4rem;
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 0.75rem;
		padding: 0.5rem 1rem;
		border-bottom: 1px solid var(--mg-border-light);
	}
	.management-mobile-drawer-groups { min-height: 0; flex: 1; overflow-y: auto; overscroll-behavior: contain; padding: 0.65rem 0.75rem; }
	.management-mobile-drawer-utilities {
		display: grid;
		gap: 0.25rem;
		padding: 0.65rem 0.75rem max(0.65rem, env(safe-area-inset-bottom));
		border-top: 1px solid var(--mg-border-light);
		background: var(--mg-bg-page);
	}
	.drawer-utility-link {
		min-height: 2.75rem;
		display: flex;
		align-items: center;
		gap: 0.65rem;
		padding: 0.5rem 0.7rem;
		border: 0;
		border-radius: 0.75rem;
		background: transparent;
		color: var(--mg-text-main);
		font: inherit;
		font-size: 0.82rem;
		font-weight: 750;
		text-align: right;
		text-decoration: none;
		cursor: pointer;
	}
	.drawer-utility-link:hover { background: var(--mg-bg-surface); }
	.drawer-utility-link:disabled { cursor: wait; opacity: 0.6; }
	.drawer-utility-link--danger { color: var(--mg-danger); }
}

@media (prefers-reduced-motion: reduce) {
	.management-navbar--desktop,
	.navbar-group-trigger,
	.navbar-chevron,
	.navbar-link,
	.navbar-icon-link,
	.navbar-accordion-enter-active,
	.navbar-accordion-leave-active,
	.navbar-fade-enter-active,
	.navbar-fade-leave-active,
	.navbar-drawer-enter-active,
	.navbar-drawer-leave-active { transition-duration: 0.01ms; }
}

.navbar-fade-enter-active,
.navbar-fade-leave-active { transition: opacity 180ms ease; }
.navbar-fade-enter-from,
.navbar-fade-leave-to { opacity: 0; }
.navbar-drawer-enter-active,
.navbar-drawer-leave-active { transition: transform 220ms ease; }
.navbar-drawer-enter-from,
.navbar-drawer-leave-to { transform: translateX(100%); }
</style>
