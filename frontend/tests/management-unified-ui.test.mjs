import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'

const source = (path) => readFileSync(new URL(path, import.meta.url), 'utf8')
const scaffold = source('../src/components/management/ManagementPageScaffold.vue')
const surface = source('../src/components/management/ManagementSurfaceCard.vue')
const layout = source('../src/components/management/ManagementLayout.vue')
const app = source('../src/App.vue')
const toolbar = source('../src/components/management/ManagementCollectionToolbar.vue')
const settingsHub = source('../src/pages/management/settings/ManagementSettingsHubPage.vue')
const siteSettings = source('../src/pages/management/settings/ManagementSiteSettingsPage.vue')
const shiftSettings = source('../src/pages/management/settings/ManagementPosShiftSettingsPage.vue')
const dashboard = source('../src/pages/management/dashboard/ManagementDashboardPage.vue')
const products = source('../src/pages/management/catalog/ManagementProductsPage.vue')
const customers = source('../src/pages/management/customers/ManagementCustomersPage.vue')
const orders = source('../src/pages/management/sales/ManagementOrdersPage.vue')
const reservations = source('../src/pages/management/customers/ManagementReservationsPage.vue')
const branches = source('../src/pages/management/operations/ManagementBranchesPage.vue')
const couriers = source('../src/pages/management/operations/ManagementCouriersPage.vue')
const reports = source('../src/pages/management/finance/ManagementReportsIndexPage.vue')
const saveBar = source('../src/components/management/notion/NotionSaveBar.vue')
const viewSystem = source('../src/utils/viewSystem.js')

test('management pages share a responsive semantic scaffold inside the common workspace', () => {
  for (const slot of ['breadcrumbs', 'actions', 'header', 'toolbar', 'status']) {
    assert.match(scaffold, new RegExp(`name="${slot}"`))
  }
  assert.match(scaffold, /--ds-color-surface/)
  assert.match(scaffold, /<h1/)
  assert.match(surface, /--ds-color-border/)
  assert.match(layout, /class="management-workspace"/)
  assert.match(layout, /management-workspace--fullbleed/)
  assert.match(layout, /max-width: 1440px/)
})

test('reusable collection toolbar powers the main sales and operations collections', () => {
  for (const [name, page] of Object.entries({ products, customers, orders, reservations, branches, couriers, reports })) {
    assert.match(page, /ManagementCollectionToolbar/, `${name} must use the shared collection toolbar`)
  }
  assert.match(toolbar, /update:search/)
  assert.match(toolbar, /name="filters"/)
  assert.match(toolbar, /name="secondary"/)
  assert.match(toolbar, /primaryLabel/)
  assert.match(toolbar, /min-height: 44px/)
  assert.match(toolbar, /max-width: 760px/)
})

test('branch and report collections search real data fields and keep the report description contract aligned', () => {
  assert.match(branches, /:rows="filteredBranches"/)
  assert.match(branches, /const filteredBranches = computed/)
  assert.match(couriers, /@search="loadCouriers"/)
  assert.match(reports, /description: desc/)
  assert.match(reports, /:rows="filteredReports"/)
  assert.match(reports, /report\.description/)
})

test('settings hub exposes all seven categories and preserves legacy settings URLs', () => {
  for (const [key, label] of [
    ['site', 'سایت'], ['appearance', 'ظاهر و چیدمان'], ['content', 'محتوا و انتشار'],
    ['sales', 'فروش و صندوق'], ['connections', 'اتصال‌ها و پرداخت'], ['access', 'کاربران و دسترسی'], ['print', 'چاپ'],
  ]) {
    assert.match(settingsHub, new RegExp(`key: '${key}', label: '${label}'`))
  }
  for (const legacyStage of ['theme', 'page-builder', 'content', 'review', 'general', 'loader']) {
    assert.ok(settingsHub.includes(legacyStage), `legacy ${legacyStage} settings routes must be recognized`)
  }
  for (const legacyPath of ['/management/site-settings', '/management/pos-profile', '/management/pos-defaults', '/management/users', '/management/print-formats']) {
    assert.ok(app.includes(legacyPath), `${legacyPath} must route into the hub`)
  }
  assert.match(siteSettings, /hubMode/)
})

test('POS shift preferences live in the settings hub and are absent from the BI dashboard', () => {
  assert.match(settingsHub, /ManagementPosShiftSettingsPage/)
  assert.match(settingsHub, /view=shift/)
  assert.match(shiftSettings, /getManagementPOSShiftSettings/)
  assert.match(shiftSettings, /setManagementPOSShiftSettings/)
  assert.match(shiftSettings, /role="alert"/)
  assert.match(shiftSettings, /تلاش دوباره/)
  assert.doesNotMatch(dashboard, /POSShiftSettings|pos_shift|تنظیمات افتتاحیه\/اختتامیه/)
  assert.doesNotMatch(dashboard, /restaurant_menu_highlight_enabled/)
})

test('view sharing copy matches local-only persistence behavior', () => {
  assert.doesNotMatch(saveBar, /ذخیره برای همه/)
  assert.doesNotMatch(viewSystem, /saveForEveryone/)
  assert.match(saveBar, /ذخیره برای خودم/)
})
