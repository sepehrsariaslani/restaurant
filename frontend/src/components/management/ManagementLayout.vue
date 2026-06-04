<template>
  <!-- Guest/Auth Shell -->
  <section v-if="authGuest" class="management-auth-shell" dir="rtl">
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
<div
v-if="mobileMenuOpen"
class="mobile-overlay"
@click="closeMobileMenu"
/>
</Transition>

<Transition name="slide-right">
<aside v-if="mobileMenuOpen" class="mobile-sidebar">
<div class="mobile-sidebar-header">
<div class="sidebar-title">
<span class="brand-mark">
<img class="brand-image" src="/NooshYar%20Image.png" alt="NooshYar" />
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
>
<button
type="button"
class="group-button"
:class="{ active: openGroupKey === group.key }"
@click="toggleGroup(group.key)"
>
<span class="group-icon">
<component :is="group.icon" class="icon-sm" />
</span>
<span>{{ group.title }}</span>
<ChevronDownIcon
class="icon-sm chevron"
:class="{ rotated: openGroupKey === group.key }"
/>
</button>

<div v-if="openGroupKey === group.key" class="group-items">
<a
v-for="item in group.items"
:key="`mobile-item-${item.key}`"
:href="item.url"
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
<strong>{{ authProfile.full_name || authProfile.user }}</strong>
<small>{{ authProfile.user }}</small>
</div>
</div>

<button
type="button"
class="secondary-btn full"
:disabled="authSubmitting"
@click="handleMobileLogout"
>
{{ authSubmitting ? 'در حال خروج...' : 'خروج' }}
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
<img class="brand-image brand-image-lg" src="/NooshYar%20Image.png" alt="NooshYar" />
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
>
<button
type="button"
class="group-button"
:class="{ active: openGroupKey === group.key }"
@click="toggleGroup(group.key)"
>
<span class="group-icon">
<component :is="group.icon" class="icon-sm" />
</span>

<span class="group-title">{{ group.title }}</span>

<ChevronDownIcon
class="icon-sm chevron"
:class="{ rotated: openGroupKey === group.key }"
/>
</button>

<div v-if="openGroupKey === group.key" class="group-items">
<a
v-for="item in group.items"
:key="item.key"
:href="item.url"
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
<a class="primary-pill-link" :href="loginUrl">
ورود
</a>
</template>

<template v-else>
<div class="user-row">
<span class="user-avatar">
<UserIcon class="icon-sm" />
</span>
<div>
<strong>{{ authProfile.full_name || authProfile.user }}</strong>
<small>{{ authProfile.user }}</small>
</div>
</div>

<button
class="secondary-btn full"
type="button"
:disabled="authSubmitting"
@click="submitLogout"
>
{{ authSubmitting ? 'در حال خروج...' : 'خروج' }}
</button>
</template>

<p v-if="authError" class="auth-error">
{{ authError }}
</p>
</section>

<button
type="button"
class="theme-toggle"
@click="toggleTheme"
>
<SunIcon v-if="isDarkMode" class="icon-sm" />
<MoonIcon v-else class="icon-sm" />
<span>{{ isDarkMode ? 'حالت روز' : 'حالت شب' }}</span>
</button>

<div class="desktop-zoom">
<button type="button" class="zoom-btn" :disabled="!canIncrease" @click="increaseScale">
A+
</button>
<span class="zoom-level">{{ scaleLabel }}</span>
<button type="button" class="zoom-btn" :disabled="!canDecrease" @click="decreaseScale">
A-
</button>
<button type="button" class="zoom-reset" :disabled="isDefaultScale" @click="resetScale">
پیش‌فرض
</button>
</div>
</div>
</aside>

<!-- Main Content -->
<div class="desktop-content">
<header class="desktop-header">
<div class="page-title-wrap">
<small>داشبورد عملیاتی</small>
<h1>{{ activeTitle }}</h1>
</div>

<div class="desktop-header-actions">
<a class="header-site-link" href="/menu">
سایت مشتری
</a>

<template v-if="!authLoading">
<a v-if="authGuest" class="header-auth-btn" :href="loginUrl">
ورود
</a>

<template v-else>
<div class="header-user-chip" :title="authProfile.user">
<strong>{{ authProfile.full_name || authProfile.user }}</strong>
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

<main class="desktop-main module-content">
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
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import ManagementBearLoader from '@/components/management/ManagementBearLoader.vue'
import ManagementLoginGate from '@/components/management/ManagementLoginGate.vue'
import { getManagementSessionProfile, logoutManagementUser } from '@/utils/api'

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
} from 'lucide-vue-next'

const DESKTOP_MEDIA_QUERY = '(min-width: 1024px)'
const ZOOM_STORAGE_KEY = 'restaurant.management.desktopScale'
const RAIL_STORAGE_KEY = 'restaurant.management.desktopRailMode'
const THEME_STORAGE_KEY = 'restaurant.management.theme'
const ZOOM_BASE_FONT_SIZE = 16
const ZOOM_MIN = 0.85
const ZOOM_MAX = 1.2
const ZOOM_STEP = 0.05

const MOBILE_PRIMARY_LINK_KEYS = [
  'management-dashboard',
  'management-pos',
  'management-orders',
  'management-products',
  'management-reports',
]

const props = defineProps({
  page: {
type: String,
default: 'management-dashboard',
  },
  brandName: {
type: String,
default: 'Restaurant',
  },
})

const isDesktop = ref(false)
const desktopScale = ref(1)
const railMode = ref('expanded')
const mobileMenuOpen = ref(false)
const openGroupKey = ref('overview')
const isDarkMode = ref(false)

let desktopMedia = null
let desktopListener = null

const authLoading = ref(true)
const authSubmitting = ref(false)
const authError = ref('')
const authProfile = ref({
  user: 'Guest',
  full_name: '',
  user_image: '',
  is_guest: true,
})

const navLinks = computed(() => [
  {
key: 'management-dashboard',
label: 'داشبورد',
shortLabel: 'خانه',
caption: 'نمای کلی',
iconComponent: LayoutGridIcon,
url: '/management',
group: 'overview',
  },
  {
key: 'management-pos',
label: 'POS',
shortLabel: 'POS',
caption: 'فروش حضوری',
iconComponent: PosIcon,
url: '/management/pos',
group: 'sales',
  },
  {
key: 'management-pos-profile',
label: 'پروفایل POS',
shortLabel: 'پروفایل',
caption: 'تنظیمات ترمینال',
iconComponent: SlidersIcon,
url: '/management/pos-profile',
group: 'sales',
  },
  {
key: 'management-orders',
label: 'سفارش‌ها',
shortLabel: 'سفارش',
caption: 'وضعیت و تحویل',
iconComponent: OrdersIcon,
url: '/management/orders',
group: 'sales',
  },
  {
key: 'management-products',
label: 'محصولات',
shortLabel: 'محصول',
caption: 'قیمت و موجودی',
iconComponent: ProductsIcon,
url: '/management/products',
group: 'menu',
  },
  {
key: 'management-variant-builder',
label: 'صفت محصولات',
shortLabel: 'صفت',
caption: 'ویژگی‌ها و انواع',
iconComponent: TagsIcon,
url: '/management/product?variant_studio=1',
group: 'menu',
  },
  {
key: 'management-menu-groups',
label: 'دسته‌بندی',
shortLabel: 'دسته',
caption: 'گروه‌ها و زیردسته',
iconComponent: LayersIcon,
url: '/management/menu-groups',
group: 'menu',
  },
  {
key: 'management-boms',
label: 'مواد اولیه',
shortLabel: 'مواد',
caption: 'فرمول و دستور ساخت',
iconComponent: StoreIcon,
url: '/management/boms',
group: 'inventory',
  },
  {
key: 'management-customers',
label: 'مشتریان',
shortLabel: 'مشتری',
caption: 'اطلاعات مشتریان',
iconComponent: UsersIcon,
url: '/management/customers',
group: 'crm',
  },
  {
key: 'management-reports',
label: 'گزارش عملکرد',
shortLabel: 'گزارش',
caption: 'آمار و تحلیل',
iconComponent: ReportsIcon,
url: '/management/reports',
group: 'reports',
  },
  {
key: 'management-report',
label: 'گزارش',
shortLabel: 'گزارش',
caption: 'نمایش گزارش تکی',
iconComponent: FileTextIcon,
url: '/management/reports',
group: 'reports',
  },
  {
key: 'management-print-formats',
label: 'فرمت چاپ',
shortLabel: 'چاپ',
caption: 'قالب‌های چاپ',
iconComponent: PrinterIcon,
url: '/management/print-formats',
group: 'reports',
  },
  {
key: 'management-site-settings',
label: 'تنظیمات سایت',
shortLabel: 'سایت',
caption: 'محتوا و تنظیمات',
iconComponent: SettingsIcon,
url: '/management/site-settings',
group: 'settings',
  },
  {
key: 'management-settings',
label: 'تنظیمات پنل',
shortLabel: 'تنظیمات',
caption: 'رنگ‌بندی و ظاهر پنل',
iconComponent: SlidersIcon,
url: '/management/settings',
group: 'settings',
  },
])

const menuGroups = computed(() => [
  {
key: 'overview',
title: 'نمای کلی',
icon: LayoutGridIcon,
items: navLinks.value.filter((link) => link.group === 'overview'),
  },
  {
key: 'sales',
title: 'فروش و سفارش',
icon: OrdersIcon,
items: navLinks.value.filter((link) => link.group === 'sales'),
  },
  {
key: 'menu',
title: 'منو و محصولات',
icon: ProductsIcon,
items: navLinks.value.filter((link) => link.group === 'menu'),
  },
  {
key: 'inventory',
title: 'مواد و تولید',
icon: StoreIcon,
items: navLinks.value.filter((link) => link.group === 'inventory'),
  },
  {
key: 'crm',
title: 'مشتریان',
icon: UsersIcon,
items: navLinks.value.filter((link) => link.group === 'crm'),
  },
  {
key: 'reports',
title: 'گزارش‌ها و چاپ',
icon: ReportsIcon,
items: navLinks.value.filter((link) => link.group === 'reports'),
  },
  {
key: 'settings',
title: 'تنظیمات',
icon: SettingsIcon,
items: navLinks.value.filter((link) => link.group === 'settings'),
  },
])

const mobilePrimaryLinks = computed(() =>
  navLinks.value.filter(
(link) => MOBILE_PRIMARY_LINK_KEYS.includes(link.key) && link.key !== 'management-report',
  ),
)

const activeTitle = computed(() => {
  const active = navLinks.value.find((link) => isLinkActive(link.key))
  return active?.label || 'پنل مدیریت'
})

const activeGroup = computed(() => {
  return menuGroups.value.find((group) =>
group.items.some((item) => isLinkActive(item.key)),
  )
})

const canIncrease = computed(() => desktopScale.value < ZOOM_MAX)
const canDecrease = computed(() => desktopScale.value > ZOOM_MIN)
const isDefaultScale = computed(() => Math.abs(desktopScale.value - 1) < 0.001)
const scaleLabel = computed(() => `${Math.round(desktopScale.value * 100)}%`)
const isRailCollapsed = computed(() => railMode.value === 'icons')
const isLoginPage = computed(() => props.page === 'management-login')
const authGuest = computed(() => Boolean(authProfile.value?.is_guest))

const moduleThemeVars = computed(() => ({
  '--module-500': '#6f4a31',
  '--module-600': '#5a3a25',
  '--module-50': '#f1e7db',
  '--module-title-light': '#3f2a1d',
  '--module-title-dark': '#e8dacd',
}))

function toggleGroup(key) {
  openGroupKey.value = openGroupKey.value === key ? '' : key
}

function isLinkActive(key) {
  if (props.page === key) return true
  if (props.page === 'management-product' && key === 'management-products') return true
  if (props.page === 'management-menu-group' && key === 'management-menu-groups') return true
  if (props.page === 'management-bom' && key === 'management-boms') return true
  if (props.page === 'management-report' && key === 'management-reports') return true
  return false
}

function closeMobileMenu() {
  mobileMenuOpen.value = false
}

function toggleRailMode() {
  railMode.value = isRailCollapsed.value ? 'expanded' : 'icons'
}

function normalizeManagementPath(path, fallback = '/management') {
  const normalized = String(path || '').trim()
  if (!normalized.startsWith('/management')) return fallback
  return normalized
}

const currentLocationPath = computed(() => {
  if (typeof window === 'undefined') return '/management'
  const pathname = String(window.location.pathname || '/management').trim() || '/management'
  const query = String(window.location.search || '')
  return `${pathname}${query}`
})

const redirectTarget = computed(() => {
  const fallbackFromBoot =
typeof window !== 'undefined'
? normalizeManagementPath(window._BOOT?.login_redirect_to, '/management')
: '/management'

  if (typeof window === 'undefined') return fallbackFromBoot

  const params = new URLSearchParams(String(window.location.search || ''))
  const fromQuery = params.get('redirect_to') || params.get('redirect') || ''
  return normalizeManagementPath(fromQuery, fallbackFromBoot)
})

const loginUrl = computed(() => {
  const loginTarget = isLoginPage.value ? redirectTarget.value : currentLocationPath.value
  return `/management/login?redirect_to=${encodeURIComponent(loginTarget)}`
})

function normalizeScale(scale) {
  const numericScale = Number.isFinite(scale) ? scale : 1
  const stepped = Math.round(numericScale / ZOOM_STEP) * ZOOM_STEP
  return Math.min(ZOOM_MAX, Math.max(ZOOM_MIN, Number(stepped.toFixed(2))))
}

function applyDesktopScale() {
  if (typeof window === 'undefined' || !isDesktop.value) return

  const normalized = normalizeScale(desktopScale.value)

  if (normalized !== desktopScale.value) {
desktopScale.value = normalized
return
  }

  document.documentElement.style.fontSize = `${ZOOM_BASE_FONT_SIZE * normalized}px`
  window.localStorage.setItem(ZOOM_STORAGE_KEY, String(normalized))
}

function clearDesktopScale() {
  if (typeof window === 'undefined') return
  document.documentElement.style.fontSize = ''
}

function syncDesktopState() {
  if (!desktopMedia) return

  isDesktop.value = desktopMedia.matches

  if (isDesktop.value) {
applyDesktopScale()
  } else {
clearDesktopScale()
  }
}

function increaseScale() {
  desktopScale.value = normalizeScale(desktopScale.value + ZOOM_STEP)
}

function decreaseScale() {
  desktopScale.value = normalizeScale(desktopScale.value - ZOOM_STEP)
}

function resetScale() {
  desktopScale.value = 1
}

function initTheme() {
  if (typeof window === 'undefined') return

  const saved = window.localStorage.getItem(THEME_STORAGE_KEY)

  if (saved) {
isDarkMode.value = saved === 'dark'
  } else {
isDarkMode.value = window.matchMedia?.('(prefers-color-scheme: dark)').matches || false
  }

  applyTheme()
}

function applyTheme() {
  if (typeof document === 'undefined') return

  if (isDarkMode.value) {
document.documentElement.classList.add('dark')
  } else {
document.documentElement.classList.remove('dark')
  }
}

function toggleTheme() {
  isDarkMode.value = !isDarkMode.value

  if (typeof window !== 'undefined') {
window.localStorage.setItem(THEME_STORAGE_KEY, isDarkMode.value ? 'dark' : 'light')
  }

  applyTheme()
}

function syncAuthRoute() {
  if (typeof window === 'undefined' || authLoading.value) return

  const currentPath = `${window.location.pathname || ''}${window.location.search || ''}`

  if (authGuest.value) {
if (!isLoginPage.value && currentPath !== loginUrl.value) {
window.location.replace(loginUrl.value)
}
return
  }

  if (isLoginPage.value && currentPath !== redirectTarget.value) {
window.location.replace(redirectTarget.value)
  }
}

async function refreshAuthProfile() {
  authLoading.value = true
  authError.value = ''

  try {
const profile = await getManagementSessionProfile()

authProfile.value = profile || {
user: 'Guest',
full_name: '',
user_image: '',
is_guest: true,
}
  } catch {
authProfile.value = {
user: 'Guest',
full_name: '',
user_image: '',
is_guest: true,
}
  } finally {
authLoading.value = false
  }
}

async function submitLogout() {
  authError.value = ''
  authSubmitting.value = true

  try {
await logoutManagementUser()
await refreshAuthProfile()
  } catch (error) {
authError.value = error.message || 'خروج ناموفق بود.'
  } finally {
authSubmitting.value = false
  }
}

async function handleMobileLogout() {
  await submitLogout()

  if (!authError.value) {
closeMobileMenu()
  }
}

async function handleGuestLoginSuccess() {
  await refreshAuthProfile()
  syncAuthRoute()
}

onMounted(() => {
  initTheme()

  if (typeof window !== 'undefined') {
const storedScale = Number.parseFloat(window.localStorage.getItem(ZOOM_STORAGE_KEY) || '')
const storedRailMode = window.localStorage.getItem(RAIL_STORAGE_KEY)

desktopScale.value = normalizeScale(storedScale)
railMode.value = ['expanded', 'icons'].includes(storedRailMode) ? storedRailMode : 'expanded'

desktopMedia = window.matchMedia(DESKTOP_MEDIA_QUERY)
desktopListener = () => syncDesktopState()

if (desktopMedia.addEventListener) {
desktopMedia.addEventListener('change', desktopListener)
} else if (desktopMedia.addListener) {
desktopMedia.addListener(desktopListener)
}

syncDesktopState()

if (window.history && 'scrollRestoration' in window.history) {
window.history.scrollRestoration = 'manual'
}

window.scrollTo({ top: 0, behavior: 'auto' })

window.requestAnimationFrame(() => {
window.scrollTo({ top: 0, behavior: 'auto' })
})
  }

  refreshAuthProfile()
})

watch(
  activeGroup,
  (group) => {
if (group?.key) {
openGroupKey.value = group.key
}
  },
  { immediate: true },
)

watch(desktopScale, () => {
  applyDesktopScale()
})

watch(railMode, (value) => {
  if (typeof window === 'undefined') return
  window.localStorage.setItem(RAIL_STORAGE_KEY, value)
})

watch(isDesktop, (desktop) => {
  if (desktop) closeMobileMenu()
})

watch(mobileMenuOpen, (open) => {
  if (typeof document === 'undefined') return
  document.body.style.overflow = open ? 'hidden' : ''
})

watch([authLoading, authGuest, isLoginPage, redirectTarget], () => {
  syncAuthRoute()
})

onBeforeUnmount(() => {
  if (desktopMedia && desktopListener) {
if (desktopMedia.removeEventListener) {
desktopMedia.removeEventListener('change', desktopListener)
} else if (desktopMedia.removeListener) {
desktopMedia.removeListener(desktopListener)
}
  }

  if (typeof document !== 'undefined') {
document.body.style.overflow = ''
  }

  clearDesktopScale()
})
</script>

<style scoped>
.management-layout,
.management-auth-shell {
  --bg-page: #f6f1ea;
  --bg-card: #fdf8f1;
  --bg-soft: #f1e7db;
  --border: #d5c3af;
  --text: #3f2a1d;
  --muted: #846b58;
  --muted-2: #9b8472;
  --danger: #dc2626;
  --shadow: 0 20px 45px rgb(63 42 29 / 0.09);
  --shadow-sm: 0 8px 20px rgb(63 42 29 / 0.06);
  min-height: 100vh;
  background:
radial-gradient(circle at 10% 10%, color-mix(in srgb, var(--module-500) 10%, transparent), transparent 38%),
radial-gradient(circle at 88% 84%, color-mix(in srgb, #c98d42 8%, transparent), transparent 42%),
var(--bg-page);
  color: var(--text);
}

:global(.dark) .management-layout,
:global(.dark) .management-auth-shell {
  --bg-page: #111827;
  --bg-card: #1f2937;
  --bg-soft: #374151;
  --border: #374151;
  --text: #f9fafb;
  --muted: #d1d5db;
  --muted-2: #9ca3af;
  --shadow: 0 20px 45px rgb(0 0 0 / 0.26);
  --shadow-sm: 0 8px 20px rgb(0 0 0 / 0.18);
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
  width: 2.35rem;
  height: 2.35rem;
  border-radius: 0.95rem;
  background: linear-gradient(135deg, var(--module-500), var(--module-600));
  display: inline-flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 10px 20px color-mix(in srgb, var(--module-500) 26%, transparent);
  flex-shrink: 0;
}

.icon-button {
  width: 2.4rem;
  height: 2.4rem;
  border: none;
  border-radius: 0.8rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  color: var(--muted);
  cursor: pointer;
  transition: 0.18s ease;
}

.icon-button:hover {
  background: var(--bg-soft);
  color: var(--text);
}

/* Mobile */
.mobile-layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.mobile-header {
  height: 3.5rem;
  padding: 0 1rem;
  border-bottom: 1px solid var(--border);
  background: color-mix(in srgb, var(--bg-card) 94%, transparent);
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
  padding: 0.85rem 0.75rem 5.5rem;
}

.mobile-bottom-nav {
  position: fixed;
  right: 0;
  left: 0;
  bottom: 0;
  z-index: 90;
  height: calc(4rem + env(safe-area-inset-bottom));
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
  min-width: 4rem;
  padding: 0.35rem;
  display: grid;
  justify-items: center;
  align-content: center;
  gap: 0.25rem;
  color: var(--muted);
  font-size: 0.68rem;
}

.bottom-nav-item.active {
  color: var(--module-600);
}

:global(.dark) .bottom-nav-item.active {
  color: var(--module-title-dark);
}

.mobile-overlay {
  position: fixed;
  inset: 0;
  z-index: 110;
  background: rgb(0 0 0 / 0.5);
}

.mobile-sidebar {
  position: fixed;
  top: 0;
  right: 0;
  bottom: 0;
  z-index: 120;
  width: min(86vw, 330px);
  background: var(--bg-card);
  border-left: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  box-shadow: -18px 0 45px rgb(0 0 0 / 0.18);
}

.mobile-sidebar-header {
  height: 4rem;
  padding: 0 1rem;
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.sidebar-title {
  display: inline-flex;
  align-items: center;
  gap: 0.65rem;
}

.sidebar-title div {
  display: grid;
}

.sidebar-title strong {
  font-size: 0.9rem;
}

.sidebar-title small {
  color: var(--muted);
  font-size: 0.7rem;
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
width: 16rem;
height: 100vh;
position: sticky;
top: 0;
border-left: 1px solid var(--border);
background: color-mix(in srgb, var(--bg-card) 96%, transparent);
display: flex;
flex-direction: column;
transition: width 0.22s ease;
  }

  .management-layout.rail-collapsed .desktop-sidebar {
width: 5.8rem;
  }

  .sidebar-logo-block {
min-height: 4rem;
padding: 0.75rem 1rem;
border-bottom: 1px solid var(--border);
display: grid;
gap: 0.65rem;
  }

  .rail-mini-toggle {
width: 2rem;
height: 2rem;
justify-self: start;
border: 1px solid var(--border);
border-radius: 0.75rem;
background: var(--bg-soft);
color: var(--text);
cursor: pointer;
display: inline-flex;
align-items: center;
justify-content: center;
  }

  .rail-brand {
display: flex;
align-items: center;
gap: 0.7rem;
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

  .desktop-header {
height: 3.5rem;
border-bottom: 1px solid var(--border);
background: color-mix(in srgb, var(--bg-card) 96%, transparent);
padding: 0 1.5rem;
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
font-size: 0.95rem;
font-weight: 900;
  }

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
padding: 1rem;
  }

  .desktop-main > :deep(*) {
max-width: 1320px;
margin-inline: auto;
  }
}

/* Accordion Nav */
.accordion-nav {
  padding: 1rem;
  overflow: auto;
  display: grid;
  gap: 0.55rem;
  align-content: start;
}

.desktop-nav {
  flex: 1;
}

.nav-group {
  border: 1px solid var(--border);
  border-radius: 0.95rem;
  overflow: hidden;
  background: var(--bg-card);
}

.group-button {
  width: 100%;
  border: 0;
  background: transparent;
  color: var(--text);
  padding: 0.62rem 0.65rem;
  display: flex;
  align-items: center;
  gap: 0.65rem;
  cursor: pointer;
  font-weight: 800;
  font-size: 0.84rem;
  transition: 0.18s ease;
}

.group-button:hover,
.group-button.active {
  background: var(--module-50);
  color: var(--module-title-light);
}

:global(.dark) .group-button:hover,
:global(.dark) .group-button.active {
  background: color-mix(in srgb, var(--module-500) 16%, transparent);
  color: var(--module-title-dark);
}

.group-icon,
.item-icon {
  width: 2rem;
  height: 2rem;
  border-radius: 0.7rem;
  background: var(--bg-soft);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.group-button.active .group-icon {
  background: var(--module-500);
  color: white;
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
  padding: 0.35rem 0.5rem 0.55rem;
  display: grid;
  gap: 0.25rem;
}

.nav-item {
  border-radius: 0.75rem;
  padding: 0.42rem 0.5rem;
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
  box-shadow: 0 8px 16px color-mix(in srgb, var(--module-500) 12%, transparent);
}

:global(.dark) .nav-item.active {
  background: color-mix(in srgb, var(--module-500) 16%, transparent);
  color: var(--module-title-dark);
}

.nav-item.active .item-icon {
  background: var(--module-500);
  color: white;
}

.item-label {
  display: grid;
  gap: 0.06rem;
  flex: 1;
  min-width: 0;
}

.item-label strong {
  font-size: 0.8rem;
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
  padding: 0.85rem 1rem;
  display: grid;
  gap: 0.65rem;
}

.customer-site-link,
.theme-toggle {
  min-height: 2.35rem;
  border: 1px solid var(--border);
  border-radius: 0.8rem;
  background: var(--bg-soft);
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
  border-radius: 0.95rem;
  background: color-mix(in srgb, var(--bg-soft) 72%, transparent);
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
  padding: 0.5rem 0.85rem;
  font-size: 0.75rem;
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
  margin: auto 1rem 1rem;
}
</style>
