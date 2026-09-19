import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import path from 'node:path'

const root = path.resolve(new URL('..', import.meta.url).pathname)
const read = (file) => fs.readFileSync(path.join(root, file), 'utf8')

test('POS product cards use one reusable reference component for every view', () => {
  const panel = read('src/components/management/pos/PosProductPanel.vue')
  const card = read('src/components/management/pos/ManagementPosProductCard.vue')

  assert.match(panel, /ManagementPosProductCard/)
  assert.doesNotMatch(panel, /class="product-card"/)
  assert.doesNotMatch(panel, /class="compact-card"/)
  assert.match(card, /pos-product-card--\$\{view\}/)
  assert.match(card, /pos-product-card--compact/)
  assert.match(card, /pos-product-card--list/)
  assert.match(card, /pos-product-card__customize/)
  assert.doesNotMatch(card, /pos-product-card__bom/)
  assert.match(card, /object-fit:\s*cover/)
  assert.match(card, /min-height:\s*128px/)
})

test('POS shared controls use the Restaurant design-system button contract', () => {
  const panel = read('src/components/management/pos/PosProductPanel.vue')
  const button = read('src/components/design/DsButton.vue')

  assert.match(panel, /@\/components\/design\/DsButton\.vue/)
  assert.match(panel, /<DsButton/)
  assert.match(button, /<slot name="leading"\s*\/>/)
  assert.match(button, /<slot\s*\/>/)
  assert.match(button, /<slot name="trailing"\s*\/>/)
})

test('POS guest count uses the Persian numeric input component', () => {
  const header = read('src/components/management/pos/PosHeaderBar.vue')

  assert.match(header, /@\/components\/PersianNumberInput\.vue/)
  assert.match(header, /<PersianNumberInput/)
  assert.match(header, /aria-label="تعداد مهمان"/)
  assert.doesNotMatch(header, /type="number"/)
})

test('POS reference surfaces are discoverable in the design system catalog', () => {
  const catalog = read('src/design-system/catalog.js')

  assert.match(catalog, /management-pos-product-card/)
  assert.match(catalog, /pos-workspace/)
})

test('POS desktop workspace keeps products on the left and cart on the right', () => {
  const page = read('src/pages/management/sales/ManagementPosPage.vue')

  assert.match(page, /\.pos-main-grid\s*\{[\s\S]*direction:\s*ltr/)
  assert.match(page, /\.products-col\s*\{[\s\S]*direction:\s*rtl/)
  assert.match(page, /\.cart-desktop-col\s*\{[\s\S]*direction:\s*rtl/)
})

test('POS keeps order metadata in the cart panel instead of the product surface', () => {
  const panel = read('src/components/management/pos/PosProductPanel.vue')
  const cart = read('src/components/management/pos/PosCartPanel.vue')
  const page = read('src/pages/management/sales/ManagementPosPage.vue')

  assert.doesNotMatch(panel, /secondary-customer-field|secondaryCustomerVisible/)
  assert.match(cart, /مشتری ثانویه \/ تحویل‌گیرنده/)
  assert.match(cart, /<SearchableDropdown[\s\S]*fixed-panel/)
  assert.match(cart, /<PersianNumberInput[\s\S]*aria-label="تعداد نفرات"/)
  assert.match(page, /:secondary-customer="form\.secondary_customer"/)
  assert.match(page, /:guest-count="form\.guest_count"/)
  assert.match(page, /:waiter-options="waiterOptions"/)
})

test('POS marks Food Partner orders inside its shared transaction views', () => {
  const page = read('src/pages/management/sales/ManagementPosPage.vue')

  assert.match(page, /function isSnappFoodOrder\(order = \{\}\)/)
  assert.match(page, /external_source/)
  assert.match(page, /اسنپ‌فود/)
  assert.match(page, /isSnappFoodOrder\(tx\)/)
  assert.match(page, /isSnappFoodOrder\(order\)/)
})

test('POS refreshes the shared native order lists while the cashier screen is visible', () => {
  const page = read('src/pages/management/sales/ManagementPosPage.vue')

  assert.match(page, /const SHARED_POS_REFRESH_MS = 60000/)
  assert.match(page, /async function refreshSharedPOSLists\(\)/)
  assert.match(page, /const requests = \[loadOpenInvoices\(true\)\]/)
  assert.match(page, /document\.addEventListener\('visibilitychange', handlePOSVisibilityChange\)/)
  assert.match(page, /sharedPosRefreshTimer = setInterval\(refreshSharedPOSLists, SHARED_POS_REFRESH_MS\)/)
  assert.match(page, /clearInterval\(sharedPosRefreshTimer\)/)
})

test('POS keeps Food Partner traceability inline in the native order detail', () => {
  const page = read('src/pages/management/sales/ManagementPosPage.vue')

  assert.match(page, /od-external-meta/)
  assert.match(page, /external_bill_number/)
  assert.match(page, /external_order_id/)
  assert.match(page, /external_state/)
})

test('POS financial controls hide unused rows and style nested amount inputs consistently', () => {
  const cart = read('src/components/management/pos/PosCartPanel.vue')

  assert.doesNotMatch(cart, /<span>انعام<\/span>/)
  assert.doesNotMatch(cart, /<span>بسته‌بندی<\/span>/)
  assert.match(cart, /\.fin-control :deep\(\.number-input\)/)
  assert.match(cart, /\.fin-control :deep\(\.number-input:focus\)/)
  assert.match(cart, /min-height:\s*44px/)
  assert.match(cart, /height:\s*44px/)
})

test('Persian numeric input keeps zero as an empty editable value', () => {
  const input = read('src/components/PersianNumberInput.vue')

  assert.match(input, /inputText\.value = clamped \? formatForDisplay\(clamped\) : ''/)
  assert.match(input, /if \(!numeric\) \{\s*return ''/)
})

test('POS uses the Accounts-style empty numeric contract and removes tip and packaging surfaces', () => {
  const cart = read('src/components/management/pos/PosCartPanel.vue')
  const page = read('src/pages/management/sales/ManagementPosPage.vue')

  assert.match(cart, /empty-as-null/)
  assert.match(cart, /input-class="pos-amount-input"/)
  assert.doesNotMatch(page, /tipAmount/)
  assert.doesNotMatch(page, /packagingAmount/)
  assert.doesNotMatch(page, /انعام/)
  assert.doesNotMatch(page, /بسته‌بندی/)
})
