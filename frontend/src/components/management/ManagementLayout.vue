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

				<a href="/management" class="mobile-brand">
					<span class="brand-mark">
						<img class="brand-image" src="/NooshYar%20Image.png" alt="NooshYar" />
					</span>
					<span class="mobile-brand-text">
						<strong>نوش‌یار</strong>
						<small>پنل مدیریت</small>
					</span>
				</a>

				<div class="mobile-header-actions">
					<button
						type="button"
						class="mobile-theme-toggle"
						:class="{ 'is-dark': isDarkMode }"
						@click="toggleTheme"
						:aria-label="isDarkMode ? 'فعال‌سازی حالت روز' : 'فعال‌سازی حالت شب'"
						:title="isDarkMode ? 'حالت روز' : 'حالت شب'"
					>
						<span class="theme-toggle-glow" aria-hidden="true"></span>
						<span class="theme-toggle-track" aria-hidden="true">
							<SunIcon class="theme-icon theme-icon-sun" />
							<MoonIcon class="theme-icon theme-icon-moon" />
							<span class="theme-toggle-thumb">
								<SunIcon v-if="isDarkMode" class="theme-thumb-icon" />
								<MoonIcon v-else class="theme-thumb-icon" />
							</span>
						</span>
						<span class="sr-only">{{ isDarkMode ? 'حالت روز' : 'حالت شب' }}</span>
					</button>

					<a href="/menu" class="icon-button" title="مشاهده سایت مشتری">
						<HomeIcon class="icon-md" />
					</a>
				</div>
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
			


			<!-- Main Content -->
			<div class="desktop-content" :class="{ 'desktop-content--pos': isPosPage }">
								<header class="desktop-header">
					<div class="desktop-header-start">
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
	UserCog as UserCogIcon,
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
	LogOut as LogOutIcon,
	Sun as SunIcon,
	Moon as MoonIcon,
	PanelRightClose as PanelRightCloseIcon,
	PanelRightOpen as PanelRightOpenIcon,
	SlidersHorizontal as SlidersIcon,
	Store as StoreIcon,
	Boxes as InventoryIcon,
	UtensilsCrossed as KitchenIcon,
	HeartHandshake as ClubIcon,
	ClipboardCheck as SurveyIcon,
	Wallet as WalletIcon,
	Calculator as CalculatorIcon,
	CalendarCheck as CalendarCheckIcon,
	Headset as HeadsetIcon,
	Building2 as BuildingIcon,
	LifeBuoy as LifeBuoyIcon,
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
const railMode = ref("icons");
const mobileMenuOpen = ref(false);
const userMenuOpen = ref(false);
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
			key: "management-register",
			label: "صندوق و تسویه",
			shortLabel: "صندوق",
			caption: "بستن صندوق، شیفت و کمبو",
			iconComponent: StoreIcon,
			url: "/management/register",
			group: "sales",
		},
		{
			key: "management-inventory",
			label: "انبارداری هوشمند",
			shortLabel: "انبار",
			caption: "موجودی، خرید، تولید و ضایعات",
			iconComponent: InventoryIcon,
			url: "/management/inventory",
			group: "inventory",
		},
		{
			key: "management-inventory-overview",
			label: "موجودی و ارزش",
			shortLabel: "موجودی",
			caption: "موجودی مقداری و مبلغی",
			iconComponent: InventoryIcon,
			url: "/management/inventory?tab=overview",
			group: "inventory",
		},
		{
			key: "management-material-requests",
			label: "درخواست مواد",
			shortLabel: "درخواست مواد",
			caption: "ثبت نیاز و انتقال به خرید",
			iconComponent: OrdersIcon,
			url: "/management/inventory?tab=requests",
			group: "inventory",
		},
		{
			key: "management-inventory-materials",
			label: "مواد اولیه",
			shortLabel: "مواد",
			caption: "کالاها، واحدها و نقطه سفارش",
			iconComponent: ProductsIcon,
			url: "/management/inventory?tab=materials",
			group: "inventory",
		},
		{
			key: "management-inventory-purchase",
			label: "خرید مواد",
			shortLabel: "خرید",
			caption: "سفارش خرید و دریافت",
			iconComponent: StoreIcon,
			url: "/management/inventory?tab=purchase",
			group: "inventory",
		},
		{
			key: "management-inventory-warehouses",
			label: "انبارها",
			shortLabel: "انبارها",
			caption: "مدیریت انبار و مقصد دریافت",
			iconComponent: LayersIcon,
			url: "/management/inventory?tab=warehouses",
			group: "inventory",
		},
		{
			key: "management-inventory-movements",
			label: "ورود و خروج",
			shortLabel: "گردش",
			caption: "گردش، انتقال و ضایعات",
			iconComponent: FileTextIcon,
			url: "/management/inventory?tab=movements",
			group: "inventory",
		},
		{
			key: "management-inventory-reorder",
			label: "نقطه سفارش",
			shortLabel: "هشدار",
			caption: "کمبود و پیشنهاد خرید",
			iconComponent: SurveyIcon,
			url: "/management/inventory?tab=reorder",
			group: "inventory",
		},
		{
			key: "management-inventory-production",
			label: "برنامه تولید",
			shortLabel: "تولید",
			caption: "نیاز مواد و تولید دستی",
			iconComponent: KitchenIcon,
			url: "/management/inventory?tab=production",
			group: "inventory",
		},
		{
			key: "management-inventory-losses",
			label: "ضایعات و اوتی‌ها",
			shortLabel: "ضایعات",
			caption: "ثبت و گزارش خسارت",
			iconComponent: WalletIcon,
			url: "/management/inventory?tab=losses",
			group: "inventory",
		},
		{
			key: "management-inventory-count",
			label: "انبارگردانی",
			shortLabel: "گردش شمارش",
			caption: "شمارش و مغایرت‌گیری",
			iconComponent: SettingsIcon,
			url: "/management/inventory?tab=count",
			group: "inventory",
		},
		{
			key: "management-inventory-costs",
			label: "بهای تمام‌شده",
			shortLabel: "هزینه مواد",
			caption: "محاسبه بهای مواد و فرمول",
			iconComponent: CalculatorIcon,
			url: "/management/inventory?tab=costs",
			group: "inventory",
		},
		{
			key: "management-club",
			label: "باشگاه مشتریان",
			shortLabel: "باشگاه",
			caption: "وفاداری، پیامک، کیف پول و کمپین",
			iconComponent: ClubIcon,
			url: "/management/club",
			group: "crm",
		},
		{
			key: "management-surveys",
			label: "نظرسنجی هوشمند",
			shortLabel: "نظرسنجی",
			caption: "نظر سفارش‌محور و هشدار نارضایتی",
			iconComponent: SurveyIcon,
			url: "/management/surveys",
			group: "crm",
		},
		{
			key: "management-cost-control",
			label: "کاست کنترل",
			shortLabel: "هزینه",
			caption: "بودجه، سود و زیان و نقطه سربه‌سر",
			iconComponent: WalletIcon,
			url: "/management/cost-control",
			group: "reports",
		},
		{
			key: "management-accounting",
			label: "حسابداری یکپارچه",
			shortLabel: "حسابداری",
			caption: "تراز دریافت و پرداخت، مالیات و اسناد",
			iconComponent: CalculatorIcon,
			url: "/management/accounting",
			group: "reports",
		},
		{
			key: "management-reservations",
			label: "رزرواسیون",
			shortLabel: "رزرو",
			caption: "رزرو میز، میهمان و یادآوری",
			iconComponent: CalendarCheckIcon,
			url: "/management/reservations",
			group: "sales",
		},
		{
			key: "management-call-center",
			label: "مرکز تماس",
			shortLabel: "تماس",
			caption: "تماس ورودی VOIP و پروفایل مشتری",
			iconComponent: HeadsetIcon,
			url: "/management/call-center",
			group: "crm",
		},
		{
			key: "management-branches",
			label: "شعب",
			shortLabel: "شعبه",
			caption: "مدیریت شعب و انتقال مشتری",
			iconComponent: BuildingIcon,
			url: "/management/branches",
			group: "settings",
		},
		{
			key: "management-help",
			label: "راهنما و آموزش",
			shortLabel: "راهنما",
			caption: "پشتیبانی، آموزش و اکانت منیجر",
			iconComponent: LifeBuoyIcon,
			url: "/management/help",
			group: "settings",
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
			key: "management-users",
			label: "کاربران و دسترسی‌ها",
			shortLabel: "کاربران",
			caption: "نقش‌ها و سطح دسترسی",
			iconComponent: UserCogIcon,
			url: "/management/users",
			group: "settings",
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
const isKitchenPage = computed(() => props.page === "management-kitchen");
const authGuest = computed(() => Boolean(authProfile.value?.is_guest));

const moduleThemeVars = computed(() => {
	if (isDarkMode.value) {
		return {
			"--module-500": "#f4e6d3",
			"--module-600": "#fff3e2",
			"--module-50": "rgb(244 230 211 / 0.13)",
			"--module-title-light": "var(--mg-text-main)",
			"--module-title-dark": "#fff7ed",
		};
	}

	return {
		"--module-500": "var(--mg-primary)",
		"--module-600": "var(--mg-primary)",
		"--module-50": "rgb(139 94 52 / 0.075)",
		"--module-title-light": "var(--mg-text-main)",
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
	if (props.page === "management-inventory") {
		const inventoryTabs = {
			"management-inventory-overview": "overview",
			"management-material-requests": "requests",
			"management-inventory-materials": "materials",
			"management-inventory-purchase": "purchase",
			"management-inventory-warehouses": "warehouses",
			"management-inventory-movements": "movements",
			"management-inventory-reorder": "reorder",
			"management-inventory-production": "production",
			"management-inventory-losses": "losses",
			"management-inventory-count": "count",
			"management-inventory-costs": "costs",
		};
		if (key === "management-inventory") {
			const currentTab = new URLSearchParams(window.location.search).get("tab") || "overview";
			return currentTab === "overview";
		}
		if (inventoryTabs[key]) {
			const currentTab = new URLSearchParams(window.location.search).get("tab") || "overview";
			return currentTab === inventoryTabs[key];
		}
	}
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

function toggleUserMenu() {
		userMenuOpen.value = !userMenuOpen.value;
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

	railMode.value = "icons"; // Default to closed for all pages with floating menu


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

.mobile-header-actions {
	display: flex;
	align-items: center;
	gap: 0.2rem;
}

.mobile-theme-toggle {
	position: relative;
	width: 4.15rem;
	height: 2.5rem;
	padding: 0;
	border: 0;
	background: transparent;
	color: var(--mg-text-muted);
	cursor: pointer;
	-webkit-tap-highlight-color: transparent;
}

.theme-toggle-track {
	position: absolute;
	inset: 0.2rem 0;
	display: block;
	overflow: hidden;
	border: 1px solid var(--mg-border-light);
	border-radius: 999px;
	background: linear-gradient(135deg, var(--mg-bg-soft), var(--mg-bg-page));
	box-shadow: inset 0 1px 2px rgba(52, 38, 31, 0.08), 0 3px 10px rgba(52, 38, 31, 0.06);
	transition: background 0.45s ease, border-color 0.45s ease, box-shadow 0.45s ease;
}

.mobile-theme-toggle.is-dark .theme-toggle-track {
	background: linear-gradient(135deg, #25221f, #3b302b);
	border-color: rgba(244, 230, 211, 0.25);
	box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.35), 0 3px 14px rgba(0, 0, 0, 0.22);
}

.theme-toggle-thumb {
	position: absolute;
	top: 0.18rem;
	left: 0.2rem;
	width: 1.7rem;
	height: 1.7rem;
	display: grid;
	place-items: center;
	border-radius: 50%;
	background: #fffaf3;
	color: #c97852;
	box-shadow: 0 2px 7px rgba(52, 38, 31, 0.2);
	transition: transform 0.5s cubic-bezier(0.22, 1.25, 0.36, 1), background 0.45s ease, color 0.45s ease;
}

.mobile-theme-toggle.is-dark .theme-toggle-thumb {
	transform: translateX(2.05rem) rotate(180deg);
	background: #f4e6d3;
	color: #57483e;
}

.theme-thumb-icon { width: 1rem; height: 1rem; }
.theme-icon {
	position: absolute;
	top: 0.62rem;
	width: 0.9rem;
	height: 0.9rem;
	opacity: 0.72;
	transition: opacity 0.35s ease, transform 0.45s ease;
}
.theme-icon-sun { right: 0.42rem; color: #efb454; }
.theme-icon-moon { left: 0.42rem; color: #d8c8b4; }
.mobile-theme-toggle:not(.is-dark) .theme-icon-moon { opacity: 0.3; }
.mobile-theme-toggle.is-dark .theme-icon-sun { opacity: 0.3; }

.theme-toggle-glow {
	position: absolute;
	inset: 0.12rem;
	border-radius: 999px;
	background: var(--mg-primary);
	opacity: 0;
	transform: scale(0.55);
	pointer-events: none;
}
.mobile-theme-toggle:active .theme-toggle-glow {
	animation: theme-toggle-pulse 0.55s ease-out;
}
.mobile-theme-toggle:focus-visible {
	outline: 3px solid color-mix(in srgb, var(--mg-primary) 45%, transparent);
	outline-offset: 2px;
	border-radius: 999px;
}

@keyframes theme-toggle-pulse {
	0% { opacity: 0.35; transform: scale(0.55); }
	100% { opacity: 0; transform: scale(1.25); }
}

@media (prefers-reduced-motion: reduce) {
	.theme-toggle-track,
	.theme-toggle-thumb,
	.theme-icon {
		transition-duration: 0.01ms;
	}
	.mobile-theme-toggle:active .theme-toggle-glow {
		animation: none;
	}
}

.sr-only {
	position: absolute;
	width: 1px;
	height: 1px;
	padding: 0;
	margin: -1px;
	overflow: hidden;
	clip: rect(0, 0, 0, 0);
	white-space: nowrap;
	border: 0;
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

/* --- Desktop Floating Menu (Integrated in Header) --- */
	.dfm-wrapper.inline-dfm {
		position: relative;
		z-index: 10000;
		margin-left: 0.5rem;
	}

	.dfm-toggle-btn {
		width: 2.5rem;
		height: 2.5rem;
		border-radius: 50%;
		background: var(--mg-bg-surface);
		color: var(--mg-primary);
		border: 1px solid var(--mg-border-light);
		display: flex;
		align-items: center;
		justify-content: center;
		cursor: pointer;
		box-shadow: 0 4px 12px rgba(0,0,0,0.05);
		transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
		position: relative;
		z-index: 10001;
	}
	
	/* Space rings animation */
	.dfm-toggle-btn::before, .dfm-toggle-btn::after {
		content: '';
		position: absolute;
		inset: -2px;
		border-radius: 50%;
		border: 1px solid var(--mg-primary);
		opacity: 0;
		pointer-events: none;
	}
	.dfm-toggle-btn::before {
		animation: dfm-ring-pulse 3s infinite ease-out;
	}
	.dfm-toggle-btn::after {
		animation: dfm-ring-pulse 3s infinite ease-out 1.5s;
	}

	@keyframes dfm-ring-pulse {
		0% { transform: scale(1); opacity: 0.6; border-width: 1px; }
		100% { transform: scale(1.6); opacity: 0; border-width: 0px; }
	}

	.dfm-toggle-btn:hover {
		transform: scale(1.05);
		background: var(--mg-primary);
		color: #fff;
		border-color: var(--mg-primary);
	}
	.dfm-toggle-btn:hover .dfm-line {
		background: #fff;
	}

	.dfm-burger {
		width: 16px;
		height: 12px;
		position: relative;
	}
	.dfm-line {
		display: block;
		width: 100%;
		height: 2px;
		background: var(--mg-primary);
		border-radius: 2px;
		position: absolute;
		right: 0;
		transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
	}
	.dfm-line.top { top: 0; }
	.dfm-line.mid { top: 50%; transform: translateY(-50%); }
	.dfm-line.bot { bottom: 0; }

	.dfm-toggle-btn.is-open {
		background: var(--mg-primary);
		color: #fff;
		border-color: var(--mg-primary);
		transform: rotate(90deg);
	}
	.dfm-toggle-btn.is-open::before, .dfm-toggle-btn.is-open::after {
		animation-play-state: paused;
		opacity: 0;
		display: none;
	}
	.dfm-toggle-btn.is-open .dfm-line { background: #fff; }
	.dfm-toggle-btn.is-open .dfm-line.top { top: 50%; transform: translateY(-50%) rotate(45deg); }
	.dfm-toggle-btn.is-open .dfm-line.mid { opacity: 0; transform: translateY(-50%) scaleX(0); }
	.dfm-toggle-btn.is-open .dfm-line.bot { bottom: 50%; transform: translateY(50%) rotate(-45deg); }

	.dfm-dropdown {
		position: absolute;
		top: calc(100% + 1.25rem);
		right: 0;

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
		backdrop-filter: blur(4px);
		-webkit-backdrop-filter: blur(4px);
		z-index: 9998;
	}

	.dfm-anim-enter-active, .dfm-anim-leave-active {
		transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
		transform-origin: top right;
	}
	.dfm-anim-enter-from, .dfm-anim-leave-to {
		opacity: 0;
		transform: scale(0.85) translateY(-20px);
	}



	/* Desktop layout content takes full width now */
	

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
		border-bottom: 1px solid var(--mg-border-light);
	}

	.desktop-header-start {
		display: flex;
		align-items: center;
		gap: 1.5rem;
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
	}

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
	.desktop-main--fullbleed > :deep(*) { max-width: 100%; margin: 0; }
	.desktop-main--fullbleed > :deep(*) { max-width: 100%; margin: 0; }

	
		
	

	.desktop-sidebar { display: none; }
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
