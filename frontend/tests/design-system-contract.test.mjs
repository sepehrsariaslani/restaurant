import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'

const sourceRoot = new URL('../src/', import.meta.url)
const tokensSource = fs.readFileSync(new URL('design-system/tokens.js', sourceRoot), 'utf8')
const catalogSource = fs.readFileSync(new URL('design-system/catalog.js', sourceRoot), 'utf8')
const appSource = fs.readFileSync(new URL('App.vue', sourceRoot), 'utf8')
const themeSource = fs.readFileSync(new URL('theme.css', sourceRoot), 'utf8')
const themeSettingsSource = fs.readFileSync(new URL('utils/themeSettings.js', sourceRoot), 'utf8')
const layoutSource = fs.readFileSync(new URL('components/management/ManagementLayout.vue', sourceRoot), 'utf8')
const hooksSource = fs.readFileSync(new URL('../../restaurant/hooks.py', import.meta.url), 'utf8')
const designSystemHtmlSource = fs.readFileSync(new URL('../../restaurant/www/management/design_system.html', import.meta.url), 'utf8')
const designSystemPySource = fs.readFileSync(new URL('../../restaurant/www/management/design_system.py', import.meta.url), 'utf8')
const designSystemHyphenHtmlSource = fs.readFileSync(new URL('../../restaurant/www/management/design-system.html', import.meta.url), 'utf8')
const designSystemHyphenPySource = fs.readFileSync(new URL('../../restaurant/www/management/design-system.py', import.meta.url), 'utf8')
const usersHtmlSource = fs.readFileSync(new URL('../../restaurant/www/management/users.html', import.meta.url), 'utf8')
const usersPySource = fs.readFileSync(new URL('../../restaurant/www/management/users.py', import.meta.url), 'utf8')
const userAccessHtmlSource = fs.readFileSync(new URL('../../restaurant/www/management/user_access.html', import.meta.url), 'utf8')
const userAccessPySource = fs.readFileSync(new URL('../../restaurant/www/management/user_access.py', import.meta.url), 'utf8')
const menuDesignHtmlSource = fs.readFileSync(new URL('../../restaurant/www/management/menu_design.html', import.meta.url), 'utf8')
const menuDesignPySource = fs.readFileSync(new URL('../../restaurant/www/management/menu_design.py', import.meta.url), 'utf8')
const variantBuilderHtmlSource = fs.readFileSync(new URL('../../restaurant/www/management/variant_builder.html', import.meta.url), 'utf8')
const variantBuilderPySource = fs.readFileSync(new URL('../../restaurant/www/management/variant_builder.py', import.meta.url), 'utf8')
const variantBuilderSource = fs.readFileSync(new URL('../src/pages/management/catalog/ManagementVariantBuilderPage.vue', import.meta.url), 'utf8')
const ordersSource = fs.readFileSync(new URL('../src/pages/management/sales/ManagementOrdersPage.vue', import.meta.url), 'utf8')
const couriersSource = fs.readFileSync(new URL('../src/pages/management/operations/ManagementCouriersPage.vue', import.meta.url), 'utf8')
const clubSource = fs.readFileSync(new URL('../src/pages/management/customers/ManagementClubPage.vue', import.meta.url), 'utf8')
const callCenterSource = fs.readFileSync(new URL('../src/pages/management/customers/ManagementCallCenterPage.vue', import.meta.url), 'utf8')
const reportSource = fs.readFileSync(new URL('../src/pages/management/finance/ManagementReportPage.vue', import.meta.url), 'utf8')
const reservationsSource = fs.readFileSync(new URL('../src/pages/management/customers/ManagementReservationsPage.vue', import.meta.url), 'utf8')
const surveysSource = fs.readFileSync(new URL('../src/pages/management/customers/ManagementSurveysPage.vue', import.meta.url), 'utf8')
const branchesSource = fs.readFileSync(new URL('../src/pages/management/operations/ManagementBranchesPage.vue', import.meta.url), 'utf8')
const costControlSource = fs.readFileSync(new URL('../src/pages/management/finance/ManagementCostControlPage.vue', import.meta.url), 'utf8')
const accountingSource = fs.readFileSync(new URL('../src/pages/management/finance/ManagementAccountingPage.vue', import.meta.url), 'utf8')
const inventorySource = fs.readFileSync(new URL('../src/pages/management/inventory/ManagementInventoryPage.vue', import.meta.url), 'utf8')
const inventoryCountDetailSource = fs.readFileSync(new URL('../src/pages/management/inventory/ManagementInventoryCountDetailPage.vue', import.meta.url), 'utf8')
const zarinpalSource = fs.readFileSync(new URL('../src/pages/management/settings/ManagementZarinpalSettingsPage.vue', import.meta.url), 'utf8')
const productsSource = fs.readFileSync(new URL('../src/pages/management/catalog/ManagementProductsPage.vue', import.meta.url), 'utf8')
const galleryViewSource = fs.readFileSync(new URL('../src/components/management/ManagementGalleryView.vue', import.meta.url), 'utf8')
const kanbanViewSource = fs.readFileSync(new URL('../src/components/management/ManagementKanbanView.vue', import.meta.url), 'utf8')
const notionControlsSource = fs.readFileSync(new URL('../src/components/management/notion/NotionViewControls.vue', import.meta.url), 'utf8')
const notionSettingsSource = fs.readFileSync(new URL('../src/components/management/notion/NotionViewSettings.vue', import.meta.url), 'utf8')
const searchableDropdownSource = fs.readFileSync(new URL('../src/components/SearchableDropdown.vue', import.meta.url), 'utf8')
const restaurantApiSource = fs.readFileSync(new URL('../../restaurant/api.py', import.meta.url), 'utf8')
const restaurantFeaturePackSource = fs.readFileSync(new URL('../../restaurant/api_feature_pack.py', import.meta.url), 'utf8')
const apiSource = fs.readFileSync(new URL('../src/utils/api.js', import.meta.url), 'utf8')

test('design system tokens expose stable semantic layers for RTL restaurant UI', async () => {
  const { designTokens } = await import('../src/design-system/tokens.js')

  assert.equal(designTokens.direction, 'rtl')
  assert.equal(designTokens.font.family, 'Peyda')
  assert.ok(designTokens.color.primitive.primary)
  assert.ok(designTokens.color.semantic.surface.page)
  assert.ok(designTokens.color.semantic.text.primary)
  assert.ok(designTokens.spacing['4'])
  assert.ok(designTokens.radius.md)
  assert.ok(designTokens.shadow.sm)
  assert.ok(designTokens.motion.fast)
  assert.ok(designTokens.zIndex.overlay)
})

test('design system catalog contains the requested reference tabs and product surfaces', async () => {
  const { designSystemTabs, designSystemCatalog } = await import('../src/design-system/catalog.js')
  const tabIds = designSystemTabs.map((tab) => tab.id)

  assert.deepEqual(tabIds, ['theme', 'icons', 'components', 'patterns', 'templates'])
  assert.ok(designSystemCatalog.components.some((item) => item.id === 'product-card'))
  assert.ok(designSystemCatalog.components.some((item) => item.id === 'product-detail'))
  assert.ok(designSystemCatalog.components.some((item) => item.id === 'management-product-native-panel'))
  assert.ok(designSystemCatalog.components.some((item) => item.id === 'management-product-connections-panel'))
  assert.ok(designSystemCatalog.components.some((item) => item.id === 'management-product-inventory-panel'))
  assert.ok(designSystemCatalog.patterns.some((item) => item.id === 'product-search'))
  assert.ok(designSystemCatalog.patterns.some((item) => item.id === 'management-list-detail'))
  assert.ok(designSystemCatalog.patterns.some((item) => item.id === 'product-detail-native-settings'))
  assert.ok(designSystemCatalog.patterns.some((item) => item.id === 'product-detail-connections'))
  assert.ok(designSystemCatalog.patterns.some((item) => item.id === 'product-detail-inventory-ledger'))
  assert.ok(designSystemCatalog.patterns.some((item) => item.id === 'order-fulfillment'))
  assert.ok(designSystemCatalog.patterns.some((item) => item.id === 'courier-workbench'))
  assert.ok(designSystemCatalog.patterns.some((item) => item.id === 'reservation-workbench'))
  assert.ok(designSystemCatalog.patterns.some((item) => item.id === 'survey-feedback'))
  assert.ok(designSystemCatalog.patterns.some((item) => item.id === 'crm-engagement'))
  assert.ok(designSystemCatalog.patterns.some((item) => item.id === 'branch-workbench'))
  assert.ok(designSystemCatalog.patterns.some((item) => item.id === 'cost-control'))
  assert.ok(designSystemCatalog.patterns.some((item) => item.id === 'accounting-workbench'))
  assert.ok(designSystemCatalog.templates.some((item) => item.id === 'products-list'))
  assert.ok(designSystemCatalog.templates.some((item) => item.id === 'management-orders'))
  assert.ok(designSystemCatalog.templates.some((item) => item.id === 'management-couriers'))
  assert.ok(designSystemCatalog.templates.some((item) => item.id === 'management-reservations'))
  assert.ok(designSystemCatalog.templates.some((item) => item.id === 'management-surveys'))
  assert.ok(designSystemCatalog.templates.some((item) => item.id === 'management-club'))
  assert.ok(designSystemCatalog.templates.some((item) => item.id === 'management-branches'))
  assert.ok(designSystemCatalog.templates.some((item) => item.id === 'management-cost-control'))
  assert.ok(designSystemCatalog.templates.some((item) => item.id === 'management-accounting'))
})

test('design system route is registered in the management shell', () => {
  assert.match(appSource, /ManagementDesignSystemPage/)
  assert.match(appSource, /page === 'management-design-system'/)
  assert.match(appSource, /pathname\.startsWith\('\/management\/design-system'\)/)
  assert.match(layoutSource, /management-design-system/)
  assert.match(hooksSource, /from_route":\s*"\/management\/design-system"/)
  assert.match(designSystemHtmlSource, /window\._PAGE\s*=\s*'management-design-system'/)
  assert.match(designSystemHtmlSource, /assets\/restaurant\/frontend\/assets\/index\.js/)
  assert.match(designSystemPySource, /build_context\(context, "management-design-system"\)/)
  assert.match(designSystemHyphenHtmlSource, /window\._PAGE\s*=\s*'management-design-system'/)
  assert.match(designSystemHyphenHtmlSource, /assets\/restaurant\/frontend\/assets\/index\.js/)
  assert.match(designSystemHyphenPySource, /from \.design_system import get_context/)
  assert.match(usersHtmlSource, /window\._PAGE\s*=\s*'management-users'/)
  assert.match(usersPySource, /build_context\(context, "management-users"\)/)
  assert.match(userAccessHtmlSource, /window\._PAGE\s*=\s*'management-users'/)
  assert.match(userAccessPySource, /build_context\(context, "management-users"\)/)
  assert.match(menuDesignHtmlSource, /window\._PAGE\s*=\s*'management-menu-design'/)
  assert.match(menuDesignPySource, /build_context\(context, "management-menu-design"\)/)
  assert.match(variantBuilderHtmlSource, /window\._PAGE\s*=\s*'management-variant-builder'/)
  assert.match(variantBuilderPySource, /build_context\(context, "management-variant-builder"\)/)
})

test('product views keep shared controls left-aligned and resolve fallback media', () => {
  assert.match(productsSource, /\.notion-view-tools\s*\{[\s\S]*?justify-content:\s*flex-end/)
  assert.match(galleryViewSource, /row\?\.item_image/)
  assert.match(kanbanViewSource, /row\?\.item_image/)
  assert.match(kanbanViewSource, /subGroupBy/)
  assert.match(kanbanViewSource, /data-kanban-field/)
  assert.match(productsSource, /handleKanbanMove/)
  assert.match(productsSource, /kanbanSubGroupBy/)
  assert.match(notionControlsSource, /fixed-panel/)
  assert.match(notionControlsSource, /@click\.stop/)
  assert.match(notionSettingsSource, /position: "fixed"/)
  assert.match(searchableDropdownSource, /rect\.right - panelWidth/)
  assert.match(restaurantApiSource, /_core_item_image_select_fields\(\)/)
  assert.match(restaurantApiSource, /attached_to_doctype.*Item/)
  assert.match(restaurantFeaturePackSource, /has_customization.*restaurant_is_customizable/)
  assert.match(apiSource, /restaurant\.api_management_products_safe\.list_management_products_safe/)
  assert.match(apiSource, /callMethodByPath\(MANAGEMENT_PRODUCTS_SAFE_METHOD, args\)/)
})

test('management navbar keeps operational modules separated and directly routable', () => {
  for (const group of ['sales', 'menu', 'purchasing', 'inventory', 'operations', 'customers', 'reports', 'settings']) {
    assert.match(layoutSource, new RegExp(`group: "${group}"`))
    assert.match(layoutSource, new RegExp(`key: "${group}"`))
  }
  assert.doesNotMatch(layoutSource, /group: "crm"/)
  assert.match(layoutSource, /title: "خرید"/)
  assert.match(layoutSource, /title: "انبار و تولید"/)
  assert.match(layoutSource, /title: "عملیات رستوران"/)
  assert.match(layoutSource, /title: "مشتریان و ارتباط"/)
  for (const route of [
    '/management/couriers',
    '/management/users',
    '/management/tables',
    '/management/modifier-groups',
    '/management/zarinpal-settings',
    '/management/variant-builder',
    '/management/user-access',
    '/management/call_center',
    '/management/print_formats',
    '/management/site_settings',
  ]) {
    assert.match(hooksSource, new RegExp(`from_route":\\s*"${route.replaceAll('/', '\\\/')}"`))
  }
})

test('semantic design tokens are published as CSS variables while legacy aliases remain available', () => {
  for (const token of [
    '--ds-color-bg-page',
    '--ds-color-surface',
    '--ds-color-text-primary',
    '--ds-color-action-primary',
    '--ds-space-4',
    '--ds-radius-md',
    '--ds-shadow-sm',
    '--ds-motion-fast',
  ]) {
    assert.match(themeSource, new RegExp(`${token.replaceAll('-', '\\-')}\\s*:`), `${token} must be declared`)
  }
  assert.match(themeSource, /--accent-green:\s*var\(--ds-color-action-primary\)/)
  assert.match(themeSource, /--text-primary:\s*var\(--ds-color-text-primary\)/)
})

test('management semantic aliases are driven by the shared theme source', () => {
  for (const token of [
    '--mg-bg-page',
    '--mg-bg-surface',
    '--mg-bg-soft',
    '--mg-text-main',
    '--mg-text-muted',
    '--mg-border',
    '--mg-primary',
    '--mg-primary-hover',
    '--mg-success',
    '--mg-danger',
  ]) {
    assert.match(themeSource, new RegExp(`${token.replaceAll('-', '\\-')}\\s*:`), `${token} must be declared in theme.css`)
  }
  assert.match(themeSettingsSource, /setCssVar\('--mg-primary', normalized\.primary\)/)
  assert.match(themeSettingsSource, /setCssVar\('--mg-bg-page', normalized\.background\)/)
  assert.match(themeSettingsSource, /setCssVar\('--mg-bg-surface', normalized\.surface\)/)
  assert.match(themeSettingsSource, /setCssVar\('--mg-text-main', normalized\.text\)/)
  assert.match(themeSettingsSource, /setCssVar\('--mg-border', borderColor\)/)
  assert.doesNotMatch(appSource, /Global Management Theme Tokens/)
})

test('design system page declares all catalog tabs and reference language', () => {
  const pageSource = fs.readFileSync(new URL('../src/pages/management/design-system/ManagementDesignSystemPage.vue', import.meta.url), 'utf8')
  for (const label of ['تم و توکن‌ها', 'آیکون‌ها', 'کامپوننت‌ها', 'پترن‌ها', 'تمپلیت‌ها']) {
    assert.match(catalogSource, new RegExp(label))
  }
  assert.match(pageSource, /designSystemTabs/)
  assert.match(pageSource, /MenuProductCard/)
  assert.match(pageSource, /ManagementProductSummaryCard/)
  assert.match(pageSource, /prefers-reduced-motion/)
})

test('design primitives expose semantic variants and accessible async state', () => {
  const buttonSource = fs.readFileSync(new URL('../src/components/design/DsButton.vue', import.meta.url), 'utf8')
  const badgeSource = fs.readFileSync(new URL('../src/components/design/DsBadge.vue', import.meta.url), 'utf8')
  assert.match(buttonSource, /variant.*primary|primary.*variant/)
  assert.match(buttonSource, /aria-busy/)
  assert.match(buttonSource, /ds-button/)
  assert.match(badgeSource, /status|tone/)
  assert.match(badgeSource, /ds-badge/)
})

test('ERPNext item attribute catalog uses the shared management list pattern', () => {
  assert.match(variantBuilderSource, /ManagementListView/)
  assert.match(variantBuilderSource, /:rows="itemAttributeCatalog"/)
  assert.match(variantBuilderSource, /@row-click="openItemAttributeEditor/)
  assert.match(variantBuilderSource, /itemAttributeColumns/)
})

test('management orders keep a shared list-to-detail workflow', () => {
  assert.match(ordersSource, /ManagementListView/)
  assert.match(ordersSource, /:rows="displayOrders"/)
  assert.match(ordersSource, /@row-click="openOrderDetail"/)
  assert.match(ordersSource, /getManagementOrderDetail/)
  assert.match(ordersSource, /selectedOrder/)
})

test('management collections and detail routes stay reusable across operational domains', () => {
  const collectionSource = fs.readFileSync(new URL('../src/components/management/ManagementCollectionView.vue', import.meta.url), 'utf8')
  const usersSource = fs.readFileSync(new URL('../src/pages/management/settings/ManagementUsersPage.vue', import.meta.url), 'utf8')
  const customersSource = fs.readFileSync(new URL('../src/pages/management/customers/ManagementCustomersPage.vue', import.meta.url), 'utf8')
  const inventorySource = fs.readFileSync(new URL('../src/pages/management/inventory/ManagementInventoryCountDetailPage.vue', import.meta.url), 'utf8')
  const documentsSource = fs.readFileSync(new URL('../src/pages/management/inventory/ManagementInventoryDocumentsPage.vue', import.meta.url), 'utf8')
  const dateInputSource = fs.readFileSync(new URL('../src/components/PersianRangeDateInput.vue', import.meta.url), 'utf8')

  for (const mode of ['list', 'gallery', 'table', 'kanban', 'sheet', 'calendar', 'tree']) {
    assert.match(collectionSource, new RegExp(`name="${mode}"`))
  }
  assert.match(usersSource, /ManagementCollectionView/)
  assert.match(usersSource, /ManagementNotionListView/)
  assert.match(usersSource, /openUserDetail/)
  assert.match(customersSource, /ManagementCollectionView/)
  assert.ok(customersSource.includes('/management/customer?'))
  assert.match(inventorySource, /ManagementSmartDataTable/)
  assert.match(documentsSource, /Purchase Invoice/)
  assert.match(documentsSource, /Purchase Receipt/)
  assert.match(documentsSource, /Stock Entry/)
  assert.ok(dateInputSource.includes('iso: jalaliToIso'))
  assert.match(appSource, /management-order-detail/)
  assert.match(appSource, /management-user-detail/)
  assert.match(appSource, /management-customer-detail/)
  assert.match(appSource, /management-inventory-document-detail/)
  assert.match(hooksSource, /from_route":\s*"\/management\/order"/)
  assert.match(hooksSource, /from_route":\s*"\/management\/user"/)
  assert.match(hooksSource, /from_route":\s*"\/management\/customer"/)
  assert.match(hooksSource, /from_route":\s*"\/management\/inventory\/documents"/)
})

test('courier management uses the shared list and product-like detail workflow', () => {
  assert.match(couriersSource, /ManagementListView/)
  assert.match(couriersSource, /:rows="couriers"/)
  assert.match(couriersSource, /@row-click="editCourier"/)
  assert.match(couriersSource, /courier-workbench/)
  assert.match(couriersSource, /جزئیات پیک/)
})

test('club customer management uses the shared list pattern', () => {
  assert.match(clubSource, /ManagementListView/)
  assert.match(clubSource, /:rows="customers"/)
  assert.match(clubSource, /clubCustomerColumns/)
  assert.match(clubSource, /cell-customer_name/)
  assert.match(clubSource, /ویرایش/)
})

test('customer voice management uses the shared list pattern and preserves response actions', () => {
  assert.match(clubSource, /:rows="voices"/)
  assert.match(clubSource, /voiceColumns/)
  assert.match(clubSource, /@row-click="openVoiceReply"/)
  assert.match(clubSource, /openVoiceReply\(row\)/)
  assert.match(clubSource, /removeVoice\(row\)/)
})

test('club organization management keeps contracts, members and orders in shared lists', () => {
  assert.match(clubSource, /orgContractColumns/)
  assert.match(clubSource, /orgMemberColumns/)
  assert.match(clubSource, /orgCreditMemberColumns/)
  assert.match(clubSource, /orgOrderColumns/)
  assert.match(clubSource, /:rows="orgContracts"/)
  assert.match(clubSource, /:rows="orgMembers"/)
  assert.match(clubSource, /:rows="orgOrders"/)
  assert.match(clubSource, /selectedOrgOrders\[row\.name\]/)
})

test('club wallet, referral and campaign surfaces use shared list patterns', () => {
  for (const token of [
    'smsKindStatsColumns',
    'walletColumns',
    'pointEntryColumns',
    'walletTransactionColumns',
    'referralTopColumns',
    'campaignColumns',
    'couponColumns',
  ]) {
    assert.match(clubSource, new RegExp(token))
  }
  assert.match(clubSource, /:rows="smsKindStatsRows"/)
  assert.match(clubSource, /:rows="wallets"/)
  assert.match(clubSource, /:rows="walletDetail\.point_entries"/)
  assert.match(clubSource, /:rows="walletDetail\.transactions"/)
  assert.match(clubSource, /:rows="referral\.top"/)
  assert.match(clubSource, /:rows="campaigns"/)
  assert.match(clubSource, /:rows="coupons"/)
})

test('sms history uses the shared responsive list pattern', () => {
  assert.match(clubSource, /:rows="smsHistory\.messages \|\| \[\]"/)
  assert.match(clubSource, /smsHistoryColumns/)
  assert.match(clubSource, /row\.provider_note/)
  assert.match(clubSource, /cell-status/)
})

test('call center uses the shared list pattern for recent calls', () => {
  assert.match(callCenterSource, /ManagementListView/)
  assert.match(callCenterSource, /:rows="calls"/)
  assert.match(callCenterSource, /callColumns/)
  assert.match(callCenterSource, /cell-caller_mobile/)
  assert.match(callCenterSource, /پاسخ/)
})

test('management reports keep operational titles and waiter performance connected', () => {
  assert.match(reportSource, /getManagementReportWaiterPerformance/)
  assert.match(reportSource, /'waiter-performance'/)
  assert.match(reportSource, /'menu-engineering'/)
  assert.match(reportSource, /'tax-reconciliation'/)
  assert.match(reportSource, /getManagementReportBranchPerformance/)
  assert.match(reportSource, /getManagementReportVendorSales/)
  assert.match(reportSource, /getManagementReportReceiptPaymentBalance/)
  assert.match(reportSource, /'receipt-payment-balance': getManagementReportReceiptPaymentBalance/)
  assert.match(reportSource, /reportSubtitle/)
  assert.doesNotMatch(reportSource, /:subtitle="reportKey"/)
})

test('reservations use the shared responsive list pattern without losing actions', () => {
  assert.match(reservationsSource, /ManagementListView/)
  assert.match(reservationsSource, /:rows="rows"/)
  assert.match(reservationsSource, /reservationColumns/)
  assert.match(reservationsSource, /@row-click="openForm"/)
  assert.match(reservationsSource, /setStatus\(row, 'تأییدشده'\)/)
  assert.match(reservationsSource, /removeReservation\(row\)/)
})

test('survey questions and responses use shared list patterns', () => {
  assert.match(surveysSource, /ManagementListView/)
  assert.match(surveysSource, /questionColumns/)
  assert.match(surveysSource, /responseColumns/)
  assert.match(surveysSource, /:rows="questions"/)
  assert.match(surveysSource, /:rows="filteredResponses"/)
  assert.match(surveysSource, /openQuestionForm\(row\)/)
  assert.match(surveysSource, /starString\(row\.overall_rating\)/)
})

test('branch management uses the shared responsive list pattern and keeps native actions', () => {
  assert.match(branchesSource, /ManagementListView/)
  assert.match(branchesSource, /:rows="branches"/)
  assert.match(branchesSource, /branchColumns/)
  assert.match(branchesSource, /openForm\(row\)/)
  assert.match(branchesSource, /toggleBranch\(row\)/)
})

test('cost control uses shared lists for profit-loss and budgets', () => {
  assert.match(costControlSource, /ManagementListView/)
  assert.match(costControlSource, /:rows="boot\.pl_rows \|\| \[\]"/)
  assert.match(costControlSource, /:rows="budgets"/)
  assert.match(costControlSource, /plColumns/)
  assert.match(costControlSource, /budgetColumns/)
  assert.match(costControlSource, /openBudgetForm\(row\)/)
})

test('accounting uses shared lists for balance, tax submissions and journal entries', () => {
  assert.match(accountingSource, /ManagementListView/)
  assert.match(accountingSource, /balanceRows/)
  assert.match(accountingSource, /balanceColumns/)
  assert.match(accountingSource, /tax\.submissions/)
  assert.match(accountingSource, /taxSubmissionColumns/)
  assert.match(accountingSource, /journalEntryColumns/)
  assert.match(accountingSource, /cell-status/)
})

test('inventory read-only operational surfaces use shared lists', () => {
  assert.match(inventorySource, /ManagementListView/)
  for (const token of [
    'materialColumns',
    'warehouseColumns',
    'movementColumns',
    'reorderColumns',
    'purchaseColumns',
    'productionMaterialColumns',
    'productionProductColumns',
    'wasteItemColumns',
    'orderLossColumns',
    'countResultColumns',
    'reconciliationColumns',
  ]) {
    assert.match(inventorySource, new RegExp(token))
  }
  for (const rows of [
    'materials',
    'warehouses',
    'movements',
    'reorderAlerts',
    'purchases',
    'plan.materials',
    'plan.products',
    'wasteReport.by_item',
    'orderLosses',
    'countResult.rows',
    'reconciliations',
  ]) {
    assert.match(inventorySource, new RegExp(`:rows="${rows.replaceAll('.', '\\.')}"`))
  }
  assert.match(inventorySource, /openReconciliationDetail/)
  assert.match(inventoryCountDetailSource, /ManagementSmartDataTable/)
})

test('zarinpal placeholder stays explicit and uses the shared management shell', () => {
  assert.match(zarinpalSource, /ManagementPageScaffold/)
  assert.match(zarinpalSource, /ManagementSurfaceCard/)
  assert.match(zarinpalSource, /قرارداد درگاه هنوز فعال نشده است/)
  assert.doesNotMatch(zarinpalSource, /getZarinpalSettings|saveZarinpalSettings|testZarinpalConnection/)
})

test('management pages and domain components stay organized by module', () => {
  const moduleDirectories = [
    'pages/management/catalog',
    'pages/management/sales',
    'pages/management/customers',
    'pages/management/inventory',
    'pages/management/purchasing',
    'pages/management/operations',
    'pages/management/finance',
    'pages/management/settings',
    'pages/management/builder',
    'pages/management/design-system',
    'pages/management/dashboard',
  ]
  for (const directory of moduleDirectories) {
    assert.equal(fs.existsSync(new URL(directory, sourceRoot)), true, `${directory} must exist`)
  }
  const rootVueFiles = fs.readdirSync(new URL('pages/management/', sourceRoot)).filter((file) => file.endsWith('.vue'))
  assert.deepEqual(rootVueFiles, [], 'route-level management pages must live in a module folder')
  assert.doesNotMatch(layoutSource, /management-inventory-overview/)

  const moduleFiles = [
    'pages/management/catalog/ManagementProductsPage.vue',
    'pages/management/catalog/ManagementProductDetailPage.vue',
    'pages/management/catalog/ManagementBomsPage.vue',
    'pages/management/sales/ManagementOrdersPage.vue',
    'pages/management/sales/ManagementPosPage.vue',
    'pages/management/customers/ManagementClubPage.vue',
    'pages/management/customers/ManagementCallCenterPage.vue',
    'pages/management/inventory/ManagementInventoryPage.vue',
    'pages/management/purchasing/ManagementInventoryPurchasesPage.vue',
    'pages/management/operations/ManagementKitchenPage.vue',
    'pages/management/finance/ManagementAccountingPage.vue',
    'pages/management/settings/ManagementSiteSettingsPage.vue',
    'pages/management/design-system/ManagementDesignSystemPage.vue',
    'components/management/catalog/ManagementBomManager.vue',
    'components/management/catalog/ManagementProductSummaryCard.vue',
    'components/management/design-system/ManagementThemeStudio.vue',
    'components/management/builder/ManagementPageBuilderWorkspace.vue',
  ]
  for (const file of moduleFiles) {
    assert.equal(fs.existsSync(new URL(file, sourceRoot)), true, `${file} must stay in its module folder`)
  }
  for (const file of [
    'pages/management/ManagementProductsPage.vue',
    'pages/management/ManagementInventoryPage.vue',
    'pages/management/ManagementInventoryPurchasesPage.vue',
    'pages/management/sales/ManagementCallCenterPage.vue',
    'components/management/ManagementBomManager.vue',
    'components/management/ManagementThemeStudio.vue',
  ]) {
    assert.equal(fs.existsSync(new URL(file, sourceRoot)), false, `${file} must not remain at the legacy root`)
  }
  assert.match(appSource, /pages\/management\/catalog\/ManagementProductsPage\.vue/)
  assert.match(appSource, /pages\/management\/inventory\/ManagementInventoryPage\.vue/)
  assert.match(appSource, /pages\/management\/purchasing\/ManagementInventoryPurchasesPage\.vue/)
  assert.doesNotMatch(appSource, /pages\/management\/ManagementProductsPage\.vue/)
  assert.doesNotMatch(appSource, /pages\/management\/ManagementInventoryPage\.vue/)
})
