<template>
	<!-- Guest/Auth Shell -->
	<section
		v-if="authGuest"
		class="management-auth-shell"
		:class="{ dark: isDarkMode }"
		:style="moduleThemeVars"
		dir="rtl"
	>
		<article v-if="authLoading" class="management-auth-card">
			<ManagementBearLoader :size="210" label="در حال آماده‌سازی پنل..." />
			<p class="auth-card-title">در حال بررسی وضعیت ورود...</p>
			<p class="auth-card-muted">چند لحظه صبر کنید.</p>
		</article>

		<ManagementLoginGate
			v-else
			:redirect-to="redirectTarget"
			@login-success="handleGuestLoginSuccess"
		/>

		<p v-if="authError" class="auth-error auth-error--login">
			{{ authError }}
		</p>
	</section>

	<!-- Main Management Layout -->
	<div
		v-else
		class="management-layout module-theme"
		:class="{
			dark: isDarkMode,
			'rail-collapsed': isDesktop && isRailCollapsed,
			'management-layout--pos': isPosPage,
			'management-layout--kitchen': isKitchenPage,
		}"
		:style="moduleThemeVars"
		dir="rtl"
	>
		<!-- Mobile Layout -->
		<div class="mobile-layout">
			<!-- Mobile Header -->
			<header class="mobile-header">
				<button
					type="button"
					class="icon-button"
					aria-label="باز کردن منو"
					@click="mobileMenuOpen = true"
				>
					<MenuIcon class="icon-md" />
				</button>

				<a href="/management" class="mobile-brand">
					<span class="brand-mark">
						<img class="brand-image" src="/NooshYar%20Image.png" alt="NooshYar" />
					</span>
					<span class="mobile-brand-text">
						<strong>نوش‌یار</strong>
						<small>پنل مدیریت</small>
					</span>
				</a>

				<a href="/menu" class="icon-button" title="مشاهده سایت مشتری">
					<HomeIcon class="icon-md" />
				</a>
			</header>

			<!-- Mobile Content -->
			<main class="mobile-main module-content">
				<div v-if="authLoading" class="auth-gate-card">
					<ManagementBearLoader :size="188" label="در حال همگام‌سازی نشست..." />
					<p class="auth-gate-title">در حال بروزرسانی نشست کاربر...</p>
					<p class="auth-card-muted">کمی صبر کنید.</p>
				</div>
				<slot v-else />
			</main>

			<!-- Mobile Bottom Navigation -->
			<nav class="mobile-bottom-nav">
				<a
					v-for="link in mobilePrimaryLinks"
					:key="`bottom-${link.key}`"
					:href="link.url"
					class="bottom-nav-item"
					:class="{ active: isLinkActive(link.key) }"
				>
					<component :is="link.iconComponent" class="icon-md" />
					<span>{{ link.shortLabel }}</span>
				</a>
			</nav>

			<!-- Mobile Sidebar Overlay -->
			<Transition name="fade">
				<div v-if="mobileMenuOpen" class="mobile-overlay" @click="closeMobileMenu" />
			</Transition>

			<Transition name="slide-right">
				<aside v-if="mobileMenuOpen" class="mobile-sidebar">
					<div class="mobile-sidebar-header">
						<div class="sidebar-title">
							<span class="brand-mark"><img class="brand-image" src="/NooshYar%20Image.png" alt="NooshYar" /></span>
							<div><strong>نوش‌یار</strong><small>{{ brandName }}</small></div>
						</div>
						<button type="button" class="icon-button" @click="closeMobileMenu"><XIcon class="icon-md" /></button>
					</div>

					<nav class="accordion-nav">
						<div v-for="group in menuGroups" :key="`mobile-group-${group.key}`" class="nav-group open">
							<div class="group-title-rail">{{ group.title }}</div>
							<div class="group-items">
								<a v-for="item in group.items" :key="`mobile-item-${item.key}`" :href="item.url" :target="item.target || '_self'" class="nav-item" :class="{ active: isLinkActive(item.key) }" @click="closeMobileMenu">
									<span class="item-icon"><component :is="item.iconComponent" class="icon-sm" /></span>
									<span>{{ item.label }}</span>
								</a>
							</div>
						</div>
					</nav>

					<div class="mobile-utility-zone">
						<a class="utility-link" href="/menu" @click="closeMobileMenu"><ExternalLinkIcon class="icon-sm" /> سایت مشتری</a>
						<button type="button" class="utility-link" @click="toggleTheme">
							<component :is="isDarkMode ? SunIcon : MoonIcon" class="icon-sm" /> 
							{{ isDarkMode ? 'حالت روز' : 'حالت شب' }}
						</button>
						<template v-if="!authLoading && !authGuest">
							<button type="button" class="utility-link text-danger" :disabled="authSubmitting" @click="handleMobileLogout">
								<UserIcon class="icon-sm" /> {{ authSubmitting ? 'در حال خروج...' : 'خروج از حساب' }}
							</button>
						</template>
					</div>
				</aside>
			</Transition>
		</div>

		<!-- Desktop Layout -->
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
			</aside>
			<!-- Main Content -->
			<div class="desktop-content" :class="{ 'desktop-content--pos': isPosPage }">
				<header v-if="!isPosPage && !isKitchenPage" class="desktop-header">
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
				</header>
				<main
					class="desktop-main module-content"
					:class="{ 'desktop-main--fullbleed': isPosPage || isKitchenPage }"
				>
					<section v-if="authLoading" class="auth-gate-card">
						<ManagementBearLoader :size="188" label="در حال همگام‌سازی نشست..." />
						<p class="auth-gate-title">در حال بروزرسانی نشست کاربر...</p>
						<p class="auth-card-muted">کمی صبر کنید.</p>
					</section>

					<slot v-else />
				</main>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import ManagementBearLoader from "@/components/management/ManagementBearLoader.vue";
import ManagementLoginGate from "@/components/management/ManagementLoginGate.vue";
import { getManagementSessionProfile, logoutManagementUser } from "@/utils/api";

import {
	LayoutGrid as LayoutGridIcon,
	MonitorCog as PosIcon,
	ClipboardList as OrdersIcon,
	Package as ProductsIcon,
	Tags as TagsIcon,
	Settings as SettingsIcon,
	Users as UsersIcon,
	BarChart3 as ReportsIcon,
	FileText as FileTextIcon,
	Printer as PrinterIcon,
	Layers as LayersIcon,
	Home as HomeIcon,
	Menu as MenuIcon,
	X as XIcon,
	User as UserIcon,
	ChevronDown as ChevronDownIcon,
	ChevronLeft as ChevronLeftIcon,
	ExternalLink as ExternalLinkIcon,
	Sun as SunIcon,
	Moon as MoonIcon,
	PanelRightClose as PanelRightCloseIcon,
	PanelRightOpen as PanelRightOpenIcon,
	SlidersHorizontal as SlidersIcon,
	Store as StoreIcon,
	UtensilsCrossed as KitchenIcon,
} from "lucide-vue-next";

const DESKTOP_MEDIA_QUERY = "(min-width: 1024px)";
const ZOOM_STORAGE_KEY = "restaurant.management.desktopScale";
const RAIL_STORAGE_KEY = "restaurant.management.desktopRailMode";
const THEME_STORAGE_KEY = "restaurant.management.theme";
const ZOOM_BASE_FONT_SIZE = 16;
const MOBILE_BASE_FONT_SIZE = 15;
const ZOOM_MIN = 0.85;
const ZOOM_MAX = 1.2;
const ZOOM_STEP = 0.05;

const MOBILE_PRIMARY_LINK_KEYS = [
	"management-dashboard",
	"management-pos",
	"management-orders",
	"management-products",
	"management-reports",
];

const props = defineProps({
	page: {
		type: String,
		default: "management-dashboard",
	},
	brandName: {
		type: String,
		default: "Restaurant",
	},
});

const isDesktop = ref(false);
const desktopScale = ref(1);
const railMode = ref("expanded");
const mobileMenuOpen = ref(false);
const openGroupKey = ref("");
const openGroups = ref({});

function initOpenGroup() {
	const active = menuGroups.value.find((group) =>
		group.items.some((item) => isLinkActive(item.key)),
	);
	if (active) {
		openGroupKey.value = active.key;
		openMenuGroup(active.key);
	}
}
const isDarkMode = ref(false);

let desktopMedia = null;
let desktopListener = null;
let lockedScrollY = 0;

const authLoading = ref(true);
const authSubmitting = ref(false);
const authError = ref("");
const authProfile = ref({
	user: "Guest",
	full_name: "",
	user_image: "",
	is_guest: true,
	is_staff: false,
	is_admin: false,
	roles: [],
});

const navLinks = computed(() => {
	const isStaff = authProfile.value?.is_staff || false;
	const links = [
		{
			key: "management-dashboard",
			label: "داشبورد",
			shortLabel: "خانه",
			caption: "نمای کلی",
			iconComponent: LayoutGridIcon,
			url: "/management",
			group: "overview",
		},
		{
			key: "management-pos",
			label: "POS",
			shortLabel: "POS",
			caption: "فروش حضوری",
			iconComponent: PosIcon,
			url: "/management/pos",
			group: "sales",
		},
		{
			key: "management-pos-profile",
			label: "پروفایل POS",
			shortLabel: "پروفایل",
			caption: "تنظیمات ترمینال",
			iconComponent: SlidersIcon,
			url: "/management/pos-profile",
			group: "sales",
		},
		{
			key: "management-pos-defaults",
			label: "پیش‌فرض‌های POS",
			shortLabel: "پیش‌فرض",
			caption: "مشتری و جایگاه پیش‌فرض",
			iconComponent: SettingsIcon,
			url: "/management/pos-defaults",
			group: "sales",
		},
		{
			key: "management-couriers",
			label: "پیک‌ها",
			shortLabel: "پیک",
			caption: "ناوگان و تخصیص",
			iconComponent: UsersIcon,
			url: "/management/couriers",
			group: "sales",
		},
		{
			key: "management-orders",
			label: "سفارش‌ها",
			shortLabel: "سفارش",
			caption: "وضعیت و تحویل",
			iconComponent: OrdersIcon,
			url: "/management/orders",
			group: "sales",
		},
		{
			key: "management-kitchen",
			label: "آشپزخانه",
			shortLabel: "آشپز",
			caption: "نمایشگر تولید",
			iconComponent: KitchenIcon,
			url: "/management/kitchen",
			target: "_blank",
			group: "sales",
		},
		{
			key: "management-products",
			label: "محصولات",
			shortLabel: "محصول",
			caption: "قیمت و موجودی",
			iconComponent: ProductsIcon,
			url: "/management/products",
			group: "menu",
		},
		{
			key: "management-modifier-groups",
			label: "مودیفایرها",
			shortLabel: "Modifier",
			caption: "گروه‌ها و قیمت‌گذاری",
			iconComponent: TagsIcon,
			url: "/management/modifier-groups",
			group: "menu",
		},
		{
			key: "management-menu-design",
			label: "طراحی منو",
			shortLabel: "طراحی",
			caption: "Preview و چیدمان",
			iconComponent: LayoutGridIcon,
			url: "/management/menu-design",
			group: "menu",
		},
		{
			key: "management-variant-builder",
			label: "صفت محصولات",
			shortLabel: "صفت",
			caption: "ویژگی‌ها و انواع",
			iconComponent: TagsIcon,
			url: "/management/product?variant_studio=1",
			group: "menu",
		},
		{
			key: "management-builder-templates",
			label: "قالب‌های سفارشی‌سازی",
			shortLabel: "سفارشی‌سازی",
			caption: "قالب‌ها و مراحل",
			iconComponent: TagsIcon,
			url: "/management/builder-templates",
			group: "menu",
		},
		{
			key: "management-menu-groups",
			label: "دسته‌بندی",
			shortLabel: "دسته",
			caption: "گروه‌ها و زیردسته",
			iconComponent: LayersIcon,
			url: "/management/menu-groups",
			group: "menu",
		},
		{
			key: "management-boms",
			label: "مواد اولیه",
			shortLabel: "مواد",
			caption: "فرمول و دستور ساخت",
			iconComponent: StoreIcon,
			url: "/management/boms",
			group: "inventory",
		},
		{
			key: "management-customers",
			label: "مشتریان",
			shortLabel: "مشتری",
			caption: "اطلاعات مشتریان",
			iconComponent: UsersIcon,
			url: "/management/customers",
			group: "crm",
		},
		{
			key: "management-tables",
			label: "میزها",
			shortLabel: "میزها",
			caption: "مدیریت میز و رزرو",
			iconComponent: LayoutGridIcon,
			url: "/management/tables",
			group: "sales",
		},
		{
			key: "management-reports",
			label: "گزارش عملکرد",
			shortLabel: "گزارش",
			caption: "آمار و تحلیل",
			iconComponent: ReportsIcon,
			url: "/management/reports",
			group: "reports",
		},
		{
			key: "management-report",
			label: "گزارش",
			shortLabel: "گزارش",
			caption: "نمایش گزارش تکی",
			iconComponent: FileTextIcon,
			url: "/management/reports",
			group: "reports",
		},
		{
			key: "management-print-formats",
			label: "فرمت چاپ",
			shortLabel: "چاپ",
			caption: "قالب‌های چاپ",
			iconComponent: PrinterIcon,
			url: "/management/print-formats",
			group: "reports",
		},
		{
			key: "management-home-builder",
			label: "طراحی صفحه اصلی",
			shortLabel: "صفحه اصلی",
			caption: "چیدمان و کامپوننت‌ها",
			iconComponent: LayoutGridIcon,
			url: "/management/site-settings?tab=page-builder&page=home",
			group: "settings",
		},
		{
			key: "management-site-settings",
			label: "تنظیمات سایت",
			shortLabel: "سایت",
			caption: "محتوا و تنظیمات",
			iconComponent: SettingsIcon,
			url: "/management/site-settings",
			group: "settings",
		},
		{
			key: "management-settings",
			label: "تنظیمات پنل",
			shortLabel: "تنظیمات",
			caption: "تم، رنگ و ظاهر",
			iconComponent: SlidersIcon,
			url: "/management/site-settings?stage=theme",
			group: "settings",
		},
	];

	// Hide BOM/formula section from non-staff users
	if (!isStaff) {
		return links.filter((link) => link.key !== "management-boms");
	}
	return links;
});

const menuGroups = computed(() => [
	{
		key: "overview",
		title: "نمای کلی",
		icon: LayoutGridIcon,
		items: navLinks.value.filter((link) => link.group === "overview"),
	},
	{
		key: "sales",
		title: "فروش و سفارش",
		icon: OrdersIcon,
		items: navLinks.value.filter((link) => link.group === "sales"),
	},
	{
		key: "menu",
		title: "منو و محصولات",
		icon: ProductsIcon,
		items: navLinks.value.filter((link) => link.group === "menu"),
	},
	{
		key: "inventory",
		title: "مواد و تولید",
		icon: StoreIcon,
		items: navLinks.value.filter((link) => link.group === "inventory"),
	},
	{
		key: "crm",
		title: "مشتریان",
		icon: UsersIcon,
		items: navLinks.value.filter((link) => link.group === "crm"),
	},
	{
		key: "reports",
		title: "گزارش‌ها و چاپ",
		icon: ReportsIcon,
		items: navLinks.value.filter((link) => link.group === "reports"),
	},
	{
		key: "settings",
		title: "تنظیمات",
		icon: SettingsIcon,
		items: navLinks.value.filter((link) => link.group === "settings"),
	},
]);

const mobilePrimaryLinks = computed(() =>
	navLinks.value.filter(
		(link) => MOBILE_PRIMARY_LINK_KEYS.includes(link.key) && link.key !== "management-report",
	),
);

const activeTitle = computed(() => {
	const active = navLinks.value.find((link) => isLinkActive(link.key));
	return active?.label || "پنل مدیریت";
});

const activeGroup = computed(() => {
	return menuGroups.value.find((group) => group.items.some((item) => isLinkActive(item.key)));
});

const canIncrease = computed(() => desktopScale.value < ZOOM_MAX);
const canDecrease = computed(() => desktopScale.value > ZOOM_MIN);
const isDefaultScale = computed(() => Math.abs(desktopScale.value - 1) < 0.001);
const scaleLabel = computed(() => `${Math.round(desktopScale.value * 100)}%`);
const isRailCollapsed = computed(() => railMode.value === "icons");
const isLoginPage = computed(() => props.page === "management-login");
const isPosPage = computed(() => props.page === "management-pos");
const isKitchenPage = computed(() => props.page === "kitchen");
const authGuest = computed(() => Boolean(authProfile.value?.is_guest));

const moduleThemeVars = computed(() => {
	if (isDarkMode.value) {
		return {
			"--module-500": "#f4e6d3",
			"--module-600": "#fff3e2",
			"--module-50": "rgb(244 230 211 / 0.13)",
			"--module-title-light": "#0f172a",
			"--module-title-dark": "#fff7ed",
		};
	}

	return {
		"--module-500": "#8b5e34",
		"--module-600": "#6f4726",
		"--module-50": "rgb(139 94 52 / 0.075)",
		"--module-title-light": "#0f172a",
		"--module-title-dark": "#fff7ed",
	};
});

function openMenuGroup(key) {
	const normalized = String(key || "").trim();
	if (!normalized) return;
	openGroupKey.value = normalized;
	openGroups.value = { ...openGroups.value, [normalized]: true };
}

function toggleGroup(key) {
	const normalized = String(key || "").trim();
	if (!normalized) return;
	openGroupKey.value = normalized;
	openGroups.value = { ...openGroups.value, [normalized]: !openGroups.value[normalized] };
}

function isGroupOpen(key) {
	const normalized = String(key || "").trim();
	return Boolean(normalized && openGroups.value[normalized]);
}

function isLinkActive(key) {
	if (props.page === key) return true;
	if (props.page.startsWith(key + "-")) return true;
	if (key === "management-products" && props.page.startsWith("management-product")) return true;
	if (key === "management-menu-groups" && props.page.startsWith("management-menu-group"))
		return true;
	if (key === "management-boms" && props.page.startsWith("management-bom")) return true;
	if (key === "management-reports" && props.page.startsWith("management-report")) return true;
	if (key === "management-builder-templates" && props.page === "management-builder-templates")
		return true;
	return false;
}

function closeMobileMenu() {
	mobileMenuOpen.value = false;
}

function lockBodyScroll() {
	if (typeof window === "undefined" || typeof document === "undefined") return;
	lockedScrollY = window.scrollY || window.pageYOffset || 0;
	document.documentElement.style.scrollBehavior = "auto";
	document.body.style.position = "fixed";
	document.body.style.top = `-${lockedScrollY}px`;
	document.body.style.left = "0";
	document.body.style.right = "0";
	document.body.style.width = "100%";
	document.body.style.overflow = "hidden";
}

function unlockBodyScroll() {
	if (typeof window === "undefined" || typeof document === "undefined") return;
	document.documentElement.style.scrollBehavior = "";
	document.body.style.position = "";
	document.body.style.top = "";
	document.body.style.left = "";
	document.body.style.right = "";
	document.body.style.width = "";
	document.body.style.overflow = "";
	window.scrollTo(0, lockedScrollY || 0);
	lockedScrollY = 0;
}

function toggleRailMode() {
	railMode.value = isRailCollapsed.value ? "expanded" : "icons";
}

function normalizeManagementPath(path, fallback = "/management") {
	const normalized = String(path || "").trim();
	if (!normalized.startsWith("/management")) return fallback;
	return normalized;
}

const currentLocationPath = computed(() => {
	if (typeof window === "undefined") return "/management";
	const pathname = String(window.location.pathname || "/management").trim() || "/management";
	const query = String(window.location.search || "");
	return `${pathname}${query}`;
});

const redirectTarget = computed(() => {
	const fallbackFromBoot =
		typeof window !== "undefined"
			? normalizeManagementPath(window._BOOT?.login_redirect_to, "/management")
			: "/management";

	if (typeof window === "undefined") return fallbackFromBoot;

	const params = new URLSearchParams(String(window.location.search || ""));
	const fromQuery = params.get("redirect_to") || params.get("redirect") || "";
	return normalizeManagementPath(fromQuery, fallbackFromBoot);
});

const loginUrl = computed(() => {
	const loginTarget = isLoginPage.value ? redirectTarget.value : currentLocationPath.value;
	return `/management/login?redirect_to=${encodeURIComponent(loginTarget)}`;
});

function normalizeScale(scale) {
	const numericScale = Number.isFinite(scale) ? scale : 1;
	const stepped = Math.round(numericScale / ZOOM_STEP) * ZOOM_STEP;
	return Math.min(ZOOM_MAX, Math.max(ZOOM_MIN, Number(stepped.toFixed(2))));
}

function applyDesktopScale() {
	if (typeof window === "undefined" || !isDesktop.value) return;

	const normalized = normalizeScale(desktopScale.value);

	if (normalized !== desktopScale.value) {
		desktopScale.value = normalized;
		return;
	}

	document.documentElement.style.fontSize = `${ZOOM_BASE_FONT_SIZE * normalized}px`;
	window.localStorage.setItem(ZOOM_STORAGE_KEY, String(normalized));
}

function clearDesktopScale() {
	if (typeof window === "undefined") return;
	document.documentElement.style.fontSize = "";
}

function applyMobileBaseScale() {
	if (typeof window === "undefined") return;
	document.documentElement.style.fontSize = `${MOBILE_BASE_FONT_SIZE}px`;
}

function syncDesktopState() {
	if (!desktopMedia) return;

	isDesktop.value = desktopMedia.matches;

	if (isDesktop.value) {
		applyDesktopScale();
	} else {
		applyMobileBaseScale();
	}
}

function increaseScale() {
	desktopScale.value = normalizeScale(desktopScale.value + ZOOM_STEP);
}

function decreaseScale() {
	desktopScale.value = normalizeScale(desktopScale.value - ZOOM_STEP);
}

function resetScale() {
	desktopScale.value = 1;
}

function initTheme() {
	if (typeof window === "undefined") return;

	const saved = window.localStorage.getItem(THEME_STORAGE_KEY);

	if (saved) {
		isDarkMode.value = saved === "dark";
	} else {
		isDarkMode.value = window.matchMedia?.("(prefers-color-scheme: dark)").matches || false;
	}

	applyTheme();
}

function applyTheme() {
	if (typeof document === "undefined") return;

	const root = document.documentElement;
	const body = document.body;

	root.classList.toggle("dark", isDarkMode.value);
	root.dataset.managementTheme = isDarkMode.value ? "dark" : "light";
	root.style.colorScheme = isDarkMode.value ? "dark" : "light";

	if (body) {
		body.classList.toggle("management-theme-dark", isDarkMode.value);
		body.classList.toggle("management-theme-light", !isDarkMode.value);
	}
}

function toggleTheme() {
	isDarkMode.value = !isDarkMode.value;

	if (typeof window !== "undefined") {
		window.localStorage.setItem(THEME_STORAGE_KEY, isDarkMode.value ? "dark" : "light");
	}

	applyTheme();
}

function syncAuthRoute() {
	if (typeof window === "undefined" || authLoading.value) return;

	const currentPath = `${window.location.pathname || ""}${window.location.search || ""}`;

	if (authGuest.value) {
		if (!isLoginPage.value && currentPath !== loginUrl.value) {
			window.location.replace(loginUrl.value);
		}
		return;
	}

	if (isLoginPage.value && currentPath !== redirectTarget.value) {
		window.location.replace(redirectTarget.value);
	}
}

async function refreshAuthProfile() {
	authLoading.value = true;
	authError.value = "";

	try {
		const profile = await getManagementSessionProfile();

		authProfile.value = profile || {
			user: "Guest",
			full_name: "",
			user_image: "",
			is_guest: true,
		};
	} catch {
		authProfile.value = {
			user: "Guest",
			full_name: "",
			user_image: "",
			is_guest: true,
		};
	} finally {
		authLoading.value = false;
	}
}

async function submitLogout() {
	authError.value = "";
	authSubmitting.value = true;

	try {
		await logoutManagementUser();
		await refreshAuthProfile();
	} catch (error) {
		authError.value = error.message || "خروج ناموفق بود.";
	} finally {
		authSubmitting.value = false;
	}
}

async function handleMobileLogout() {
	await submitLogout();

	if (!authError.value) {
		closeMobileMenu();
	}
}

async function handleGuestLoginSuccess() {
	await refreshAuthProfile();
	syncAuthRoute();
}

onMounted(() => {
	initTheme();

	if (typeof window !== "undefined") {
		const storedScale = Number.parseFloat(window.localStorage.getItem(ZOOM_STORAGE_KEY) || "");
		const storedRailMode = window.localStorage.getItem(RAIL_STORAGE_KEY);

		desktopScale.value = normalizeScale(storedScale);

	if (isKitchenPage.value) {
		railMode.value = "icons";
	} else {
		railMode.value = ["expanded", "icons"].includes(storedRailMode)
			? storedRailMode
			: "expanded";
	}


		desktopMedia = window.matchMedia(DESKTOP_MEDIA_QUERY);
		desktopListener = () => syncDesktopState();

		if (desktopMedia.addEventListener) {
			desktopMedia.addEventListener("change", desktopListener);
		} else if (desktopMedia.addListener) {
			desktopMedia.addListener(desktopListener);
		}

		syncDesktopState();

		if (window.history && "scrollRestoration" in window.history) {
			window.history.scrollRestoration = "manual";
		}

		window.scrollTo({ top: 0, behavior: "auto" });

		window.requestAnimationFrame(() => {
			window.scrollTo({ top: 0, behavior: "auto" });
		});
	}

	refreshAuthProfile();
	initOpenGroup();
});

watch(
	activeGroup,
	(group) => {
		if (group?.key) {
			openMenuGroup(group.key);
		}
	},
	{ immediate: true },
);

watch(desktopScale, () => {
	applyDesktopScale();
});

watch(railMode, (value) => {
	if (typeof window === "undefined") return;
	window.localStorage.setItem(RAIL_STORAGE_KEY, value);
});

watch(isDesktop, (desktop) => {
	if (desktop) closeMobileMenu();
});

watch(mobileMenuOpen, (open) => {
	if (open) {
		lockBodyScroll();
	} else {
		unlockBodyScroll();
	}
});

watch([authLoading, authGuest, isLoginPage, redirectTarget], () => {
	syncAuthRoute();
});

onBeforeUnmount(() => {
	if (desktopMedia && desktopListener) {
		if (desktopMedia.removeEventListener) {
			desktopMedia.removeEventListener("change", desktopListener);
		} else if (desktopMedia.removeListener) {
			desktopMedia.removeListener(desktopListener);
		}
	}

	unlockBodyScroll();

	if (typeof document !== "undefined") {
		document.body?.classList.remove("management-theme-dark", "management-theme-light");
		document.documentElement.removeAttribute("data-management-theme");
		document.documentElement.style.colorScheme = "";
	}

	clearDesktopScale();
});
</script>

<style scoped>
.management-layout,
.management-auth-shell {
	/* Legacy mappings to prevent breaking POS/Products/Dashboard */
	--bg-page: var(--mg-bg-page);
	--bg-card: var(--mg-bg-surface);
	--bg-soft: var(--mg-bg-soft);
	--bg-subtle: var(--mg-bg-page);
	--border: var(--mg-border);
	--border-strong: var(--mg-text-muted);
	--text: var(--mg-text-main);
	--muted: var(--mg-text-muted);
	--muted-2: var(--mg-olive);
	--danger: var(--mg-danger);
	--shadow: var(--mg-shadow-md);
	--shadow-sm: var(--mg-shadow-sm);
	--palette-deep-sapphire: var(--mg-primary);
	--palette-deep-sapphire-rgb: 201, 120, 82;
	--palette-june-bud: var(--mg-olive);
	--palette-june-bud-rgb: 138, 139, 99;
	--palette-deep-saffron: var(--mg-border);
	--palette-deep-saffron-rgb: 216, 200, 180;
	--palette-eggshell: var(--mg-bg-surface);
	--palette-eggshell-rgb: 251, 247, 241;

	min-height: 100vh;
	background: var(--mg-bg-page);
	color: var(--mg-text-main);
}

.desktop-layout {
	display: none;
}

.mobile-layout {
	display: flex;
	flex-direction: column;
	min-height: 100vh;
	padding-bottom: 5.5rem;
}

.mobile-header {
	height: 3.75rem;
	background: var(--mg-bg-surface);
	border-bottom: 1px solid var(--mg-border-light);
	display: flex;
	align-items: center;
	justify-content: space-between;
	padding: 0 0.5rem;
	position: sticky;
	top: 0;
	z-index: 50;
}

.mobile-brand {
	display: flex;
	align-items: center;
	gap: 0.5rem;
	text-decoration: none;
	color: var(--mg-text-main);
}

.brand-mark {
	width: 2.2rem;
	height: 2.2rem;
	border-radius: 8px;
	background: var(--mg-bg-page);
	display: grid;
	place-items: center;
	overflow: hidden;
}
.brand-image { width: 100%; height: 100%; object-fit: contain; }

.mobile-brand-text {
	display: grid;
}
.mobile-brand-text strong { font-size: 0.95rem; font-weight: 800; }
.mobile-brand-text small { font-size: 0.7rem; color: var(--mg-text-muted); }

.icon-button {
	width: 2.75rem;
	height: 2.75rem;
	border-radius: 8px;
	border: none;
	background: transparent;
	color: var(--mg-text-muted);
	display: grid;
	place-items: center;
}
.icon-button:hover { background: var(--mg-bg-soft); color: var(--mg-text-main); }

.mobile-bottom-nav {
	position: fixed;
	bottom: 0;
	left: 0;
	right: 0;
	height: 4.5rem;
	background: var(--mg-bg-surface);
	border-top: 1px solid var(--mg-border-light);
	display: flex;
	align-items: center;
	justify-content: space-around;
	padding: 0 0.5rem max(env(safe-area-inset-bottom), 0.5rem);
	z-index: 50;
}

.bottom-nav-item {
	display: flex;
	flex-direction: column;
	align-items: center;
	gap: 0.25rem;
	color: var(--mg-text-muted);
	text-decoration: none;
	padding: 0.5rem;
	border-radius: 8px;
}
.bottom-nav-item.active {
	color: var(--mg-primary);
	font-weight: 800;
}
.bottom-nav-item span { font-size: 0.7rem; }

.mobile-overlay {
	position: fixed;
	inset: 0;
	background: rgba(47, 36, 29, 0.6);
	backdrop-filter: blur(2px);
	z-index: 100;
}

.mobile-sidebar {
	position: fixed;
	top: 0; right: 0; bottom: 0;
	width: 85vw;
	max-width: 320px;
	background: var(--mg-bg-surface);
	z-index: 110;
	display: flex;
	flex-direction: column;
}

.mobile-sidebar-header {
	height: 4.5rem;
	border-bottom: 1px solid var(--mg-border-light);
	display: flex;
	align-items: center;
	justify-content: space-between;
	padding: 0 1rem;
}
.sidebar-title { display: flex; align-items: center; gap: 0.75rem; }
.sidebar-title strong { font-weight: 800; color: var(--mg-text-main); }
.sidebar-title small { font-size: 0.75rem; color: var(--mg-text-muted); }

.mobile-utility-zone {
	margin-top: auto;
	padding: 1rem;
	border-top: 1px solid var(--mg-border-light);
	display: grid;
	gap: 0.5rem;
	background: var(--mg-bg-page);
}
.utility-link {
	display: flex;
	align-items: center;
	gap: 0.75rem;
	padding: 0.75rem;
	border-radius: 8px;
	color: var(--mg-text-main);
	text-decoration: none;
	font-size: 0.9rem;
	font-weight: 700;
	background: transparent;
	border: none;
	width: 100%;
}
.utility-link:hover { background: var(--mg-bg-soft); }
.text-danger { color: var(--mg-danger); }

/* Desktop */
@media (min-width: 1024px) {
	.mobile-layout { display: none; }
	.desktop-layout {
		display: flex;
		min-height: 100vh;
	}

	.desktop-sidebar {
		width: 16rem;
		transition: width 0.2s;
		background: var(--mg-bg-surface);
		border-left: 1px solid var(--mg-border-light);
		display: flex;
		flex-direction: column;
	}

	.sidebar-logo-block {
		height: 4.5rem;
		padding: 0 1.25rem;
		display: flex;
		align-items: center;
		border-bottom: 1px solid var(--mg-border-light);
	}

	.rail-brand {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		text-decoration: none;
		color: var(--mg-text-main);
		overflow: hidden;
	}
	.rail-brand-mark {
		width: 2.2rem; height: 2.2rem;
		border-radius: 8px;
		background: var(--mg-bg-page);
		display: grid; place-items: center; flex-shrink: 0;
	}
	.brand-image-lg { width: 1.6rem; }
	
	.rail-brand-text { display: grid; }
	.rail-brand-text strong { font-weight: 800; font-size: 1rem; }
	.rail-brand-text small { font-size: 0.75rem; color: var(--mg-text-muted); }
	
	.desktop-content {
		flex: 1;
		display: flex;
		flex-direction: column;
		min-width: 0;
	}

	.desktop-header {
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
	.header-auth-btn:hover { background: var(--mg-danger-bg); }

	.desktop-main {
		flex: 1;
		padding: 1.5rem 2rem;
		overflow-y: auto;
	}
	.desktop-main > :deep(*) {
		max-width: 1400px;
		margin-inline: auto;
	}

	.desktop-main--fullbleed { padding: 0; }
	
	
	.rail-toggle-btn { margin-right: auto; }
	.rail-collapsed .desktop-sidebar { width: 5.5rem; }
	.rail-collapsed .rail-brand-text,
	.rail-collapsed .group-title-rail,
	.rail-collapsed .item-label { display: none; }
	.rail-collapsed .nav-item { justify-content: center; padding: 0.8rem; }
	
	.sidebar-logo-block { justify-content: space-between; }

	/* Kitchen Page Specific Sidebar Tweaks (Use rail-collapsed mostly, but we can keep these as fallback or let the user decide.
       Actually, let's let KDS default to collapsed via JS, but user can open it) */
	.management-layout--kitchen .desktop-header {
		display: none;
	}
	.management-layout--kitchen .desktop-main {
		padding: 0;
	}
}

/* Nav Styles */

.accordion-nav {
	flex: 1;
	overflow-y: auto;
	padding: 1.5rem 1rem;
	display: flex;
	flex-direction: column;
	gap: 1.5rem;
}

.nav-group {
	display: flex;
	flex-direction: column;
	gap: 0.5rem;
}

.group-title-rail {
	font-size: 0.75rem;
	color: var(--mg-olive);
	font-weight: 800;
	text-transform: uppercase;
	letter-spacing: 0.05em;
	padding-right: 0.5rem;
	margin-bottom: 0.25rem;
}

.group-items {
	display: flex;
	flex-direction: column;
	gap: 0.15rem;
}

.nav-item {
	display: flex;
	align-items: center;
	gap: 0.75rem;
	padding: 0.65rem 0.75rem;
	text-decoration: none;
	color: var(--mg-text-muted);
	border-radius: var(--mg-radius-sm);
	transition: all 0.2s;
}

.nav-item:hover { color: var(--mg-text-main); background: var(--mg-bg-page); }
.nav-item.active { 
	color: var(--mg-primary); 
	font-weight: 800; 
	background: var(--mg-bg-page); 
	box-shadow: -3px 0 0 0 var(--mg-primary) inset;
}

.item-icon {
	color: inherit;
	display: flex;
}

.item-label strong { font-size: 0.9rem; }

/* Transitions */
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
.slide-right-enter-active, .slide-right-leave-active { transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1); }
.slide-right-enter-from, .slide-right-leave-to { transform: translateX(100%); }

.icon-sm { width: 18px; height: 18px; }
.icon-md { width: 22px; height: 22px; }
</style>
