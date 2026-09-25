import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import test from 'node:test'
import { customerAccountHref, hasCustomerSession } from '../src/utils/customerAuth.js'
import { normalizeMobile } from '../src/utils/format.js'
import { designTokens } from '../src/design-system/tokens.js'

const source = (path) => readFileSync(new URL(path, import.meta.url), 'utf8')

test('customer account and service pages use the shared page header', () => {
  const pages = [
    '../src/pages/CustomerAddressesPage.vue',
    '../src/pages/CustomerBranchesPage.vue',
    '../src/pages/CustomerDashboardPage.vue',
    '../src/pages/CustomerDeliveryPage.vue',
    '../src/pages/CustomerOrderDetailPage.vue',
    '../src/pages/CustomerOrdersPage.vue',
    '../src/pages/CustomerProfilePage.vue',
    '../src/pages/CustomerTableReservationPage.vue',
  ]

  for (const page of pages) {
    assert.match(source(page), /CustomerPageHeader/, `${page} should use the shared RTL customer header`)
  }
})

test('customer branches exclude non-company locations and handle missing media and map URLs', () => {
  const page = source('../src/pages/CustomerBranchesPage.vue')

  assert.match(page, /branches\.value\.filter\(isCustomerCompany\)/)
  assert.match(page, /branch\.image && !imageFailed\(branch\)/)
  assert.match(page, /rawUrl === 'https:\/\/maps\.google\.com'/)
  assert.match(page, /return `\/menu\?branch=\$\{encodeURIComponent\(branchKey\(branch\)\)\}`/)
  assert.match(page, /role="status" aria-live="polite"/)
})

test('table reservation selects live available tables and the legacy route returns to that flow', () => {
  const reservation = source('../src/pages/CustomerTableReservationPage.vue')
  const legacyRoute = source('../src/pages/CustomerTableSelectPage.vue')

  assert.match(reservation, /getAvailableTables\(/)
  assert.match(reservation, /:disabled="!t\.is_available"/)
  assert.match(reservation, /aria-pressed="selectedTable\?\.id === t\.id"/)
  assert.doesNotMatch(legacyRoute, /const tables = \[/)
  assert.match(legacyRoute, /window\.location\.replace\('\/table-reservation\?step=table'\)/)
})

test('Veederakht default colors use readable, runtime-derived foregrounds', () => {
  const tokens = source('../src/design-system/tokens.js')
  const themeSettings = source('../src/utils/themeSettings.js')

  assert.match(tokens, /primary: '#B94712'/)
  assert.match(tokens, /accent: '#DFAF2E'/)
  assert.match(themeSettings, /readableForeground\(normalized\.primary\)/)
  assert.match(themeSettings, /readableForeground\(normalized\.accent\)/)
})

test('Persian and Arabic phone digits normalize to the same mobile number', () => {
  assert.equal(normalizeMobile('۰۹۱۲ ۳۴۵ ۶۷۸۹'), '09123456789')
  assert.equal(normalizeMobile('٠٩١٢٣٤٥٦٧٨٩'), '09123456789')
})

test('frontend and server fallback themes share the orange and saffron palette', () => {
  const backend = readFileSync(new URL('../../restaurant/api.py', import.meta.url), 'utf8')
  const defaults = backend.match(/MANAGEMENT_THEME_DEFAULTS = \{([\s\S]*?)\n\}/)?.[1]

  assert.ok(defaults, 'server theme defaults should be declared')
  for (const key of ['primary', 'accent', 'success', 'danger', 'warning', 'surface', 'surfaceAlt', 'background', 'border', 'text', 'textSecondary', 'muted']) {
    const value = designTokens.color.primitive[key]
    assert.ok(defaults.includes(`"${key}": "${value}"`), `server ${key} should match frontend token ${value}`)
  }
  assert.ok(defaults.includes(`"posAccent": "${designTokens.color.primitive.accent}"`))
})

test('mobile account links send guests to sign-in and return to the requested account page', () => {
  const values = new Map()
  const storage = { getItem: (key) => values.get(key) || null }

  assert.equal(hasCustomerSession(storage), false)
  values.set('customer_phone', '09123456789')
  assert.equal(hasCustomerSession(storage), false, 'guest checkout contact data is not an authenticated session')
  assert.equal(customerAccountHref('/customer/dashboard', storage), '/customer/login?redirect=%2Fcustomer%2Fdashboard')
  assert.equal(customerAccountHref('/customer/orders', storage), '/customer/login?redirect=%2Fcustomer%2Forders')

  values.set('restaurant-customer-auth-v1', JSON.stringify({ mobile: '09123456789' }))
  assert.equal(hasCustomerSession(storage), true)
  assert.equal(customerAccountHref('/customer/orders', storage), '/customer/orders')
  assert.equal(customerAccountHref('//example.com', storage), '/customer/dashboard')
})

test('mobile browsing uses one shared bottom bar and opens the extra links as an accessible sheet', () => {
  const app = source('../src/App.vue')
  const nav = source('../src/components/MobileBottomNav.vue')
  const landing = source('../src/pages/RestaurantLandingPage.vue')

  assert.match(app, /class="desktop-public-header"/)
  assert.match(app, /\.desktop-public-header\s*\{\s*display:\s*none;/)
  assert.match(app, /\.order-flow-page--mobile-cta\)\s*\{\s*padding-bottom:\s*calc\(150px/s)
  assert.match(app, /\.order-mobile-cta\)\s*\{\s*bottom:\s*calc\(4\.8rem/s)
  assert.match(app, /v-if="page !== 'kitchen'"/)
  assert.match(nav, /aria-label="ناوبری اصلی"/)
  assert.match(nav, /<small>بیشتر<\/small>/)
  assert.match(nav, /role="dialog" aria-modal="true"/)
  assert.match(nav, /customerAccountHref\('\/customer\/dashboard'\)/)
  assert.match(landing, /class="desktop-public-header"/)
  assert.doesNotMatch(app, /page !== 'item'/)
})

test('item additions keep the order cart but avoid the duplicate floating cart and forced redirect', () => {
  const menu = source('../src/pages/MenuPage.vue')
  const home = source('../src/pages/RestaurantLandingPage.vue')
  const detail = source('../src/pages/ItemDetailPage.vue')
  const builder = source('../src/components/ProductBuilderWizard.vue')
  const dashboard = source('../src/pages/CustomerDashboardPage.vue')

  assert.match(menu, /<CartActionFeedback :message="cartFeedback" \/>/)
  assert.doesNotMatch(menu, /sticky-cart|cartTotal/)
  assert.doesNotMatch(home, /home-sticky-cart/)
  assert.match(detail, /showCartActionFeedback\(`\$\{item\.value\.title \|\| 'محصول'\} به سبد سفارش اضافه شد\.`\)/)
  assert.doesNotMatch(detail, /window\.location\.href = '\/cart'\n\}/)
  assert.doesNotMatch(builder, /success-overlay|showSuccess/)
  assert.doesNotMatch(dashboard, /cartCount|class="account-action-card customer-glass-card" href="\/cart"/)
})

test('customer account surfaces use live theme colors and the guest dashboard requires sign-in', () => {
  const theme = source('../src/theme.css')
  const dashboard = source('../src/pages/CustomerDashboardPage.vue')
  const login = source('../src/pages/CustomerLoginPage.vue')

  assert.match(theme, /\.customer-page__hero\s*\{[^}]*var\(--ds-color-action-primary\)/s)
  assert.match(theme, /\.customer-glass-card\s*\{[^}]*var\(--ds-color-surface-raised\)/s)
  assert.match(theme, /\.customer-icon-badge\s*\{[^}]*var\(--ds-color-action-accent\)/s)
  assert.match(dashboard, /window\.location\.replace\('\/customer\/login\?redirect=%2Fcustomer%2Fdashboard'\)/)
  assert.match(login, /postLoginDestination\(\)/)
  assert.match(login, /destination\.origin !== window\.location\.origin/)
})
