<template>
  <div class="management-root" v-if="isManagement">
    <ManagementLayout :page="page" :brand-name="branding.name">
      <ManagementDashboardPage v-if="page === 'management-dashboard'" />
      <ManagementSalesDashboardPage v-else-if="page === 'management-sales-dashboard'" />
      <ManagementPosPage v-else-if="page === 'management-pos'" />
      <ManagementPosProfilePage v-else-if="page === 'management-pos-profile'" />
      <ManagementPosDefaultsPage v-else-if="page === 'management-pos-defaults'" />
      <ManagementCouriersPage v-else-if="page === 'management-couriers'" />
      <ManagementUserDetailPage v-else-if="page === 'management-user-detail'" />
      <ManagementUsersPage v-else-if="page === 'management-users'" />
      <ManagementOrderDetailPage v-else-if="page === 'management-order-detail'" />
      <ManagementOrdersPage v-else-if="page === 'management-orders'" />
      <ManagementProductsPage v-else-if="page === 'management-products'" />
      <ManagementDesignSystemPage v-else-if="page === 'management-design-system'" />
      <ManagementModifierGroupsPage v-else-if="page === 'management-modifier-groups'" />
      <ManagementMenuDesignerPage v-else-if="page === 'management-menu-design'" />
      <ManagementMenuGroupsPage v-else-if="page === 'management-menu-groups'" />
      <ManagementMenuGroupDetailPage v-else-if="page === 'management-menu-group'" />
      <ManagementSiteSettingsPage v-else-if="page === 'management-site-settings'" />
      <ManagementSiteSettingsPage v-else-if="page === 'management-home-builder'" entry-mode="home-builder" />
      <ManagementBomsPage v-else-if="page === 'management-boms'" />
      <ManagementBomDetailPage v-else-if="page === 'management-bom'" />
      <ManagementProductDetailPage v-else-if="page === 'management-product'" :boot="boot" />
      <ManagementVariantBuilderPage v-else-if="page === 'management-variant-builder'" />
      <ManagementBuilderTemplatesPage v-else-if="page === 'management-builder-templates' && !isBuilderTemplateEdit" />
      <ManagementBuilderTemplatePage v-else-if="page === 'management-builder-templates' && isBuilderTemplateEdit" :template-id="builderTemplateId" />
      <ManagementCustomerDetailPage v-else-if="page === 'management-customer-detail'" />
      <ManagementCustomersPage v-else-if="page === 'management-customers'" />
      <ManagementKitchenPage v-else-if="page === 'management-kitchen'" />
      <ManagementTablesPage v-else-if="page === 'management-tables'" />
      <ManagementReportsIndexPage v-else-if="page === 'management-reports'" />
      <ManagementReportPage v-else-if="page === 'management-report'" :boot="boot" />
      <ManagementRegisterPage v-else-if="page === 'management-register'" />
      <ManagementInventoryDashboardPage v-else-if="page === 'management-inventory-dashboard'" />
      <ManagementInventoryMaterialsPage v-else-if="page === 'management-inventory-materials'" />
      <ManagementInventoryMaterialDetailPage v-else-if="page === 'management-inventory-material-detail'" />
      <ManagementMaterialRequestsPage v-else-if="page === 'management-material-requests'" />
      <ManagementMaterialRequestDetailPage v-else-if="page === 'management-material-request-detail'" />
      <ManagementInventoryPurchasesPage v-else-if="page === 'management-inventory-purchases'" />
      <ManagementInventoryPurchaseDetailPage v-else-if="page === 'management-inventory-purchase-detail'" />
      <ManagementInventoryWarehousesPage v-else-if="page === 'management-inventory-warehouses'" />
      <ManagementInventoryMovementsPage v-else-if="page === 'management-inventory-movements'" />
      <ManagementProductStockLedgerPage v-else-if="page === 'management-inventory-ledger'" />
      <ManagementInventoryReorderPage v-else-if="page === 'management-inventory-reorder'" />
      <ManagementInventoryProductionPage v-else-if="page === 'management-inventory-production'" />
      <ManagementInventoryLossesPage v-else-if="page === 'management-inventory-losses'" />
      <ManagementInventoryDocumentsPage v-else-if="page === 'management-inventory-documents'" />
      <ManagementInventoryDocumentDetailPage v-else-if="page === 'management-inventory-document-detail'" />
      <ManagementInventoryCountPage v-else-if="page === 'management-inventory-count'" />
      <ManagementInventoryCountDetailPage v-else-if="page === 'management-inventory-count-detail'" />
      <ManagementInventoryCostsPage v-else-if="page === 'management-inventory-costs'" />
      <ManagementInventoryPage v-else-if="page === 'management-inventory'" />
      <ManagementClubPage v-else-if="page === 'management-club'" />
      <ManagementSurveysPage v-else-if="page === 'management-surveys'" />
      <ManagementCostControlPage v-else-if="page === 'management-cost-control'" />
      <ManagementReservationsPage v-else-if="page === 'management-reservations'" />
      <ManagementBranchesPage v-else-if="page === 'management-branches'" />
      <ManagementCallCenterPage v-else-if="page === 'management-call-center'" />
      <ManagementAccountingPage v-else-if="page === 'management-accounting'" />
      <ManagementHelpPage v-else-if="page === 'management-help'" />
      <ManagementPrintFormatsPage v-else-if="page === 'management-print-formats'" />
      <ManagementSiteSettingsPage v-else-if="page === 'management-settings'" entry-mode="theme-settings" />
      <ManagementZarinpalSettingsPage v-else-if="page === 'management-zarinpal-settings'" />
      <ManagementSnappfoodPage v-else-if="page === 'management-snappfood'" />
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
      <ProductGroupsPage v-else-if="page === 'product-groups'" :boot="boot" />
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
      <KitchenDisplayPage v-else-if="page === 'kitchen' || page === 'management-kitchen'" />
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
      v-if="!isFullscreenPage && page !== 'kitchen' && page !== 'item'"
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
import ProductGroupsPage from './pages/ProductGroupsPage.vue'
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
import ManagementDashboardPage from './pages/management/dashboard/ManagementDashboardPage.vue'
import ManagementSalesDashboardPage from './pages/management/sales/ManagementSalesDashboardPage.vue'
import ManagementPosPage from './pages/management/sales/ManagementPosPage.vue'
import ManagementPosProfilePage from './pages/management/sales/ManagementPosProfilePage.vue'
import ManagementPosDefaultsPage from './pages/management/sales/ManagementPosDefaultsPage.vue'
import ManagementCouriersPage from './pages/management/operations/ManagementCouriersPage.vue'
import ManagementUsersPage from './pages/management/settings/ManagementUsersPage.vue'
import ManagementUserDetailPage from './pages/management/settings/ManagementUserDetailPage.vue'
import ManagementOrdersPage from './pages/management/sales/ManagementOrdersPage.vue'
import ManagementOrderDetailPage from './pages/management/sales/ManagementOrderDetailPage.vue'
import ManagementProductsPage from './pages/management/catalog/ManagementProductsPage.vue'
import ManagementDesignSystemPage from './pages/management/design-system/ManagementDesignSystemPage.vue'
import ManagementModifierGroupsPage from './pages/management/catalog/ManagementModifierGroupsPage.vue'
import ManagementMenuDesignerPage from './pages/management/catalog/ManagementMenuDesignerPage.vue'
import ManagementMenuGroupsPage from './pages/management/catalog/ManagementMenuGroupsPage.vue'
import ManagementMenuGroupDetailPage from './pages/management/catalog/ManagementMenuGroupDetailPage.vue'
import ManagementSiteSettingsPage from './pages/management/settings/ManagementSiteSettingsPage.vue'
import ManagementBomsPage from './pages/management/catalog/ManagementBomsPage.vue'
import ManagementBomDetailPage from './pages/management/catalog/ManagementBomDetailPage.vue'
import ManagementProductDetailPage from './pages/management/catalog/ManagementProductDetailPage.vue'
import ManagementVariantBuilderPage from './pages/management/catalog/ManagementVariantBuilderPage.vue'
import ManagementBuilderTemplatesPage from './pages/management/builder/ManagementBuilderTemplatesPage.vue'
import ManagementBuilderTemplatePage from './pages/management/builder/ManagementBuilderTemplatePage.vue'
import ManagementCustomersPage from './pages/management/customers/ManagementCustomersPage.vue'
import ManagementCustomerDetailPage from './pages/management/customers/ManagementCustomerDetailPage.vue'
import ManagementKitchenPage from './pages/management/operations/ManagementKitchenPage.vue'
import ManagementTablesPage from './pages/management/operations/ManagementTablesPage.vue'
import ManagementReportsIndexPage from './pages/management/finance/ManagementReportsIndexPage.vue'
import ManagementReportPage from './pages/management/finance/ManagementReportPage.vue'
import ManagementRegisterPage from './pages/management/sales/ManagementRegisterPage.vue'
import ManagementInventoryPage from './pages/management/inventory/ManagementInventoryPage.vue'
import ManagementInventoryDashboardPage from './pages/management/inventory/ManagementInventoryDashboardPage.vue'
import ManagementInventoryMaterialsPage from './pages/management/inventory/ManagementInventoryMaterialsPage.vue'
import ManagementInventoryMaterialDetailPage from './pages/management/inventory/ManagementInventoryMaterialDetailPage.vue'
import ManagementMaterialRequestsPage from './pages/management/purchasing/ManagementMaterialRequestsPage.vue'
import ManagementMaterialRequestDetailPage from './pages/management/purchasing/ManagementMaterialRequestDetailPage.vue'
import ManagementInventoryPurchasesPage from './pages/management/purchasing/ManagementInventoryPurchasesPage.vue'
import ManagementInventoryPurchaseDetailPage from './pages/management/purchasing/ManagementInventoryPurchaseDetailPage.vue'
import ManagementInventoryWarehousesPage from './pages/management/inventory/ManagementInventoryWarehousesPage.vue'
import ManagementInventoryMovementsPage from './pages/management/inventory/ManagementInventoryMovementsPage.vue'
import ManagementProductStockLedgerPage from './pages/management/inventory/ManagementProductStockLedgerPage.vue'
import ManagementInventoryReorderPage from './pages/management/inventory/ManagementInventoryReorderPage.vue'
import ManagementInventoryProductionPage from './pages/management/inventory/ManagementInventoryProductionPage.vue'
import ManagementInventoryLossesPage from './pages/management/inventory/ManagementInventoryLossesPage.vue'
import ManagementInventoryDocumentsPage from './pages/management/inventory/ManagementInventoryDocumentsPage.vue'
import ManagementInventoryDocumentDetailPage from './pages/management/inventory/ManagementInventoryDocumentDetailPage.vue'
import ManagementInventoryCountPage from './pages/management/inventory/ManagementInventoryCountPage.vue'
import ManagementInventoryCountDetailPage from './pages/management/inventory/ManagementInventoryCountDetailPage.vue'
import ManagementInventoryCostsPage from './pages/management/inventory/ManagementInventoryCostsPage.vue'
import ManagementClubPage from './pages/management/customers/ManagementClubPage.vue'
import ManagementSurveysPage from './pages/management/customers/ManagementSurveysPage.vue'
import ManagementCostControlPage from './pages/management/finance/ManagementCostControlPage.vue'
import ManagementReservationsPage from './pages/management/customers/ManagementReservationsPage.vue'
import ManagementBranchesPage from './pages/management/operations/ManagementBranchesPage.vue'
import ManagementCallCenterPage from './pages/management/customers/ManagementCallCenterPage.vue'
import ManagementAccountingPage from './pages/management/finance/ManagementAccountingPage.vue'
import ManagementHelpPage from './pages/management/settings/ManagementHelpPage.vue'
import ManagementPrintFormatsPage from './pages/management/settings/ManagementPrintFormatsPage.vue'
import ManagementZarinpalSettingsPage from './pages/management/settings/ManagementZarinpalSettingsPage.vue'
import ManagementSnappfoodPage from './pages/management/settings/ManagementSnappfoodPage.vue'
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
    if (pathname.startsWith('/management/sales')) return 'management-sales-dashboard'
    if (pathname.startsWith('/management/couriers')) return 'management-couriers'
    if (pathname === '/management/user' || pathname.startsWith('/management/user/')) return 'management-user-detail'
    if (pathname.startsWith('/management/users') || pathname.startsWith('/management/user-access')) return 'management-users'
    if (pathname.startsWith('/management/pos-defaults') || pathname.startsWith('/management/pos_defaults')) return 'management-pos-defaults'
    if (pathname.startsWith('/management/pos-profile') || pathname.startsWith('/management/pos_profile')) return 'management-pos-profile'
    if (pathname.startsWith('/management/pos')) return 'management-pos'
    if (pathname === '/management/order' || pathname.startsWith('/management/order/')) return 'management-order-detail'
    if (pathname.startsWith('/management/orders')) return 'management-orders'
    if (pathname.startsWith('/management/design-system') || pathname.startsWith('/management/design_system')) return 'management-design-system'
    if (pathname.startsWith('/management/products/detail') && variantStudioMode) return 'management-variant-builder'
    if (pathname.startsWith('/management/product') && variantStudioMode) return 'management-variant-builder'
    if (pathname.startsWith('/management/modifier-groups') || pathname.startsWith('/management/modifier_groups')) return 'management-modifier-groups'
    if (pathname.startsWith('/management/products')) return 'management-products'
    if (pathname.startsWith('/management/product')) return 'management-product'
    if (pathname.startsWith('/management/menu-design') || pathname.startsWith('/management/menu_design')) return 'management-menu-design'
    if (pathname.startsWith('/management/menu-groups') || pathname.startsWith('/management/menu_groups')) return 'management-menu-groups'
    if (pathname.startsWith('/management/menu-group') || pathname.startsWith('/management/menu_group')) return 'management-menu-group'
    if (pathname.startsWith('/management/boms')) return 'management-boms'
    if (pathname.startsWith('/management/bom')) return 'management-bom'
    if (pathname === '/management/customer' || pathname.startsWith('/management/customer/')) return 'management-customer-detail'
    if (pathname.startsWith('/management/customers')) return 'management-customers'
    if (pathname.startsWith('/management/tables')) return 'management-tables'
    if (pathname.startsWith('/management/reports/')) return 'management-report'
    if (pathname.startsWith('/management/reports')) return 'management-reports'
    if (pathname.startsWith('/management/register')) return 'management-register'
    if (pathname.startsWith('/management/inventory/materials/detail')) return 'management-inventory-material-detail'
    if (pathname.startsWith('/management/inventory/materials')) return 'management-inventory-materials'
    if (pathname.startsWith('/management/inventory/requests/detail')) return 'management-material-request-detail'
    if (pathname.startsWith('/management/inventory/requests')) return 'management-material-requests'
    if (pathname.startsWith('/management/inventory/purchases/detail')) return 'management-inventory-purchase-detail'
    if (pathname.startsWith('/management/inventory/purchases')) return 'management-inventory-purchases'
    if (pathname.startsWith('/management/inventory/warehouses')) return 'management-inventory-warehouses'
    if (pathname.startsWith('/management/inventory/movements')) return 'management-inventory-movements'
    if (pathname.startsWith('/management/inventory/ledger')) return 'management-inventory-ledger'
    if (pathname.startsWith('/management/inventory/reorder')) return 'management-inventory-reorder'
    if (pathname.startsWith('/management/inventory/production')) return 'management-inventory-production'
    if (pathname.startsWith('/management/inventory/losses')) return 'management-inventory-losses'
    if (pathname.startsWith('/management/inventory/documents/detail')) return 'management-inventory-document-detail'
    if (pathname.startsWith('/management/inventory/documents')) return 'management-inventory-documents'
    if (pathname.startsWith('/management/inventory/count/detail')) return 'management-inventory-count-detail'
    if (pathname.startsWith('/management/inventory/count')) return 'management-inventory-count'
    if (pathname.startsWith('/management/inventory/costs')) return 'management-inventory-costs'
    if (pathname === '/management/inventory' || pathname === '/management/inventory/') return 'management-inventory-dashboard'
    if (pathname.startsWith('/management/inventory')) return 'management-inventory'
    if (pathname.startsWith('/management/club')) return 'management-club'
  if (pathname.startsWith('/management/surveys')) return 'management-surveys'
  if (pathname.startsWith('/management/cost-control')) return 'management-cost-control'
  if (pathname.startsWith('/management/reservations')) return 'management-reservations'
  if (pathname.startsWith('/management/branches')) return 'management-branches'
  if (pathname.startsWith('/management/call-center') || pathname.startsWith('/management/call_center')) return 'management-call-center'
  if (pathname.startsWith('/management/accounting')) return 'management-accounting'
  if (pathname.startsWith('/management/help')) return 'management-help'
    if (pathname.startsWith('/management/print-formats') || pathname.startsWith('/management/print_formats')) return 'management-print-formats'
    if (pathname.startsWith('/management/home-builder') || pathname.startsWith('/management/home_builder')) return 'management-home-builder'
    if (pathname.startsWith('/management/site-settings') || pathname.startsWith('/management/site_settings')) return 'management-site-settings'
    if (pathname.startsWith('/management/variant-builder') || pathname.startsWith('/management/variant_builder')) return 'management-variant-builder'
    if (pathname.startsWith('/management/builder-template')) return 'management-builder-templates'
    if (pathname.startsWith('/management/zarinpal-settings') || pathname.startsWith('/management/zarinpal_settings')) return 'management-zarinpal-settings'
    if (pathname.startsWith('/management/snappfood') || pathname.startsWith('/management/snapp-food')) return 'management-snappfood'
    if (pathname.startsWith('/management/settings')) return 'management-settings'

    if (pathname === '/' || pathname === '') return 'landing'
    if (pathname.startsWith('/product-groups') || pathname.startsWith('/product_groups') || pathname.startsWith('/groups')) return 'product-groups'
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
    if (pathname.startsWith('/management/kitchen')) return 'management-kitchen'
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
