import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import path from 'node:path'

const root = path.resolve(new URL('..', import.meta.url).pathname)
const read = (file) => fs.readFileSync(path.join(root, file), 'utf8')

test('Food Partner settings blocks mapping and sync until the native schema is migrated', () => {
  const page = read('src/pages/management/settings/ManagementSnappfoodPage.vue')

  assert.match(page, /schema_ready/)
  assert.match(page, /ابتدا migrate/)
  assert.match(page, /migration اپ Restaurant را روی سایت اجرا کنید/)
  assert.match(page, /saving \|\| !status\.schema_ready/)
  assert.match(page, /mappingLoading \|\| !status\.schema_ready/)
  assert.match(page, /syncing \|\| !status\.schema_ready/)
})

test('Food Partner route has a Frappe page wrapper for the SPA entry point', () => {
  const html = read('../restaurant/www/management/snappfood.html')
  const context = read('../restaurant/www/management/snappfood.py')

  assert.match(html, /window\._PAGE = 'management-snappfood'/)
  assert.match(html, /assets\/restaurant\/frontend\/assets\/index\.js/)
  assert.match(context, /build_context\(context, "management-snappfood"\)/)
})

test('Food Partner settings keeps orders and invoices on the shared POS flow', () => {
  const page = read('src/pages/management/settings/ManagementSnappfoodPage.vue')

  assert.match(page, /همان سفارش فروش و فاکتور POS/)
  assert.match(page, /همان سفارش‌های فروش و فاکتورهای POS ثبت می‌شوند/)
})

test('Food Partner settings exposes a read-only connection test', () => {
  const page = read('src/pages/management/settings/ManagementSnappfoodPage.vue')
  const api = read('src/utils/api.js')
  const backend = read('../restaurant/api.py')

  assert.match(page, /تست اتصال/)
  assert.match(page, /testSnappfoodConnection/)
  assert.match(api, /test_snappfood_connection/)
  assert.match(backend, /def test_snappfood_connection\(\)/)
  assert.match(backend, /max_pages=1/)
})

test('Food Partner connection opens the official Partner panel without harvesting browser secrets', () => {
  const page = read('src/pages/management/settings/ManagementSnappfoodPage.vue')

  assert.match(page, /https:\/\/partner\.snappfood\.ir\//)
  assert.match(page, /ورود به پنل Partner/)
  assert.match(page, /Cookie، localStorage و Header مرورگر جمع‌آوری نمی‌شود/)
  assert.doesNotMatch(page, /document\.cookie|localStorage\.getItem\(['"](?:token|authorization|cookie)/i)
})

test('Food Partner token helper supports explicit clipboard paste without reading Partner storage', () => {
  const page = read('src/pages/management/settings/ManagementSnappfoodPage.vue')

  assert.match(page, /چسباندن از کلیپ‌بورد/)
  assert.match(page, /navigator\.clipboard\.readText\(\)/)
  assert.match(page, /نمایش توکن|مخفی‌کردن توکن/)
  assert.doesNotMatch(page, /partner\.snappfood\.ir[^\n]+(?:localStorage|document\.cookie)/i)
})

test('Food Partner settings lets the server infer vendor ID from a saved token and surfaces menu API errors', () => {
  const page = read('src/pages/management/settings/ManagementSnappfoodPage.vue')
  const backend = read('../restaurant/api.py')
  const sync = read('../restaurant/snapp_sync.py')

  assert.match(page, /توکن خودکار تشخیص داده می‌شود/)
  assert.match(page, /data\?\.status === 'error'/)
  assert.match(backend, /_extract_vendor_id_from_token/)
  assert.match(backend, /"status": "error"/)
  assert.match(sync, /_normalize_bearer_token/)
  assert.match(sync, /401, 403/)
})

test('Food Partner mapping renders category context with product and variation IDs', () => {
  const page = read('src/pages/management/settings/ManagementSnappfoodPage.vue')

  assert.match(page, /row\.category_title/)
  assert.match(page, /row\.variation_id/)
  assert.match(page, /row\.product_id/)
})

test('Food Partner mapping can load and display menu categories', () => {
  const page = read('src/pages/management/settings/ManagementSnappfoodPage.vue')
  const api = read('src/utils/api.js')
  const backend = read('../restaurant/api.py')
  const sync = read('../restaurant/snapp_sync.py')

  assert.match(page, /دریافت گروه‌های کالا/)
  assert.match(page, /category\.title/)
  assert.match(api, /getSnappfoodCategories/)
  assert.match(backend, /def get_snappfood_categories\(/)
  assert.match(sync, /menu-category/)
})

test('Food Partner settings makes disabled automatic invoicing explicit', () => {
  const page = read('src/pages/management/settings/ManagementSnappfoodPage.vue')

  assert.match(page, /فاکتور خودکار خاموش/)
  assert.match(page, /برای ثبت فاکتور native در همان POS/)
})
