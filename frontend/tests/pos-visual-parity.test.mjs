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
