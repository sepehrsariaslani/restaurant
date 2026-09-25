import test from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'

const root = new URL('../src/pages/', import.meta.url)

async function page(name) {
  return readFile(new URL(name, root), 'utf8')
}

test('guest dashboard shows one clear sign-in route and hides profile editing', async () => {
  const source = await page('CustomerDashboardPage.vue')

  assert.match(source, /v-if="customerMobile" href="\/customer\/profile" class="hero-profile-link"/)
  assert.match(source, /customerMobile \? 'اطلاعات حساب مشتری' : 'حساب کاربری مهمان'/)
  assert.match(source, /برای ذخیره و پیگیری سفارش‌ها وارد حساب شوید/)
  assert.match(source, /<a v-if="customerMobile" href="\/customer\/profile" class="customer-page__ghost-action">/)
  assert.match(source, /ورود \/ ثبت‌نام/)
})

test('guest profile explains the login requirement and does not expose editable fields', async () => {
  const source = await page('CustomerProfilePage.vue')

  assert.match(source, /const isLoggedIn = computed\(\(\) => Boolean\(String\(form\.value\.phone \|\| ''\)\.trim\(\)\)\)/)
  assert.match(source, /v-if="!isLoggedIn"[^]*?ورود به حساب/)
  assert.match(source, /v-else class="customer-section customer-glass-card customer-list-card"/)
  assert.match(source, /if \(!readAuth\(\)\.mobile\)[^]*?customer\/login\?redirect=\/customer\/profile/)
})

test('address saving requires a real server record and preserves manual map recovery', async () => {
  const source = await page('CustomerAddressesPage.vue')
  assert.match(source, /:open="mapStatus === 'error'"/)
  assert.match(source, /if \(!result\?\.address\?\.id\) throw/)
  assert.doesNotMatch(source, /localStorage\.setItem/)
})

test('pickup screen keeps its title, action, and selected card visually balanced', async () => {
  const source = await page('OrderPickupPage.vue')

  assert.match(source, /\.order-flow-title\s*\{[^}]*font-size:\s*clamp\(1\.55rem, 4vw, 2\.25rem\)/s)
  assert.match(source, /\.order-flow-hero > \.order-flow-secondary\s*\{[^}]*width:\s*fit-content/s)
  assert.match(source, /\.order-flow-branch-card\.active\s*\{[^}]*color-mix\(in srgb, var\(--ds-color-action-primary\)/s)
  assert.match(source, /scroll-snap-type:\s*x proximity/)
})

test('checkout keeps customer fields visible under the dynamic theme', async () => {
  const source = await page('CheckoutPage.vue')

  assert.match(source, /\.checkout-context-page \.order-flow-form \.order-flow-field\s*\{[^}]*max-width:\s*34rem/s)
  assert.match(source, /\.order-flow-input:not\(:focus\)\s*\{[^}]*color-mix\(in srgb, var\(--ds-color-border\)[^}]*var\(--ds-color-text-muted\)/s)
  assert.match(source, /\.payment-method-card\s*\{[^}]*background:\s*var\(--ds-color-surface-raised\)/s)
})
