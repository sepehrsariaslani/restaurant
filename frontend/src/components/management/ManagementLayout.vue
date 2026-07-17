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
							<span class="brand-mark">
								<img
									class="brand-image"
									src="/NooshYar%20Image.png"
									alt="NooshYar"
								/>
							</span>
							<div>
								<strong>منوی مدیریت</strong>
								<small>{{ brandName }}</small>
							</div>
						</div>

						<button type="button" class="icon-button" @click="closeMobileMenu">
							<XIcon class="icon-md" />
						</button>
					</div>

					<nav class="accordion-nav">
						<div
							v-for="group in menuGroups"
							:key="`mobile-group-${group.key}`"
							class="nav-group"
							:class="{ open: isGroupOpen(group.key) }"
						>
							<button
								type="button"
								class="group-button"
								:class="{ active: isGroupOpen(group.key) }"
								:aria-expanded="isGroupOpen(group.key)"
								@click="toggleGroup(group.key)"
							>
								<span class="group-icon">
									<component :is="group.icon" class="icon-sm" />
								</span>
								<span>{{ group.title }}</span>
								<ChevronDownIcon
									class="icon-sm chevron"
									:class="{ rotated: isGroupOpen(group.key) }"
								/>
							</button>

							<div v-if="isGroupOpen(group.key)" class="group-items">
								<a
									v-for="item in group.items"
									:key="`mobile-item-${item.key}`"
									:href="item.url"
									:target="item.target || '_self'"
									class="nav-item"
									:class="{ active: isLinkActive(item.key) }"
									@click="closeMobileMenu"
								>
									<span class="item-icon">
										<component :is="item.iconComponent" class="icon-sm" />
									</span>
									<span>{{ item.label }}</span>
									<ChevronLeftIcon
										v-if="isLinkActive(item.key)"
										class="icon-sm active-chevron"
									/>
								</a>
							</div>
						</div>
					</nav>

					<section class="sidebar-auth-card">
						<template v-if="authLoading">
							<p class="muted">در حال بررسی وضعیت کاربر...</p>
						</template>

						<template v-else-if="authGuest">
							<p class="auth-title">وضعیت کاربر: مهمان</p>
							<a class="primary-pill-link" :href="loginUrl" @click="closeMobileMenu">
								ورود به حساب مدیریت
							</a>
						</template>

						<template v-else>
							<div class="user-row">
								<span class="user-avatar">
									<UserIcon class="icon-sm" />
								</span>
								<div>
									<strong>{{
										authProfile.full_name || authProfile.user
									}}</strong>
									<small>{{ authProfile.user }}</small>
								</div>
							</div>

							<button
								type="button"
								class="secondary-btn full"
								:disabled="authSubmitting"
								@click="handleMobileLogout"
							>
								{{ authSubmitting ? "در حال خروج..." : "خروج" }}
							</button>
						</template>

						<p v-if="authError" class="auth-error">
							{{ authError }}
						</p>
					</section>
				</aside>
			</Transition>
		</div>

		<!-- Desktop Layout -->
		<div class="desktop-layout">
			<!-- Sidebar -->
			<aside class="desktop-sidebar">
				<!-- Sidebar Top -->
				<div class="sidebar-logo-block">
					<button
						type="button"
						class="rail-mini-toggle"
						:title="isRailCollapsed ? 'باز کردن منو' : 'کوچک کردن منو'"
						@click="toggleRailMode"
					>
						<PanelRightCloseIcon v-if="!isRailCollapsed" class="icon-sm" />
						<PanelRightOpenIcon v-else class="icon-sm" />
					</button>

					<a class="rail-brand" href="/management">
						<span class="rail-brand-mark">
							<img
								class="brand-image brand-image-lg"
								src="/NooshYar%20Image.png"
								alt="NooshYar"
							/>
						</span>

						<span class="rail-brand-text">
							<strong>نوش‌یار</strong>
							<small>پنل مدیریت رستوران</small>
						</span>
					</a>
				</div>

				<!-- Accordion Nav -->
				<nav class="accordion-nav desktop-nav">
					<div
						v-for="group in menuGroups"
						:key="group.key"
						class="nav-group"
						:class="{ open: isGroupOpen(group.key) }"
					>
						<button
							type="button"
							class="group-button"
							:class="{ active: isGroupOpen(group.key) }"
							:aria-expanded="isGroupOpen(group.key)"
							@click="toggleGroup(group.key)"
						>
							<span class="group-icon">
								<component :is="group.icon" class="icon-sm" />
							</span>

							<span class="group-title">{{ group.title }}</span>

							<ChevronDownIcon
								class="icon-sm chevron"
								:class="{ rotated: isGroupOpen(group.key) }"
							/>
						</button>

						<div v-if="isGroupOpen(group.key)" class="group-items">
							<a
								v-for="item in group.items"
								:key="item.key"
								:href="item.url"
								:target="item.target || '_self'"
								class="nav-item"
								:class="{ active: isLinkActive(item.key) }"
								:title="item.label"
							>
								<span class="item-icon">
									<component :is="item.iconComponent" class="icon-sm" />
								</span>

								<span class="item-label">
									<strong>{{ item.label }}</strong>
									<small>{{ item.caption }}</small>
								</span>

								<ChevronLeftIcon
									v-if="isLinkActive(item.key)"
									class="icon-sm active-chevron"
								/>
							</a>
						</div>
					</div>
				</nav>

				<!-- Sidebar Footer -->
				<div class="sidebar-footer">
					<a class="customer-site-link" href="/menu" title="مشاهده سایت مشتری">
						<ExternalLinkIcon class="icon-sm" />
						<span>مشاهده سایت مشتری</span>
					</a>

					<section class="auth-panel">
						<template v-if="authLoading">
							<p class="muted">در حال بررسی وضعیت کاربر...</p>
						</template>

						<template v-else-if="authGuest">
							<p class="auth-title">وضعیت کاربر: مهمان</p>
							<p class="muted">برای مشاهده داشبورد، ابتدا وارد حساب شوید.</p>
							<a class="primary-pill-link" :href="loginUrl"> ورود </a>
						</template>

						<template v-else>
							<div class="user-row">
								<span class="user-avatar">
									<UserIcon class="icon-sm" />
								</span>
								<div>
									<strong>{{
										authProfile.full_name || authProfile.user
									}}</strong>
									<small>{{ authProfile.user }}</small>
								</div>
							</div>

							<button
								class="secondary-btn full"
								type="button"
								:disabled="authSubmitting"
								@click="submitLogout"
							>
								{{ authSubmitting ? "در حال خروج..." : "خروج" }}
							</button>
						</template>

						<p v-if="authError" class="auth-error">
							{{ authError }}
						</p>
					</section>

					<button type="button" class="theme-toggle" @click="toggleTheme">
						<SunIcon v-if="isDarkMode" class="icon-sm" />
						<MoonIcon v-else class="icon-sm" />
						<span>{{ isDarkMode ? "حالت روز" : "حالت شب" }}</span>
					</button>

					<div class="desktop-zoom">
						<button
							type="button"
							class="zoom-btn"
							:disabled="!canIncrease"
							@click="increaseScale"
						>
							A+
						</button>
						<span class="zoom-level">{{ scaleLabel }}</span>
						<button
							type="button"
							class="zoom-btn"
							:disabled="!canDecrease"
							@click="decreaseScale"
						>
							A-
						</button>
						<button
							type="button"
							class="zoom-reset"
							:disabled="isDefaultScale"
							@click="resetScale"
						>
							پیش‌فرض
						</button>
					</div>
				</div>
			</aside>

			<!-- Main Content -->
			<div class="desktop-content" :class="{ 'desktop-content--pos': isPosPage }">
				<header v-if="!isPosPage" class="desktop-header">
					<div class="page-title-wrap">
						<small>داشبورد عملیاتی</small>
						<h1>{{ activeTitle }}</h1>
					</div>

					<div class="desktop-header-actions">
						<a class="header-site-link" href="/menu"> سایت مشتری </a>

						<template v-if="!authLoading">
							<a v-if="authGuest" class="header-auth-btn" :href="loginUrl"> ورود </a>

							<template v-else>
								<div class="header-user-chip" :title="authProfile.user">
									<strong>{{
										authProfile.full_name || authProfile.user
									}}</strong>
									<small>{{ authProfile.user }}</small>
								</div>

								<button
									class="header-auth-btn muted"
									type="button"
									@click="submitLogout"
								>
									خروج
								</button>
							</template>
						</template>
					</div>
				</header>

				<main
					class="desktop-main module-content"
					:class="{ 'desktop-main--fullbleed': isPosPage }"
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
		railMode.value = ["expanded", "icons"].includes(storedRailMode)
			? storedRailMode
			: "expanded";

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
	/* Core Earthy Theme Backgrounds */
	--bg-page: #FDFBF7; /* Muted parchment/cream */
	--bg-card: #ffffff;
	--bg-soft: #F4EFE6; /* Dusty beige/sand */
	--bg-subtle: #FDFBF7;
	--border: #E8D1A7; /* Golden Batter */
	--border-strong: #9D9167; /* Olive */
	
	/* Core Earthy Theme Typography */
	--text: #442D1C; /* Cowhide Cocoa */
	--muted: #84592B; /* Toasted Caramel */
	--muted-2: #9D9167; /* Olive Harvest */
	--danger: #A33D3D; /* Deep Semantic Red */
	
	--shadow: 0 18px 44px rgba(68, 45, 28, 0.07);
	--shadow-sm: 0 8px 22px rgba(68, 45, 28, 0.045);

	/* Palette Overrides mapped to Earthy Theme */
	--palette-deep-sapphire: #743014; /* Spiced Wine / Terracotta */
	--palette-deep-sapphire-rgb: 116 48 20;
	--palette-june-bud: #9D9167; /* Olive Harvest */
	--palette-june-bud-rgb: 157 145 103;
	--palette-deep-saffron: #84592B; /* Toasted Caramel */
	--palette-deep-saffron-rgb: 132 89 43;
	--palette-gold: #E8D1A7; /* Golden Batter */
	--palette-gold-rgb: 232 209 167;
	--palette-eggshell: #ffffff;
	--palette-eggshell-rgb: 255 255 255;
	--theme-surface-alt: var(--bg-soft);
	--theme-background: var(--bg-page);
	--theme-border: var(--border);
	--glass-bg: #ffffff;
	--glass-border: var(--border);
	--glass-highlight: rgb(255 255 255 / 0.95);
	--accent-green: #8b5e34;
	--accent-green80: rgb(139 94 52 / 0.86);
	--accent-green60: rgb(139 94 52 / 0.62);
	--accent-green40: rgb(139 94 52 / 0.12);
	--accent-green20: rgb(139 94 52 / 0.075);
	--accent-cream: #f4e6d3;
	--accent-cream80: rgb(244 230 211 / 0.88);
	--accent-cream50: rgb(244 230 211 / 0.52);
	--accent-cream20: rgb(244 230 211 / 0.24);
	--accent-gold: #b8793f;
	--accent-gold80: rgb(184 121 63 / 0.82);
	--accent-gold50: rgb(184 121 63 / 0.45);
	--accent-gold20: rgb(184 121 63 / 0.1);
	--accent: #8b5e34;
	--text-primary: var(--text);
	--text-secondary: #334155;
	--text-muted: var(--muted);
	--management-ink: var(--text);
	--ink-900: #0f172a;
	--ink-800: #1e293b;
	--ink-700: #334155;
	--ink-600: #64748b;
	--ink-400: #94a3b8;
	--ink-200: #e2e8f0;
	--success: #16a34a;
	--success-rgb: 22 163 74;
	--warning: #d97706;
	--warning-rgb: 217 119 6;
	--shadow-deep: 0 24px 56px rgb(15 23 42 / 0.1);
	--shadow-soft: 0 12px 28px rgb(15 23 42 / 0.07);
	--radius-xl: 28px;
	--radius-lg: 18px;
	--radius-md: 14px;
	--pos-primary-color: #6f4a31;
	--pos-primary-rgb: 111 74 49;
	--pos-accent-color: #c98d42;
	--pos-accent-rgb: 201 141 66;
	--pos-success-color: #0b7d4a;
	--pos-success-rgb: 11 125 74;
	--pos-danger-color: #ab3535;
	--pos-danger-rgb: 171 53 53;
	--pos-warning-color: #f59e0b;
	--pos-warning-rgb: 245 158 11;
	--pos-surface-color: #ffffff;

	min-height: 100vh;
	background: var(--bg-page);
	color: var(--text);
}

:global(body.management-theme-dark) {
	background: #020617;
	color: #f8fafc;
}

:global(body.management-theme-light) {
	background: #f8fafc;
	color: #0f172a;
}

.management-layout.dark,
.management-auth-shell.dark,
:global(.dark) .management-layout,
:global(.dark) .management-auth-shell {
	--bg-page: #020617;
	--bg-card: #0f172a;
	--bg-soft: #111827;
	--bg-subtle: #1e293b;
	--border: #1f2937;
	--border-strong: #334155;
	--text: #f8fafc;
	--muted: #cbd5e1;
	--muted-2: #94a3b8;
	--shadow: 0 22px 54px rgb(0 0 0 / 0.38);
	--shadow-sm: 0 10px 28px rgb(0 0 0 / 0.28);
	--palette-deep-sapphire: #f4e6d3;
	--palette-deep-sapphire-rgb: 244 230 211;
	--palette-june-bud: #f4e6d3;
	--palette-june-bud-rgb: 244 230 211;
	--palette-deep-saffron: #ffd7a8;
	--palette-deep-saffron-rgb: 255 215 168;
	--glass-bg: #0f172a;
	--glass-border: #1f2937;
	--glass-highlight: rgb(255 255 255 / 0.08);
	--theme-surface-alt: #111827;
	--theme-background: #020617;
	--theme-border: #1f2937;
	--accent-green: #f4e6d3;
	--accent-green80: rgb(244 230 211 / 0.9);
	--accent-green60: rgb(244 230 211 / 0.7);
	--accent-green40: rgb(244 230 211 / 0.2);
	--accent-green20: rgb(244 230 211 / 0.11);
	--accent-cream: #f4e6d3;
	--accent-cream80: rgb(244 230 211 / 0.88);
	--accent-cream50: rgb(244 230 211 / 0.48);
	--accent-cream20: rgb(244 230 211 / 0.14);
	--accent-gold: #ffd7a8;
	--accent-gold80: rgb(255 215 168 / 0.82);
	--accent-gold50: rgb(255 215 168 / 0.45);
	--accent-gold20: rgb(255 215 168 / 0.12);
	--accent: #f4e6d3;
	--text-primary: var(--text);
	--text-secondary: #e2e8f0;
	--text-muted: var(--muted);
	--management-ink: var(--text);
	--ink-900: #f8fafc;
	--ink-800: #e2e8f0;
	--ink-700: #cbd5e1;
	--ink-600: #94a3b8;
	--ink-400: #64748b;
	--ink-200: #334155;
	--pos-primary-color: #f4e6d3;
	--pos-primary-rgb: 244 230 211;
	--pos-accent-color: #d4a169;
	--pos-accent-rgb: 212 161 105;
	--pos-success-color: #34d399;
	--pos-success-rgb: 52 211 153;
	--pos-danger-color: #f87171;
	--pos-danger-rgb: 248 113 113;
	--pos-warning-color: #fbbf24;
	--pos-warning-rgb: 251 191 36;
	--pos-surface-color: #0f172a;
}

/* Auth */
.management-auth-shell {
	display: grid;
	place-items: center;
	padding: 1rem;
}

.management-auth-card,
.auth-gate-card {
	width: min(440px, 100%);
	border: 1px solid var(--border);
	border-radius: 22px;
	background: color-mix(in srgb, var(--bg-card) 94%, transparent);
	box-shadow: var(--shadow);
	padding: 1.1rem;
	display: grid;
	gap: 0.45rem;
	justify-items: center;
	text-align: center;
}

.auth-card-title,
.auth-gate-title {
	margin: 0;
	font-size: 1rem;
	font-weight: 900;
	color: var(--text);
}

.auth-card-muted,
.muted {
	margin: 0;
	color: var(--muted);
	font-size: 0.78rem;
}

.auth-error {
	margin: 0;
	color: var(--danger);
	font-size: 0.75rem;
}

.auth-error--login {
	margin-top: 0.75rem;
}

/* Common */
.icon-sm {
	width: 1rem;
	height: 1rem;
}

.icon-md {
	width: 1.35rem;
	height: 1.35rem;
}

.brand-image {
	width: 1.35rem;
	height: 1.35rem;
	object-fit: cover;
	border-radius: 0.55rem;
}

.brand-image-lg {
	width: 1.55rem;
	height: 1.55rem;
}

.brand-mark,
.rail-brand-mark {
	width: 2.45rem;
	height: 2.45rem;
	border-radius: 0.8rem;
	background: var(--bg-soft);
	border: 1px solid var(--border);
	display: inline-flex;
	align-items: center;
	justify-content: center;
	box-shadow: none;
	flex-shrink: 0;
}

.icon-button {
	width: 2.75rem;
	height: 2.75rem;
	border: 1px solid var(--border);
	border-radius: 0.75rem;
	display: inline-flex;
	align-items: center;
	justify-content: center;
	background: var(--bg-card);
	color: var(--muted);
	cursor: pointer;
	transition: 0.18s ease;
}

.icon-button:hover {
	background: var(--bg-soft);
	border-color: var(--border);
	color: var(--text);
}

/* Mobile */
.mobile-layout {
	min-height: 100vh;
	display: flex;
	flex-direction: column;
}

.mobile-header {
	min-height: 4.35rem;
	padding: 0 0.9rem;
	border-bottom: 1px solid var(--border);
	background: color-mix(in srgb, var(--bg-card) 98%, transparent);
	backdrop-filter: blur(10px);
	display: flex;
	align-items: center;
	justify-content: space-between;
	gap: 0.75rem;
	position: sticky;
	top: 0;
	z-index: 80;
}

.mobile-brand {
	min-width: 0;
	display: inline-flex;
	align-items: center;
	gap: 0.55rem;
	color: var(--text);
}

.mobile-brand-text {
	display: grid;
	gap: 0.04rem;
	min-width: 0;
}

.mobile-brand-text strong {
	font-size: 0.88rem;
}

.mobile-brand-text small {
	color: var(--muted);
	font-size: 0.68rem;
}

.mobile-main {
	flex: 1;
	overflow: auto;
	overflow-x: hidden;
	padding: 0.85rem clamp(0.7rem, 3vw, 1rem) 5.75rem;
	width: 100%;
	max-width: 100vw;
}

.mobile-bottom-nav {
	position: fixed;
	right: 0;
	left: 0;
	bottom: 0;
	z-index: 90;
	height: calc(4.55rem + env(safe-area-inset-bottom));
	padding-bottom: env(safe-area-inset-bottom);
	background: color-mix(in srgb, var(--bg-card) 96%, transparent);
	border-top: 1px solid var(--border);
	display: flex;
	justify-content: space-around;
	align-items: center;
	backdrop-filter: blur(10px);
}

.bottom-nav-item {
	height: 100%;
	min-width: 4.45rem;
	min-height: 3.75rem;
	border-radius: 8px;
	padding: 0.38rem 0.42rem;
	display: grid;
	justify-items: center;
	align-content: center;
	gap: 0.25rem;
	color: var(--muted);
	font-size: 0.68rem;
	touch-action: manipulation;
}

.bottom-nav-item.active {
	color: var(--module-600);
	background: var(--module-50);
	font-weight: 900;
}

.management-layout.dark .bottom-nav-item.active,
:global(.dark) .bottom-nav-item.active {
	color: var(--module-title-dark);
}

.mobile-overlay {
	position: fixed;
	inset: 0;
	height: 100dvh;
	z-index: 110;
	background: rgb(2 6 23 / 0.56);
	backdrop-filter: blur(2px);
}

.mobile-sidebar {
	position: fixed;
	inset-block: 0;
	top: 0;
	right: 0;
	bottom: 0;
	z-index: 120;
	width: min(94vw, 410px);
	height: 100dvh;
	max-height: 100dvh;
	background: var(--bg-card);
	border-left: 1px solid var(--border);
	border-radius: 16px 0 0 16px;
	display: flex;
	flex-direction: column;
	box-shadow: -24px 0 56px rgb(15 23 42 / 0.18);
	overflow: hidden;
}

.mobile-sidebar-header {
	position: sticky;
	top: 0;
	z-index: 2;
	min-height: 4.6rem;
	padding: 0.85rem 1rem;
	border-bottom: 1px solid var(--border);
	background: var(--bg-card);
	display: flex;
	align-items: center;
	justify-content: space-between;
}

.mobile-sidebar .accordion-nav {
	flex: 1;
	min-height: 0;
	padding: 0.85rem;
	overflow-y: auto;
	overscroll-behavior: contain;
}

.mobile-sidebar .group-button {
	min-height: 3.02rem;
	padding-block: 0.48rem;
}

.mobile-sidebar .nav-item {
	min-height: 2.82rem;
}

.sidebar-title {
	display: inline-flex;
	align-items: center;
	gap: 0.75rem;
}

.sidebar-title div {
	display: grid;
}

.sidebar-title strong {
	font-size: 0.98rem;
}

.sidebar-title small {
	color: var(--muted);
	font-size: 0.74rem;
}

/* Desktop */
.desktop-layout {
	display: none;
}

@media (min-width: 1024px) {
	.mobile-layout {
		display: none;
	}

	.desktop-layout {
		min-height: 100vh;
		display: flex;
	}

	.desktop-sidebar {
		width: 18.25rem;
		height: 100vh;
		position: sticky;
		top: 0;
		border-left: 1px solid var(--border);
		background: color-mix(in srgb, var(--bg-card) 96%, var(--bg-page));
		display: flex;
		flex-direction: column;
		box-shadow: -10px 0 32px rgb(15 23 42 / 0.04);
		transition:
			width 0.22s ease,
			box-shadow 0.22s ease;
	}

	.management-layout.rail-collapsed .desktop-sidebar {
		width: 5.8rem;
	}

	.sidebar-logo-block {
		min-height: 5.35rem;
		padding: 0.95rem 1rem;
		border-bottom: 1px solid var(--border);
		display: flex;
		align-items: center;
		gap: 0.7rem;
	}

	.rail-mini-toggle {
		width: 2.45rem;
		height: 2.45rem;
		flex-shrink: 0;
		border: 1px solid var(--border);
		border-radius: 0.75rem;
		background: var(--bg-card);
		color: var(--text);
		cursor: pointer;
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}

	.rail-brand {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		color: var(--text);
		min-width: 0;
	}

	.rail-brand-text {
		display: grid;
		gap: 0.1rem;
		min-width: 0;
	}

	.rail-brand-text strong {
		font-size: 1rem;
	}

	.rail-brand-text small {
		color: var(--muted);
		font-size: 0.72rem;
	}

	.management-layout.rail-collapsed .rail-brand {
		justify-content: center;
	}

	.management-layout.rail-collapsed .sidebar-logo-block {
		justify-content: center;
		padding-inline: 0.55rem;
	}

	.management-layout.rail-collapsed .rail-mini-toggle {
		width: 2.65rem;
		height: 2.65rem;
	}

	.management-layout.rail-collapsed .rail-brand-text,
	.management-layout.rail-collapsed .group-title,
	.management-layout.rail-collapsed .chevron,
	.management-layout.rail-collapsed .item-label,
	.management-layout.rail-collapsed .active-chevron,
	.management-layout.rail-collapsed .customer-site-link span,
	.management-layout.rail-collapsed .auth-panel,
	.management-layout.rail-collapsed .theme-toggle span,
	.management-layout.rail-collapsed .desktop-zoom {
		display: none;
	}

	.desktop-content {
		flex: 1;
		min-width: 0;
		display: flex;
		flex-direction: column;
	}

	.desktop-content--pos {
		background: var(--bg-page);
	}

	.desktop-header {
		height: 4.6rem;
		border-bottom: 1px solid var(--border);
		background: color-mix(in srgb, var(--bg-card) 96%, transparent);
		padding: 0 1.65rem;
		display: flex;
		align-items: center;
		justify-content: space-between;
		backdrop-filter: blur(10px);
		position: sticky;
		top: 0;
		z-index: 70;
	}

	.page-title-wrap {
		display: grid;
		gap: 0.08rem;
	}

	.page-title-wrap small {
		color: var(--muted);
		font-size: 0.72rem;
	}

	.page-title-wrap h1 {
		margin: 0;
		color: var(--module-title-light);
		font-size: 1.04rem;
		font-weight: 900;
	}

	.management-layout.dark .page-title-wrap h1,
	:global(.dark) .page-title-wrap h1 {
		color: var(--module-title-dark);
	}

	.desktop-header-actions {
		display: inline-flex;
		align-items: center;
		gap: 0.55rem;
	}

	.desktop-main {
		flex: 1;
		overflow: auto;
	}

	.desktop-main > :deep(*) {
		max-width: 1320px;
		margin-inline: auto;
	}

	.desktop-main--fullbleed {
		padding: 0;
	}

	.desktop-main--fullbleed > :deep(*) {
		max-width: none;
		margin-inline: 0;
		width: 100%;
	}
}

.module-content :deep(.glass-card),
.module-content :deep(.surface-card),
.module-content :deep(.hero-card),
.module-content :deep(.management-surface-card),
.module-content :deep(.table-shell),
.module-content :deep(.filter-panel),
.module-content :deep(.builder-step-card),
.module-content :deep(.report-card),
.module-content :deep(.kpi-card),
.module-content :deep(.line-card),
.module-content :deep(.designer-panel),
.module-content :deep(.designer-preview),
.module-content :deep(.preview-category-card),
.module-content :deep(.editable-table) {
	border-color: var(--border) !important;
	background: var(--bg-card) !important;
	color: var(--text) !important;
	box-shadow: var(--shadow-sm) !important;
}

.module-content :deep(.hero-card),
.module-content :deep(.surface-card.tone-soft),
.module-content :deep(.surface-card.tone-accent),
.module-content :deep(.glass-card.tone-accent),
.module-content :deep(.menu-preview-frame) {
	background: linear-gradient(
		180deg,
		var(--bg-card),
		color-mix(in srgb, var(--bg-card) 92%, var(--bg-soft))
	) !important;
}

.module-content :deep(.surface-head h3),
.module-content :deep(.hero-card h2),
.module-content :deep(.section-title),
.module-content :deep(h1),
.module-content :deep(h2),
.module-content :deep(h3) {
	color: var(--text) !important;
}

.module-content :deep(.muted),
.module-content :deep(.surface-head p),
.module-content :deep(.hero-card p),
.module-content :deep(.hint),
.module-content :deep(.field-help),
.module-content :deep(.category-copy small),
.module-content :deep(.product-copy small),
.module-content :deep(.preview-category-copy p),
.module-content :deep(small) {
	color: var(--muted) !important;
}

.module-content :deep(.input),
.module-content :deep(.select),
.module-content :deep(.textarea),
.module-content :deep(input:not([type="checkbox"]):not([type="radio"]):not([type="color"])),
.module-content :deep(select),
.module-content :deep(textarea) {
	border-color: var(--border) !important;
	background: var(--bg-card) !important;
	color: var(--text) !important;
}

.module-content :deep(.input:focus),
.module-content :deep(.select:focus),
.module-content :deep(.textarea:focus),
.module-content :deep(input:focus),
.module-content :deep(select:focus),
.module-content :deep(textarea:focus) {
	border-color: rgb(var(--palette-deep-sapphire-rgb) / 0.42) !important;
	box-shadow: 0 0 0 3px rgb(var(--palette-deep-sapphire-rgb) / 0.1) !important;
}

.module-content :deep(.secondary-btn),
.module-content :deep(.ghost-btn),
.module-content :deep(.mini-link-btn),
.module-content :deep(.icon-btn),
.module-content :deep(.mini-icon),
.module-content :deep(.drag-handle),
.module-content :deep(.preview-tab),
.module-content :deep(.switch-btn) {
	border-color: var(--border) !important;
	background: var(--bg-card) !important;
	color: var(--text) !important;
}

.module-content :deep(.secondary-btn:hover),
.module-content :deep(.ghost-btn:hover),
.module-content :deep(.mini-link-btn:hover) {
	border-color: rgb(var(--palette-deep-sapphire-rgb) / 0.22) !important;
	background: var(--module-50) !important;
	color: var(--module-title-light) !important;
}

.module-content :deep(.primary-btn),
.module-content :deep(.primary-pill-link) {
	background: var(--module-500) !important;
	border-color: var(--module-500) !important;
	color: #fff !important;
	box-shadow: 0 10px 24px rgb(var(--palette-deep-sapphire-rgb) / 0.18) !important;
}

.management-layout.dark .module-content :deep(.primary-btn),
.management-layout.dark .module-content :deep(.primary-pill-link),
:global(.dark) .module-content :deep(.primary-btn),
:global(.dark) .module-content :deep(.primary-pill-link) {
	color: #111827 !important;
}

.module-content :deep(.badge),
.module-content :deep(.state-pill),
.module-content :deep(.pill),
.module-content :deep(.tab-badge),
.module-content :deep(.count-chip),
.module-content :deep(.dirty-chip),
.module-content :deep(.order-badge),
.module-content :deep(.preview-tab.active) {
	border-color: rgb(var(--palette-deep-sapphire-rgb) / 0.16) !important;
	background: var(--module-50) !important;
	color: var(--module-title-light) !important;
}

.management-layout.dark .module-content :deep(.badge),
.management-layout.dark .module-content :deep(.state-pill),
.management-layout.dark .module-content :deep(.pill),
.management-layout.dark .module-content :deep(.tab-badge),
.management-layout.dark .module-content :deep(.count-chip),
.management-layout.dark .module-content :deep(.dirty-chip),
.management-layout.dark .module-content :deep(.order-badge),
.management-layout.dark .module-content :deep(.preview-tab.active),
:global(.dark) .module-content :deep(.badge),
:global(.dark) .module-content :deep(.state-pill),
:global(.dark) .module-content :deep(.pill),
:global(.dark) .module-content :deep(.tab-badge),
:global(.dark) .module-content :deep(.count-chip),
:global(.dark) .module-content :deep(.dirty-chip),
:global(.dark) .module-content :deep(.order-badge),
:global(.dark) .module-content :deep(.preview-tab.active) {
	color: var(--module-title-dark) !important;
}

.module-content :deep(table),
.module-content :deep(thead th) {
	color: var(--text) !important;
}

.module-content :deep(thead th),
.module-content :deep(.table thead th) {
	background: var(--bg-soft) !important;
}

.module-content :deep(td),
.module-content :deep(th),
.module-content :deep(.table-shell) {
	border-color: var(--border) !important;
}

/* Accordion Nav */
.accordion-nav {
	padding: 0.9rem;
	overflow-x: hidden;
	overflow-y: auto;
	display: flex;
	flex-direction: column;
	gap: 0.5rem;
	min-height: 0;
}

.desktop-nav {
	flex: 1;
	padding-bottom: 1.1rem;
}

.nav-group {
	border: 1px solid var(--border);
	border-radius: 14px;
	overflow: hidden;
	background: var(--bg-card);
	flex: 0 0 auto;
	min-height: 0;
	transition:
		border-color 0.18s ease,
		box-shadow 0.18s ease,
		background-color 0.18s ease;
}

.nav-group.open {
	overflow: hidden;
	border-color: rgb(var(--palette-deep-sapphire-rgb) / 0.18);
	box-shadow: 0 12px 28px rgb(15 23 42 / 0.055);
}

.group-button {
	width: 100%;
	border: 0;
	background: transparent;
	color: var(--text);
	min-height: 2.82rem;
	padding: 0.48rem 0.62rem;
	display: flex;
	align-items: center;
	gap: 0.65rem;
	cursor: pointer;
	font-weight: 800;
	font-size: 0.82rem;
	transition: 0.18s ease;
	touch-action: manipulation;
}

.group-button:hover,
.group-button.active {
	background: var(--module-50);
	color: var(--module-title-light);
}

.management-layout.dark .group-button:hover,
.management-layout.dark .group-button.active,
:global(.dark) .group-button:hover,
:global(.dark) .group-button.active {
	background: color-mix(in srgb, var(--module-500) 16%, transparent);
	color: var(--module-title-dark);
}

.group-icon,
.item-icon {
	width: 2rem;
	height: 2rem;
	border-radius: 8px;
	background: var(--bg-soft);
	display: inline-flex;
	align-items: center;
	justify-content: center;
	flex-shrink: 0;
}

.group-button.active .group-icon {
	background: var(--bg-card);
	color: var(--module-600);
	border: 1px solid var(--border);
}

.group-title {
	flex: 1;
	text-align: right;
}

.chevron {
	transition: transform 0.18s ease;
}

.chevron.rotated {
	transform: rotate(180deg);
}

.group-items {
	padding: 0.32rem 0.42rem 0.5rem;
	display: grid;
	gap: 0.3rem;
	background: var(--bg-card);
	width: 100%;
	min-height: 0;
	overflow: visible;
}

.nav-item {
	border-radius: 8px;
	min-height: 2.72rem;
	padding: 0.4rem 0.48rem;
	display: flex;
	align-items: center;
	gap: 0.6rem;
	color: var(--muted);
	transition: 0.18s ease;
}

.nav-item:hover {
	background: var(--bg-soft);
	color: var(--text);
}

.nav-item.active {
	background: var(--module-50);
	color: var(--module-title-light);
	box-shadow: inset 3px 0 0 var(--module-600);
}

.management-layout.dark .nav-item.active,
:global(.dark) .nav-item.active {
	background: color-mix(in srgb, var(--module-500) 16%, transparent);
	color: var(--module-title-dark);
}

.nav-item.active .item-icon {
	background: var(--bg-card);
	color: var(--module-600);
	border: 1px solid var(--border);
}

.item-label {
	display: grid;
	gap: 0.06rem;
	flex: 1;
	min-width: 0;
}

.item-label strong {
	font-size: 0.78rem;
	color: currentColor;
}

.item-label small {
	color: var(--muted-2);
	font-size: 0.66rem;
}

.active-chevron {
	color: var(--module-500);
}

/* Sidebar Footer */
.sidebar-footer {
	border-top: 1px solid var(--border);
	padding: 0.9rem;
	display: grid;
	gap: 0.65rem;
}

.customer-site-link,
.theme-toggle {
	min-height: 2.75rem;
	border: 1px solid var(--border);
	border-radius: 12px;
	background: var(--bg-card);
	color: var(--text);
	display: inline-flex;
	align-items: center;
	justify-content: center;
	gap: 0.45rem;
	font-size: 0.78rem;
	cursor: pointer;
}

.theme-toggle {
	width: 100%;
}

.auth-panel,
.sidebar-auth-card {
	border: 1px solid var(--border);
	border-radius: 14px;
	background: var(--bg-soft);
	padding: 0.75rem;
	display: grid;
	gap: 0.55rem;
}

.auth-title {
	margin: 0;
	font-size: 0.82rem;
	font-weight: 800;
}

.user-row {
	display: flex;
	align-items: center;
	gap: 0.65rem;
	min-width: 0;
}

.user-row div {
	min-width: 0;
	display: grid;
	gap: 0.05rem;
}

.user-row strong {
	font-size: 0.78rem;
	color: var(--text);
	white-space: nowrap;
	overflow: hidden;
	text-overflow: ellipsis;
}

.user-row small {
	font-size: 0.68rem;
	color: var(--muted);
	white-space: nowrap;
	overflow: hidden;
	text-overflow: ellipsis;
}

.user-avatar {
	width: 2.25rem;
	height: 2.25rem;
	border-radius: 999px;
	background: var(--bg-card);
	color: var(--muted);
	display: inline-flex;
	align-items: center;
	justify-content: center;
	flex-shrink: 0;
}

.primary-pill-link,
.secondary-btn,
.header-auth-btn,
.header-site-link {
	border: 1px solid var(--border);
	border-radius: 999px;
	min-height: 2.5rem;
	padding: 0.62rem 0.95rem;
	font-size: 0.78rem;
	line-height: 1;
	text-align: center;
	cursor: pointer;
}

.primary-pill-link {
	background: var(--module-500);
	border-color: var(--module-500);
	color: white;
}

.secondary-btn {
	background: var(--bg-card);
	color: var(--text);
}

.secondary-btn.full {
	width: 100%;
}

.secondary-btn:disabled {
	opacity: 0.55;
	cursor: default;
}

.header-site-link,
.header-auth-btn {
	background: var(--bg-soft);
	color: var(--text);
}

.header-auth-btn.muted {
	background: color-mix(in srgb, var(--module-500) 13%, var(--bg-soft));
}

.header-user-chip {
	border: 1px solid var(--border);
	border-radius: 0.9rem;
	background: color-mix(in srgb, var(--module-500) 10%, var(--bg-card));
	padding: 0.32rem 0.65rem;
	display: grid;
	gap: 0.04rem;
}

.header-user-chip strong {
	font-size: 0.72rem;
	color: var(--text);
}

.header-user-chip small {
	color: var(--muted);
	font-size: 0.64rem;
}

/* Zoom */
.desktop-zoom {
	display: flex;
	align-items: center;
	justify-content: center;
	gap: 0.25rem;
	border-radius: 999px;
	border: 1px solid var(--border);
	background: var(--bg-card);
	padding: 0.25rem;
}

.zoom-btn,
.zoom-reset {
	border: 1px solid var(--border);
	background: var(--bg-soft);
	color: var(--text);
	border-radius: 999px;
	font-size: 0.7rem;
	line-height: 1;
	padding: 0.36rem 0.55rem;
	cursor: pointer;
}

.zoom-btn:disabled,
.zoom-reset:disabled {
	opacity: 0.45;
	cursor: default;
}

.zoom-level {
	min-width: 2.6rem;
	text-align: center;
	color: var(--muted);
	font-size: 0.72rem;
}

/* Mobile responsive fixes for management pages */
@media (max-width: 1023px) {
	.mobile-main {
		overflow-x: hidden;
		width: 100%;
		max-width: 100vw;
	}

	.mobile-main :deep(.glass-card),
	.mobile-main :deep(.hero-card),
	.mobile-main :deep(.surface-card) {
		border-radius: 18px;
	}

	.mobile-main :deep(.hero-card),
	.mobile-main :deep(.surface-card),
	.mobile-main :deep(.management-surface-card) {
		padding: 0.75rem !important;
		overflow-x: auto;
	}

	.mobile-main :deep(.form-grid) {
		grid-template-columns: 1fr !important;
	}

	.mobile-main :deep(.form-grid .span-2),
	.mobile-main :deep(.form-grid .col-span-2) {
		grid-column: 1 !important;
	}

	.mobile-main :deep(.checks-grid) {
		grid-template-columns: 1fr 1fr !important;
	}

	.mobile-main :deep(.page-header),
	.mobile-main :deep(.module-page-header) {
		flex-wrap: wrap;
		gap: 0.5rem;
	}

	.mobile-main :deep(.page-header .page-actions),
	.mobile-main :deep(.module-page-header .page-actions) {
		flex-wrap: wrap;
		gap: 0.4rem;
	}

	.mobile-main :deep(.primary-btn),
	.mobile-main :deep(.secondary-btn),
	.mobile-main :deep(.tertiary-btn),
	.mobile-main :deep(.header-auth-btn),
	.mobile-main :deep(.sheet-management-btn) {
		min-height: 2.75rem;
		padding: 0.42rem 0.68rem;
		font-size: 0.8rem;
	}

	.mobile-main :deep(.input),
	.mobile-main :deep(.textarea),
	.mobile-main :deep(select),
	.mobile-main :deep(.searchable-dropdown),
	.mobile-main :deep(.searchable-select) {
		min-height: 2.75rem;
		font-size: 0.82rem;
	}

	.mobile-main :deep(.surface-card-inner),
	.mobile-main :deep(.management-surface-card) {
		overflow-x: auto;
	}

	.mobile-main :deep(table) {
		min-width: 480px;
	}

	.mobile-main :deep(.table-shell) {
		overflow-x: auto;
		-webkit-overflow-scrolling: touch;
		max-width: 100%;
	}

	.mobile-main :deep(.table-scroll),
	.mobile-main :deep(.table-wrap) {
		overflow-x: auto;
		-webkit-overflow-scrolling: touch;
	}

	.mobile-main :deep(.variant-row) {
		grid-template-columns: 1fr 1fr !important;
	}

	.mobile-main :deep(.stat-grid),
	.mobile-main :deep(.stats-grid) {
		grid-template-columns: 1fr 1fr !important;
	}

	.mobile-main :deep(.pos-grid),
	.mobile-main :deep(.order-grid) {
		grid-template-columns: 1fr !important;
	}

	/* Force all grids inside management pages to single column on mobile */
	.mobile-main :deep([class*="grid"]) {
		grid-template-columns: minmax(0, 1fr) !important;
	}

	/* But keep 2-col for specific small grids */
	.mobile-main :deep(.kpi-grid),
	.mobile-main :deep(.mini-matrix) {
		grid-template-columns: 1fr 1fr !important;
	}

	/* KPI cards should wrap properly */
	.mobile-main :deep(.kpi-card) {
		min-width: 0;
		overflow: hidden;
	}

	/* Charts should not overflow */
	.mobile-main :deep(canvas),
	.mobile-main :deep(svg) {
		max-width: 100% !important;
	}

	/* Toggle rows and filter controls should wrap */
	.mobile-main :deep(.toggle-row),
	.mobile-main :deep(.legend-checks),
	.mobile-main :deep(.global-controls),
	.mobile-main :deep(.filters),
	.mobile-main :deep(.toolbar) {
		display: flex !important;
		flex-wrap: wrap !important;
		gap: 0.35rem !important;
		grid-template-columns: unset !important;
	}

	/* Make labels inside controls wrap properly */
	.mobile-main :deep(.global-controls label),
	.mobile-main :deep(.filters label),
	.mobile-main :deep(.toolbar label) {
		min-width: 0;
		flex: 1 1 auto;
	}
}

/* Scoped deep tweaks for child pages */
.module-content :deep(.glass-card),
.module-content :deep(.card),
.module-content :deep(.panel) {
	border-color: var(--border);
}

.module-content :deep(.primary-btn),
.module-content :deep(.module-primary-btn),
.module-content :deep(button.bg-amber-500),
.module-content :deep(button.bg-orange-500),
.module-content :deep(button.bg-emerald-500),
.module-content :deep(button.bg-cyan-500),
.module-content :deep(button.bg-blue-500),
.module-content :deep(button.bg-violet-500),
.module-content :deep(button.bg-rose-500),
.module-content :deep(button.bg-indigo-600),
.module-content :deep(a.bg-indigo-600),
.module-content :deep(a.bg-blue-600),
.module-content :deep(button.bg-blue-600) {
	background-color: var(--module-500) !important;
	border-color: var(--module-500) !important;
}

.module-content :deep(.text-indigo-600),
.module-content :deep(.text-blue-600),
.module-content :deep(.text-emerald-600),
.module-content :deep(.text-violet-600) {
	color: var(--module-600) !important;
}

/* Transitions */
.fade-enter-active,
.fade-leave-active {
	transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
	opacity: 0;
}

.slide-right-enter-active,
.slide-right-leave-active {
	transition: transform 0.28s ease;
}

@media (prefers-reduced-motion: reduce) {
	*,
	*::before,
	*::after {
		animation-duration: 0.01ms !important;
		animation-iteration-count: 1 !important;
		scroll-behavior: auto !important;
		transition-duration: 0.01ms !important;
	}
}

.slide-right-enter-from,
.slide-right-leave-to {
	transform: translateX(100%);
}

/* Links reset */
a {
	text-decoration: none;
}

/* Mobile auth card spacing */
.mobile-sidebar .sidebar-auth-card {
	margin: 0 1rem 1rem;
	flex-shrink: 0;
}
</style>
