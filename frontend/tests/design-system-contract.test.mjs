import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'

const sourceRoot = new URL('../src/', import.meta.url)
const tokensSource = fs.readFileSync(new URL('design-system/tokens.js', sourceRoot), 'utf8')
const catalogSource = fs.readFileSync(new URL('design-system/catalog.js', sourceRoot), 'utf8')
const appSource = fs.readFileSync(new URL('App.vue', sourceRoot), 'utf8')
const themeSource = fs.readFileSync(new URL('theme.css', sourceRoot), 'utf8')
const layoutSource = fs.readFileSync(new URL('components/management/ManagementLayout.vue', sourceRoot), 'utf8')
const hooksSource = fs.readFileSync(new URL('../../restaurant/hooks.py', import.meta.url), 'utf8')
const variantBuilderSource = fs.readFileSync(new URL('../src/pages/management/ManagementVariantBuilderPage.vue', import.meta.url), 'utf8')
const ordersSource = fs.readFileSync(new URL('../src/pages/management/ManagementOrdersPage.vue', import.meta.url), 'utf8')
const couriersSource = fs.readFileSync(new URL('../src/pages/management/ManagementCouriersPage.vue', import.meta.url), 'utf8')
const clubSource = fs.readFileSync(new URL('../src/pages/management/ManagementClubPage.vue', import.meta.url), 'utf8')
const callCenterSource = fs.readFileSync(new URL('../src/pages/management/ManagementCallCenterPage.vue', import.meta.url), 'utf8')
const reportSource = fs.readFileSync(new URL('../src/pages/management/ManagementReportPage.vue', import.meta.url), 'utf8')
const reservationsSource = fs.readFileSync(new URL('../src/pages/management/ManagementReservationsPage.vue', import.meta.url), 'utf8')
const surveysSource = fs.readFileSync(new URL('../src/pages/management/ManagementSurveysPage.vue', import.meta.url), 'utf8')

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
  assert.ok(designSystemCatalog.patterns.some((item) => item.id === 'product-search'))
  assert.ok(designSystemCatalog.patterns.some((item) => item.id === 'management-list-detail'))
  assert.ok(designSystemCatalog.patterns.some((item) => item.id === 'order-fulfillment'))
  assert.ok(designSystemCatalog.patterns.some((item) => item.id === 'courier-workbench'))
  assert.ok(designSystemCatalog.patterns.some((item) => item.id === 'reservation-workbench'))
  assert.ok(designSystemCatalog.patterns.some((item) => item.id === 'survey-feedback'))
  assert.ok(designSystemCatalog.patterns.some((item) => item.id === 'crm-engagement'))
  assert.ok(designSystemCatalog.templates.some((item) => item.id === 'products-list'))
  assert.ok(designSystemCatalog.templates.some((item) => item.id === 'management-orders'))
  assert.ok(designSystemCatalog.templates.some((item) => item.id === 'management-couriers'))
  assert.ok(designSystemCatalog.templates.some((item) => item.id === 'management-reservations'))
  assert.ok(designSystemCatalog.templates.some((item) => item.id === 'management-surveys'))
  assert.ok(designSystemCatalog.templates.some((item) => item.id === 'management-club'))
})

test('design system route is registered in the management shell', () => {
  assert.match(appSource, /ManagementDesignSystemPage/)
  assert.match(appSource, /page === 'management-design-system'/)
  assert.match(appSource, /pathname\.startsWith\('\/management\/design-system'\)/)
  assert.match(layoutSource, /management-design-system/)
  assert.match(hooksSource, /from_route":\s*"\/management\/design-system"/)
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

test('design system page declares all catalog tabs and reference language', () => {
  const pageSource = fs.readFileSync(new URL('../src/pages/management/ManagementDesignSystemPage.vue', import.meta.url), 'utf8')
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
