<template>
  <div class="management-root" v-if="isManagement">
    <ManagementLayout :page="page" :brand-name="branding.name">
      <ManagementDashboardPage v-if="page === 'management-dashboard'" />
      <ManagementPosPage v-else-if="page === 'management-pos'" />
      <ManagementPosProfilePage v-else-if="page === 'management-pos-profile'" />
      <ManagementOrdersPage v-else-if="page === 'management-orders'" />
      <ManagementProductsPage v-else-if="page === 'management-products'" />
      <ManagementMenuDesignerPage v-else-if="page === 'management-menu-design'" />
      <ManagementMenuGroupsPage v-else-if="page === 'management-menu-groups'" />
      <ManagementMenuGroupDetailPage v-else-if="page === 'management-menu-group'" />
      <ManagementSiteSettingsPage v-else-if="page === 'management-site-settings'" />
      <ManagementBomsPage v-else-if="page === 'management-boms'" />
      <ManagementBomDetailPage v-else-if="page === 'management-bom'" />
      <ManagementProductDetailPage v-else-if="page === 'management-product'" :boot="boot" />
      <ManagementVariantBuilderPage v-else-if="page === 'management-variant-builder'" />
      <ManagementBuilderTemplatesPage v-else-if="page === 'management-builder-templates' && !isBuilderTemplateEdit" />
      <ManagementBuilderTemplatePage v-else-if="page === 'management-builder-templates' && isBuilderTemplateEdit" :template-id="builderTemplateId" />
      <ManagementCustomersPage v-else-if="page === 'management-customers'" />
      <ManagementTablesPage v-else-if="page === 'management-tables'" />
      <ManagementReportsIndexPage v-else-if="page === 'management-reports'" />
      <ManagementReportPage v-else-if="page === 'management-report'" :boot="boot" />
      <ManagementPrintFormatsPage v-else-if="page === 'management-print-formats'" />
      <ManagementSettingsPage v-else-if="page === 'management-settings'" />
      <ManagementZarinpalSettingsPage v-else-if="page === 'management-zarinpal-settings'" />
      <section v-else-if="page === 'management-login'" class="management-login-placeholder"></section>
      <ManagementDashboardPage v-else />
    </ManagementLayout>
  </div>

  <div class="app-layout" :class="`page-${page}`" v-else>
    <PublicHeader
      v-if="page !== 'landing' && !isCustomerPage && page !== 'checkout' && page !== 'payment-fail' && page !== 'not-found' && page !== 'kitchen'"
      :branding="branding"
      :page="page"
      :cart-count="cartCount"
      :has-last-order="hasLastOrder"
      :last-order-url="lastOrderUrl"
      :header-variant="headerVariant"
    />

    <main
      class="app-main"
      :class="{ 'app-main--no-offset': useNoHeaderOffset }"
    >
      <RestaurantLandingPage v-if="page === 'landing'" :boot="boot" />
      <AboutUsPage v-else-if="page === 'about-us'" :boot="boot" />
      <FaqPage v-else-if="page === 'faq'" :boot="boot" />
      <MenuPage v-else-if="page === 'menu'" :boot="boot" />
      <CustomerSearchPage v-else-if="page === 'search'" />
      <ItemDetailPage v-else-if="page === 'item'" :boot="boot" />
      <CartPage v-else-if="page === 'cart'" />
      <CustomizePage v-else-if="page === 'customize'" :boot="boot" />
      <BomPreviewPage v-else-if="page === 'bom-preview'" :boot="boot" />
      <PaymentGatewayEntry v-else-if="page === 'payment'" :boot="boot" />
      <PaymentCallback v-else-if="page === 'payment-callback'" :boot="boot" />
      <OrderSuccessPage v-else-if="page === 'order-success'" :boot="boot" />
      <OrderStartPage v-else-if="page === 'order-start'" />
      <OrderTypePage v-else-if="page === 'order-type'" />
      <OrderDineInPage v-else-if="page === 'order-dine-in'" />
      <OrderPickupPage v-else-if="page === 'order-pickup'" />
      <OrderDeliveryPage v-else-if="page === 'order-delivery'" />
      <CustomerLoginPage v-else-if="page === 'customer-login'" />
      <CustomerDashboardPage v-else-if="page === 'customer-dashboard'" />
      <CustomerProfilePage v-else-if="page === 'customer-profile'" />
      <CustomerAddressesPage v-else-if="page === 'customer-addresses'" />
      <CustomerBranchesPage v-else-if="page === 'customer-branches'" />
      <CustomerOrdersPage v-else-if="page === 'customer-orders'" />
      <CustomerOrderDetailPage v-else-if="page === 'customer-order-detail'" />
      <CustomerDeliveryPage v-else-if="page === 'customer-delivery'" />
      <CustomerTableReservationPage v-else-if="page === 'customer-table-reservation'" />
      <CustomerTableSelectPage v-else-if="page === 'customer-table-select'" />
      <CheckoutPage v-else-if="page === 'checkout'" />
      <PaymentFailPage v-else-if="page === 'payment-fail'" />
      <KitchenDisplayPage v-else-if="page === 'kitchen'" />
      <NotFoundPage v-else-if="page === 'not-found'" />
      <NotFoundPage v-else />
    </main>

    <SiteFooter
      v-if="page !== 'landing' && !isCustomerPage && !isFullscreenPage && siteComponents.footer_variant === 'full'"
      :brand-name="branding.name"
      :description="branding.footer_description || branding.hero_subtitle"
      :phone="branding.footer_phone"
      :email="branding.footer_email"
      :address="branding.footer_address"
      :instagram="branding.footer_instagram"
      :telegram="branding.footer_telegram"
      :copyright="branding.footer_copyright"
    />
    <SiteFooterMinimal
      v-else-if="page !== 'landing' && !isCustomerPage && !isFullscreenPage && siteComponents.footer_variant === 'minimal'"
      :brand-name="branding.name"
      :copyright="branding.footer_copyright"
    />

    <MobileBottomNav
      v-if="!isFullscreenPage && page !== 'kitchen'"
      :page="page"
      :cart-count="cartCount"
      :has-last-order="hasLastOrder"
      :last-order-url="lastOrderUrl"
    />
    <PwaInstallPrompt />
  </div>

  <SiteLoaderOverlay v-if="!isManagement && !isCustomerPage && !isFullscreenPage" :settings="loaderSettings" />
  <GlobalSearchModal />
</template>

<script setup>
import { computed, reactive } from 'vue'
import MobileBottomNav from './components/MobileBottomNav.vue'
import PublicHeader from './components/PublicHeader.vue'
import PwaInstallPrompt from './components/PwaInstallPrompt.vue'
import SiteFooter from './components/SiteFooter.vue'
import SiteFooterMinimal from './components/SiteFooterMinimal.vue'
import RestaurantLandingPage from './pages/RestaurantLandingPage.vue'
import AboutUsPage from './pages/AboutUsPage.vue'
import FaqPage from './pages/FaqPage.vue'
import MenuPage from './pages/MenuPage.vue'
import CustomerSearchPage from './pages/CustomerSearchPage.vue'
import ItemDetailPage from './pages/ItemDetailPage.vue'
import CartPage from './pages/CartPage.vue'
import CustomizePage from './pages/CustomizePage.vue'
import BomPreviewPage from './pages/BomPreviewPage.vue'
import PaymentGatewayEntry from './pages/PaymentGatewayEntry.vue'
import PaymentCallback from './pages/PaymentCallback.vue'
import OrderSuccessPage from './pages/OrderSuccessPage.vue'
import OrderStartPage from './pages/OrderStartPage.vue'
import OrderTypePage from './pages/OrderTypePage.vue'
import OrderDineInPage from './pages/OrderDineInPage.vue'
import OrderPickupPage from './pages/OrderPickupPage.vue'
import OrderDeliveryPage from './pages/OrderDeliveryPage.vue'
import CustomerLoginPage from './pages/CustomerLoginPage.vue'
import CustomerDashboardPage from './pages/CustomerDashboardPage.vue'
import CustomerProfilePage from './pages/CustomerProfilePage.vue'
import CustomerAddressesPage from './pages/CustomerAddressesPage.vue'
import CustomerBranchesPage from './pages/CustomerBranchesPage.vue'
import CustomerOrdersPage from './pages/CustomerOrdersPage.vue'
import CustomerOrderDetailPage from './pages/CustomerOrderDetailPage.vue'
import CustomerDeliveryPage from './pages/CustomerDeliveryPage.vue'
import CustomerTableReservationPage from './pages/CustomerTableReservationPage.vue'
import CustomerTableSelectPage from './pages/CustomerTableSelectPage.vue'
import CheckoutPage from './pages/CheckoutPage.vue'
import PaymentFailPage from './pages/PaymentFailPage.vue'
import NotFoundPage from './pages/NotFoundPage.vue'
import KitchenDisplayPage from './pages/KitchenDisplayPage.vue'
import ManagementLayout from './components/management/ManagementLayout.vue'
import ManagementDashboardPage from './pages/management/ManagementDashboardPage.vue'
import ManagementPosPage from './pages/management/ManagementPosPage.vue'
import ManagementPosProfilePage from './pages/management/ManagementPosProfilePage.vue'
import ManagementOrdersPage from './pages/management/ManagementOrdersPage.vue'
import ManagementProductsPage from './pages/management/ManagementProductsPage.vue'
import ManagementMenuDesignerPage from './pages/management/ManagementMenuDesignerPage.vue'
import ManagementMenuGroupsPage from './pages/management/ManagementMenuGroupsPage.vue'
import ManagementMenuGroupDetailPage from './pages/management/ManagementMenuGroupDetailPage.vue'
import ManagementSiteSettingsPage from './pages/management/ManagementSiteSettingsPage.vue'
import ManagementBomsPage from './pages/management/ManagementBomsPage.vue'
import ManagementBomDetailPage from './pages/management/ManagementBomDetailPage.vue'
import ManagementProductDetailPage from './pages/management/ManagementProductDetailPage.vue'
import ManagementVariantBuilderPage from './pages/management/ManagementVariantBuilderPage.vue'
import ManagementBuilderTemplatesPage from './pages/management/ManagementBuilderTemplatesPage.vue'
import ManagementBuilderTemplatePage from './pages/management/ManagementBuilderTemplatePage.vue'
import ManagementCustomersPage from './pages/management/ManagementCustomersPage.vue'
import ManagementTablesPage from './pages/management/ManagementTablesPage.vue'
import ManagementReportsIndexPage from './pages/management/ManagementReportsIndexPage.vue'
import ManagementReportPage from './pages/management/ManagementReportPage.vue'
import ManagementPrintFormatsPage from './pages/management/ManagementPrintFormatsPage.vue'
import ManagementSettingsPage from './pages/management/ManagementSettingsPage.vue'
import ManagementZarinpalSettingsPage from './pages/management/ManagementZarinpalSettingsPage.vue'
import SiteLoaderOverlay from './components/SiteLoaderOverlay.vue'
import GlobalSearchModal from './components/GlobalSearchModal.vue'
import { cartState } from './stores/cartStore'
import { resolveLoaderSettingsFromBoot } from './utils/loaderSettings'
import { resolveBranding, resolveSiteComponents } from './utils/siteComponents'

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
    if (pathname.startsWith('/management/menu-design') || pathname.startsWith('/management/menu_design')) return 'management-menu-design'
    if (pathname.startsWith('/management/menu-groups') || pathname.startsWith('/management/menu_groups')) return 'management-menu-groups'
    if (pathname.startsWith('/management/menu-group') || pathname.startsWith('/management/menu_group')) return 'management-menu-group'
    if (pathname.startsWith('/management/boms')) return 'management-boms'
    if (pathname.startsWith('/management/bom')) return 'management-bom'
    if (pathname.startsWith('/management/customers')) return 'management-customers'
    if (pathname.startsWith('/management/tables')) return 'management-tables'
    if (pathname.startsWith('/management/reports/')) return 'management-report'
    if (pathname.startsWith('/management/reports')) return 'management-reports'
    if (pathname.startsWith('/management/print-formats') || pathname.startsWith('/management/print_formats')) return 'management-print-formats'
    if (pathname.startsWith('/management/site-settings') || pathname.startsWith('/management/site_settings')) return 'management-site-settings'
    if (pathname.startsWith('/management/variant-builder') || pathname.startsWith('/management/variant_builder')) return 'management-variant-builder'
    if (pathname.startsWith('/management/builder-template')) return 'management-builder-templates'
    if (pathname.startsWith('/management/zarinpal-settings') || pathname.startsWith('/management/zarinpal_settings')) return 'management-zarinpal-settings'
    if (pathname.startsWith('/management/settings')) return 'management-settings'

    if (pathname === '/' || pathname === '') return 'landing'
    if (pathname.startsWith('/menu')) return 'menu'
    if (pathname.startsWith('/search')) return 'search'
    if (pathname.startsWith('/item')) return 'item'
    if (pathname.startsWith('/cart')) return 'cart'
    if (pathname.startsWith('/about-us') || pathname.startsWith('/about_us')) return 'about-us'
    if (pathname.startsWith('/faq')) return 'faq'
    if (pathname.startsWith('/order-success') || pathname.startsWith('/order_success')) return 'order-success'
    if (pathname === '/order' || pathname === '/order/' || pathname.startsWith('/order/start')) return 'order-start'
    if (pathname.startsWith('/order/type')) return 'order-type'
    if (pathname.startsWith('/order/dine-in') || pathname.startsWith('/order/dine_in')) return 'order-dine-in'
    if (pathname.startsWith('/order/pickup')) return 'order-pickup'
    if (pathname.startsWith('/order/delivery')) return 'order-delivery'
    if (pathname.startsWith('/customize/')) return 'customize'
    if (pathname.startsWith('/customer/login')) return 'customer-login'
    if (pathname.startsWith('/customer/dashboard')) return 'customer-dashboard'
    if (pathname.startsWith('/customer/profile')) return 'customer-profile'
    if (pathname.startsWith('/customer/addresses')) return 'customer-addresses'
    if (pathname.startsWith('/customer/branches')) return 'customer-branches'
    if (pathname.startsWith('/customer/orders/')) return 'customer-order-detail'
    if (pathname.startsWith('/customer/orders')) return 'customer-orders'
    if (pathname.startsWith('/delivery')) {
      window.location.replace('/order/delivery')
      return 'order-delivery'
    }
    if (pathname.startsWith('/table-reservation')) return 'customer-table-reservation'
    if (pathname.startsWith('/table-select')) {
      window.location.replace('/order/dine-in')
      return 'order-dine-in'
    }
    if (pathname.startsWith('/checkout')) return 'checkout'
    if (pathname.startsWith('/payment/fail') || pathname.startsWith('/payment-fail')) return 'payment-fail'
    if (pathname.startsWith('/kitchen')) return 'kitchen'
    if (pathname.startsWith('/payment/callback')) return 'payment-callback'
    if (pathname.startsWith('/payment/')) return 'payment'
    if (pathname.startsWith('/bom-preview/')) return 'bom-preview'
    if (pathname.startsWith('/404') || pathname.startsWith('/not-found')) return 'not-found'
  }
  return window._PAGE || 'landing'
}

const page = resolveInitialPage()
const boot = reactive(window._BOOT || {})
window._BOOT = boot
const isManagement = computed(() => String(page || '').startsWith('management-'))
const isBuilderTemplateEdit = computed(() => {
  if (typeof window === 'undefined') return false
  const pathname = String(window.location.pathname || '')
  return pathname.startsWith('/management/builder-template/edit/') || pathname === '/management/builder-template/new'
})
const builderTemplateId = computed(() => {
  if (typeof window === 'undefined') return ''
  const pathname = String(window.location.pathname || '')
  const match = pathname.match(/\/management\/builder-template\/edit\/(.+)/)
  return match ? match[1] : ''
})
const loaderSettings = computed(() => resolveLoaderSettingsFromBoot(boot))
const branding = computed(() => resolveBranding(boot))
const siteComponents = computed(() => resolveSiteComponents(boot))

const cartCount = computed(() => cartState.lines.reduce((sum, line) => sum + (Number(line.qty) || 0), 0))

const headerVariant = computed(() => {
  return siteComponents.value.header_variant
})

const isMobile = computed(() => {
  if (typeof window === 'undefined') return false
  return window.innerWidth < 920
})

const hasLastOrder = computed(() => Boolean(cartState.lastOrder?.order_code && cartState.lastOrder?.mobile))

const isOrderFlowPage = page.startsWith('order-') && page !== 'order-success'
const isCustomerPage = page.startsWith('customer-') || page === 'customer-delivery' || page === 'customer-table-reservation' || page === 'customer-table-select'

const isFullscreenPage = page === 'checkout' || isOrderFlowPage || page === 'payment-fail' || page === 'not-found' || page === 'kitchen'

const useNoHeaderOffset = computed(() => {
  return page === 'landing' || isCustomerPage || isFullscreenPage
})

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
  padding-top: 6.5rem;
}

.app-main--no-offset,
.app-main.app-main--no-offset {
  padding-top: 0;
}

.management-login-placeholder {
  min-height: 1px;
}

@media (max-width: 920px) {
  .app-main {
    padding-top: 3.75rem;
  }

  .app-main.app-main--no-offset {
    padding-top: 0;
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
