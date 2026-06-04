<template>
  <div class="management-root" v-if="isManagement">
    <ManagementLayout :page="page" :brand-name="branding.name">
      <ManagementDashboardPage v-if="page === 'management-dashboard'" />
      <ManagementPosPage v-else-if="page === 'management-pos'" />
      <ManagementPosProfilePage v-else-if="page === 'management-pos-profile'" />
      <ManagementOrdersPage v-else-if="page === 'management-orders'" />
      <ManagementProductsPage v-else-if="page === 'management-products'" />
      <ManagementMenuGroupsPage v-else-if="page === 'management-menu-groups'" />
      <ManagementMenuGroupDetailPage v-else-if="page === 'management-menu-group'" />
      <ManagementSiteSettingsPage v-else-if="page === 'management-site-settings'" />
      <ManagementBomsPage v-else-if="page === 'management-boms'" />
      <ManagementBomDetailPage v-else-if="page === 'management-bom'" />
      <ManagementProductDetailPage v-else-if="page === 'management-product'" :boot="boot" />
      <ManagementVariantBuilderPage v-else-if="page === 'management-variant-builder'" />
      <ManagementCustomersPage v-else-if="page === 'management-customers'" />
      <ManagementReportsIndexPage v-else-if="page === 'management-reports'" />
      <ManagementReportPage v-else-if="page === 'management-report'" :boot="boot" />
      <ManagementPrintFormatsPage v-else-if="page === 'management-print-formats'" />
      <ManagementSettingsPage v-else-if="page === 'management-settings'" />
      <section v-else-if="page === 'management-login'" class="management-login-placeholder"></section>
      <ManagementDashboardPage v-else />
    </ManagementLayout>
  </div>

  <div class="app-layout" :class="`page-${page}`" v-else>
    <AppHeader
      :branding="branding"
      :page="page"
      :cart-count="cartCount"
      :has-last-order="hasLastOrder"
      :last-order-url="lastOrderUrl"
    />

    <main class="app-main">
      <RestaurantLandingPage v-if="page === 'landing'" :boot="boot" />
      <AboutUsPage v-else-if="page === 'about-us'" :boot="boot" />
      <FaqPage v-else-if="page === 'faq'" :boot="boot" />
      <MenuPage v-else-if="page === 'menu'" :boot="boot" />
      <ItemDetailPage v-else-if="page === 'item'" :boot="boot" />
      <CartPage v-else-if="page === 'cart'" />
      <OrderSuccessPage v-else-if="page === 'order-success'" :boot="boot" />
      <MenuPage v-else :boot="boot" />
    </main>

    <AppFooter :branding="branding" :has-last-order="hasLastOrder" :last-order-url="lastOrderUrl" />

    <MobileBottomNav
      :page="page"
      :cart-count="cartCount"
      :has-last-order="hasLastOrder"
      :last-order-url="lastOrderUrl"
    />
  </div>

  <SiteLoaderOverlay v-if="!isManagement" :settings="loaderSettings" />
</template>

<script setup>
import { computed } from 'vue'
import AppHeader from './components/AppHeader.vue'
import AppFooter from './components/AppFooter.vue'
import MobileBottomNav from './components/MobileBottomNav.vue'
import RestaurantLandingPage from './pages/RestaurantLandingPage.vue'
import AboutUsPage from './pages/AboutUsPage.vue'
import FaqPage from './pages/FaqPage.vue'
import MenuPage from './pages/MenuPage.vue'
import ItemDetailPage from './pages/ItemDetailPage.vue'
import CartPage from './pages/CartPage.vue'
import OrderSuccessPage from './pages/OrderSuccessPage.vue'
import ManagementLayout from './components/management/ManagementLayout.vue'
import ManagementDashboardPage from './pages/management/ManagementDashboardPage.vue'
import ManagementPosPage from './pages/management/ManagementPosPage.vue'
import ManagementPosProfilePage from './pages/management/ManagementPosProfilePage.vue'
import ManagementOrdersPage from './pages/management/ManagementOrdersPage.vue'
import ManagementProductsPage from './pages/management/ManagementProductsPage.vue'
import ManagementMenuGroupsPage from './pages/management/ManagementMenuGroupsPage.vue'
import ManagementMenuGroupDetailPage from './pages/management/ManagementMenuGroupDetailPage.vue'
import ManagementSiteSettingsPage from './pages/management/ManagementSiteSettingsPage.vue'
import ManagementBomsPage from './pages/management/ManagementBomsPage.vue'
import ManagementBomDetailPage from './pages/management/ManagementBomDetailPage.vue'
import ManagementProductDetailPage from './pages/management/ManagementProductDetailPage.vue'
import ManagementVariantBuilderPage from './pages/management/ManagementVariantBuilderPage.vue'
import ManagementCustomersPage from './pages/management/ManagementCustomersPage.vue'
import ManagementReportsIndexPage from './pages/management/ManagementReportsIndexPage.vue'
import ManagementReportPage from './pages/management/ManagementReportPage.vue'
import ManagementPrintFormatsPage from './pages/management/ManagementPrintFormatsPage.vue'
import ManagementSettingsPage from './pages/management/ManagementSettingsPage.vue'
import SiteLoaderOverlay from './components/SiteLoaderOverlay.vue'
import { cartState } from './stores/cartStore'
import { resolveLoaderSettingsFromBoot } from './utils/loaderSettings'

function resolveInitialPage() {
  if (typeof window !== 'undefined') {
    const pathname = String(window.location.pathname || '')
    const params = new URLSearchParams(String(window.location.search || ''))
    const variantStudioMode = ['1', 'true', 'yes'].includes(String(params.get('variant_studio') || '').toLowerCase())

    if (pathname.startsWith('/management/login')) return 'management-login'
    if (pathname === '/management' || pathname === '/management/') return 'management-dashboard'
    if (pathname.startsWith('/management/dashboard')) return 'management-dashboard'
    if (pathname.startsWith('/management/pos-profile') || pathname.startsWith('/management/pos_profile')) return 'management-pos-profile'
    if (pathname.startsWith('/management/pos')) return 'management-pos'
    if (pathname.startsWith('/management/orders')) return 'management-orders'
    if (pathname.startsWith('/management/products/detail') && variantStudioMode) return 'management-variant-builder'
    if (pathname.startsWith('/management/product') && variantStudioMode) return 'management-variant-builder'
    if (pathname.startsWith('/management/products')) return 'management-products'
    if (pathname.startsWith('/management/product')) return 'management-product'
    if (pathname.startsWith('/management/menu-groups') || pathname.startsWith('/management/menu_groups')) return 'management-menu-groups'
    if (pathname.startsWith('/management/menu-group') || pathname.startsWith('/management/menu_group')) return 'management-menu-group'
    if (pathname.startsWith('/management/boms')) return 'management-boms'
    if (pathname.startsWith('/management/bom')) return 'management-bom'
    if (pathname.startsWith('/management/customers')) return 'management-customers'
    if (pathname.startsWith('/management/reports/')) return 'management-report'
    if (pathname.startsWith('/management/reports')) return 'management-reports'
    if (pathname.startsWith('/management/print-formats') || pathname.startsWith('/management/print_formats')) return 'management-print-formats'
    if (pathname.startsWith('/management/site-settings') || pathname.startsWith('/management/site_settings')) return 'management-site-settings'
    if (pathname.startsWith('/management/variant-builder') || pathname.startsWith('/management/variant_builder')) return 'management-variant-builder'
    if (pathname.startsWith('/management/settings')) return 'management-settings'

    if (pathname === '/' || pathname === '') return 'landing'
    if (pathname.startsWith('/menu')) return 'menu'
    if (pathname.startsWith('/item')) return 'item'
    if (pathname.startsWith('/cart')) return 'cart'
    if (pathname.startsWith('/about-us') || pathname.startsWith('/about_us')) return 'about-us'
    if (pathname.startsWith('/faq')) return 'faq'
    if (pathname.startsWith('/order-success') || pathname.startsWith('/order_success')) return 'order-success'
  }
  return window._PAGE || 'landing'
}

const page = resolveInitialPage()
const boot = window._BOOT || {}
const isManagement = computed(() => String(page || '').startsWith('management-'))
const loaderSettings = computed(() => resolveLoaderSettingsFromBoot(boot))

const branding = computed(() => {
  const fromBoot = boot.branding || {}
  return {
    name: fromBoot.name || 'Veederakht Restaurant',
    tagline: fromBoot.tagline || 'منوی آنلاین تازه و قابل شخصی سازی',
    hero_subtitle: fromBoot.hero_subtitle || '',
  }
})

const cartCount = computed(() => cartState.lines.reduce((sum, line) => sum + (Number(line.qty) || 0), 0))

const hasLastOrder = computed(() => Boolean(cartState.lastOrder?.order_code && cartState.lastOrder?.mobile))

const lastOrderUrl = computed(() => {
  const orderCode = cartState.lastOrder?.order_code || ''
  const mobile = cartState.lastOrder?.mobile || ''
  if (!orderCode || !mobile) {
    return '/menu'
  }
  return `/order-success/${encodeURIComponent(orderCode)}?mobile=${encodeURIComponent(mobile)}`
})
</script>

<style scoped>
.app-layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.app-main {
  flex: 1;
  padding-top: 5.35rem;
}

.management-login-placeholder {
  min-height: 1px;
}

@media (max-width: 920px) {
  .app-main {
    padding-top: 5rem;
  }
}

@media print {
  .app-layout.page-menu :deep(.app-header),
  .app-layout.page-menu :deep(.app-footer),
  .app-layout.page-menu :deep(.mobile-bottom-nav),
  .app-layout.page-menu :deep(.sticky-cart),
  .app-layout.page-menu :deep(.blob) {
    display: none !important;
  }

  .app-layout.page-menu .app-main {
    padding-top: 0 !important;
  }
}
</style>
