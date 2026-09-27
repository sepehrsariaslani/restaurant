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
    '../src/pages/CustomerWalletPage.vue',
  ]

  for (const page of pages) {
    assert.match(source(page), /CustomerPageHeader/, `${page} should use the shared RTL customer header`)
  }
})

test('customer wallet separates withdrawable funds from purchase-only cashback', () => {
  const app = source('../src/App.vue')
  const hooks = source('../../restaurant/hooks.py')
  const wallet = source('../src/pages/CustomerWalletPage.vue')
  const management = source('../src/pages/management/customers/ManagementClubPage.vue')

  assert.match(app, /pathname\.startsWith\('\/customer\/wallet'\)/)
  assert.match(hooks, /\{"from_route": "\/customer\/wallet", "to_route": "restaurant\/index"\}/)
  assert.match(wallet, /موجودی قابل برداشت/)
  assert.match(wallet, /اعتبار خرید \(کش‌بک\)/)
  assert.match(wallet, /درخواست برداشت/)
  assert.match(management, /ثبت واریز انجام‌شده/)
  assert.match(management, /رد و بازگرداندن موجودی/)
})

test('customer order history shows order dates and item lines on warm readable surfaces', () => {
  const page = source('../src/pages/CustomerOrdersPage.vue')
  const backend = readFileSync(new URL('../../restaurant/api.py', import.meta.url), 'utf8')
  const customerOrders = backend.slice(backend.indexOf('def get_customer_orders('), backend.indexOf('def get_customer_profile('))

  assert.match(page, /v-for="\(item, index\) in order\.items"/)
  assert.match(page, /order\.created_at \|\| order\.placed_at/)
  assert.match(page, /var\(--ds-color-text-primary\)/)
  assert.match(page, /var\(--ds-color-action-accent\)/)
  assert.match(customerOrders, /order\["created_at"\] = order\.get\("placed_at"\)/)
  assert.match(customerOrders, /order\["items"\] = \[/)
})

test('customer order history exposes verified per-order feedback and edit actions', () => {
  const page = source('../src/pages/CustomerOrdersPage.vue')
  const details = source('../src/pages/CustomerOrderDetailPage.vue')
  const summary = source('../src/components/customer/CustomerOrderSurveySummary.vue')
  const survey = source('../src/pages/OrderSurveyPage.vue')
  const backend = readFileSync(new URL('../../restaurant/api_survey.py', import.meta.url), 'utf8')

  assert.match(page, /getMyOrderSurveySummaries\(orderNames\)/)
  assert.match(page, /requestMyOrderSurvey\(orderName\)/)
  assert.match(details, /CustomerOrderSurveySummary/)
  assert.match(summary, /review\.manager_reply/)
  assert.match(summary, /ویرایش نظرها/)
  assert.match(survey, /getMyOrderSurvey\(invitation, \{ edit: editMode \}\)/)
  assert.match(backend, /def get_my_order_survey_summaries\(/)
  assert.match(backend, /def request_my_order_survey\(/)
  assert.match(backend, /def _order_owned_by_identity\(/)
  assert.match(backend, /ویرایش نظر فقط از حساب مشتری انجام می‌شود/)
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

  assert.match(tokens, /primary: '#2F684F'/)
  assert.match(tokens, /accent: '#E87935'/)
  assert.match(themeSettings, /readableForeground\(normalized\.primary\)/)
  assert.match(themeSettings, /readableForeground\(normalized\.accent\)/)
})

test('optional public hero and glass headers stay on the user-selected theme', () => {
  const heroHeader = source('../src/components/SiteHeaderHero.vue')
  const glassHeader = source('../src/components/SiteHeaderGlass.vue')

  for (const fixedBrandColor of ['#174d32', '#e8a347', '#d4923a', '#fff8ee', '#f3dfc7']) {
    assert.doesNotMatch(heroHeader, new RegExp(fixedBrandColor, 'i'))
  }
  assert.match(heroHeader, /var\(--ds-color-action-accent\)/)
  assert.match(heroHeader, /var\(--ds-color-action-accent-foreground/)
  assert.match(heroHeader, /var\(--ds-color-text-primary\)/)
  assert.equal((heroHeader.match(/class="hero-cta-btn"/g) || []).length, 1)
  assert.doesNotMatch(heroHeader, /hero-cta-outline/)
  assert.match(glassHeader, /color-mix\(in srgb, var\(--ds-color-action-primary\) 84%, black\)/)
  assert.doesNotMatch(glassHeader, /#9b6a47/i)
})

test('Persian and Arabic phone digits normalize to the same mobile number', () => {
  assert.equal(normalizeMobile('۰۹۱۲ ۳۴۵ ۶۷۸۹'), '09123456789')
  assert.equal(normalizeMobile('٠٩١٢٣٤٥٦٧٨٩'), '09123456789')
})

test('frontend and server fallback themes share the green and orange palette', () => {
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
  assert.match(app, /v-if="page !== 'kitchen' && page !== 'survey'"/)
  assert.match(nav, /aria-label="ناوبری اصلی"/)
  assert.match(nav, /<small>بیشتر<\/small>/)
  assert.match(nav, /role="dialog" aria-modal="true"/)
  assert.match(nav, /customerAccountHref\('\/customer\/dashboard'\)/)
  assert.match(nav, /ShareWebsiteButton[\s\S]*?appearance="menu"[\s\S]*?label="اشتراک‌گذاری سایت"/)
  assert.match(nav, /const siteShareUrl = window\.location\.origin/)
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

test('cart feedback stays centered in RTL and clears the product sticky purchase bar', () => {
  const feedback = source('../src/components/customer/CartActionFeedback.vue')
  const detail = source('../src/pages/ItemDetailPage.vue')

  assert.match(feedback, /left:\s*50%;\s*right:\s*auto;/)
  assert.doesNotMatch(feedback, /inset-inline-start:\s*50%/)
  assert.match(feedback, /cart-action-feedback--product[\s\S]*?bottom:\s*calc\(5\.2rem \+ 6\.25rem/)
  assert.match(detail, /<CartActionFeedback :message="cartActionMessage" placement="product" \/>/)
})

test('product sharing uses the accessible, theme-aware shared control on mobile and desktop', () => {
  const share = source('../src/components/customer/ShareWebsiteButton.vue')
  const nav = source('../src/components/MobileBottomNav.vue')
  const detail = source('../src/pages/ItemDetailPage.vue')

  assert.match(share, /navigator\.share\(data\)/)
  assert.match(share, /navigator\.clipboard\?\.writeText/)
  assert.match(share, /navigator\.clipboard\.writeText\(value\)/)
  assert.match(share, /document\.execCommand\('copy'\)/)
  assert.match(share, /role="status"[\s\S]*?aria-live="polite"/)
  assert.match(share, /var\(--ds-color-action-primary\)/)
  assert.match(share, /var\(--ds-color-surface-raised\)/)
  assert.match(share, /<slot>/)
  assert.match(share, /'icon', 'action', 'menu'/)
  assert.match(nav, /@shared="closeMore"[\s\S]*?@copied="closeMore"/)
  assert.match(detail, /<ShareWebsiteButton appearance="icon" :title="item\.title \|\| 'محصول ویدرخت'" \/>/)
  assert.match(detail, /<ShareWebsiteButton appearance="action" :title="item\.title \|\| 'محصول ویدرخت'" \/>/)
  assert.doesNotMatch(detail, /shareProduct|share-toast|shareToastVisible/)
})

test('product detail keeps the site currency selected by the shared menu settings', () => {
  const menu = source('../src/pages/MenuPage.vue')
  const detail = source('../src/pages/ItemDetailPage.vue')

  assert.match(menu, /const currency = ref\(props\.boot\.currency \|\| 'IRR'\)/)
  assert.match(detail, /const currency = ref\(props\.boot\.currency \|\| 'IRR'\)/)
  assert.doesNotMatch(detail, /currency\.value\s*=\s*['"]TOMAN['"]/)
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

test('customer login keeps the form beside the brand on desktop and stacks it on mobile', () => {
  const login = source('../src/pages/CustomerLoginPage.vue')

  assert.match(login, /\.login-hero\s*\{[^}]*grid-row:\s*1;/s)
  assert.match(login, /\.login-card\s*\{[^}]*grid-row:\s*1;/s)
  assert.match(login, /@media\s*\(max-width:\s*919px\)[\s\S]*?\.login-hero\s*\{[^}]*grid-row:\s*auto;/)
  assert.match(login, /@media\s*\(max-width:\s*919px\)[\s\S]*?\.login-card\s*\{[^}]*grid-row:\s*auto;/)
})

test('customer product feedback and checkout payment surfaces follow semantic theme colors', () => {
  const detail = source('../src/pages/ItemDetailPage.vue')
  const checkout = source('../src/pages/CheckoutPage.vue')

  assert.match(detail, /\.wishlist-circle\.loved\s*\{[^}]*color:\s*var\(--ds-color-status-danger\)/s)
  assert.match(detail, /\.error-msg\s*\{[^}]*color:\s*var\(--ds-color-status-danger\)/s)
  assert.match(detail, /\.review-success\s*\{[^}]*color:\s*var\(--ds-color-status-success\)/s)
  assert.match(detail, /\.desktop-action-btn\.loved\s*\{[^}]*var\(--ds-color-status-danger\)/s)
  assert.match(detail, /\.star-btn\s*\{[^}]*color:\s*var\(--ds-color-text-muted\)/s)
  assert.match(detail, /\.related-card\s*\{[^}]*background:\s*var\(--ds-color-surface-raised\)/s)
  assert.match(detail, /\.related-img-wrap\s*\{[^}]*background:\s*var\(--ds-color-product-media-surface\)/s)
  assert.match(detail, /\.review-input,[\s\S]*?background:\s*var\(--ds-color-surface-raised\)/)
  assert.match(checkout, /\.payment-method-card\s*\{[^}]*background:\s*var\(--ds-color-surface-raised\)/s)
})

test('cart page keeps one page title row alongside the shared mobile navigation', () => {
  const cart = source('../src/pages/CartPage.vue')
  const app = source('../src/App.vue')

  assert.match(cart, /<header class="cart-heading">[\s\S]*?aria-label="بازگشت به منو"[\s\S]*?<h1>سبد سفارش<\/h1>[\s\S]*?class="cart-count-label"/)
  assert.doesNotMatch(cart, /class="top-row"|<p>سبد خرید<\/p>/)
  assert.match(app, /<MobileBottomNav\s+v-if="page !== 'kitchen' && page !== 'survey'"/)
})
