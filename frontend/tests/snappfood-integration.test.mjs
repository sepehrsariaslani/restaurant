import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import path from 'node:path'
import { groupSnappfoodMappingRows } from '../src/utils/snappfoodMapping.js'

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
  const mapping = read('src/utils/snappfoodMapping.js')

  assert.match(page, /row\.variation_id/)
  assert.match(page, /product\.product_id/)
  assert.match(page, /product\.rows/)
  assert.match(mapping, /row\.category_title/)
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

test('Food Partner mapping groups all variations under one parent product and maps them to one Item', () => {
  const page = read('src/pages/management/settings/ManagementSnappfoodPage.vue')
  const backend = read('../restaurant/snapp_sync.py')
  const api = read('../restaurant/api.py')

  assert.match(page, /category-accordion/)
  assert.match(page, /toggleCategory/)
  assert.match(page, /categorySections/)
  assert.match(page, /groupSnappfoodMappingRows/)
  assert.match(page, /ثبت یک Item برای \$\{product\.rows\.length\} گزینه/)
  assert.match(page, /map_product_group: 1/)
  assert.match(page, /عنوان گزینه در سفارش حفظ می‌شود/)
  assert.match(backend, /def _find_mapped_product_group_item\(/)
  assert.match(backend, /map_product_group=False/)
  assert.match(api, /map_product_group=bool\(cint\(payload\.get\("map_product_group"\)\)\)/)
})

test('Food Partner mapping can create a native Item without importing an order', () => {
  const page = read('src/pages/management/settings/ManagementSnappfoodPage.vue')
  const api = read('src/utils/api.js')
  const backend = read('../restaurant/api.py')
  const sync = read('../restaurant/snapp_sync.py')

  assert.match(page, /ساخت Item و نگاشت گزینه‌ها/)
  assert.match(page, /createItemFromProductGroup/)
  assert.match(api, /createSnappfoodItemFromMapping/)
  assert.match(backend, /def create_snappfood_item_from_mapping\(/)
  assert.match(sync, /def create_snappfood_item_from_mapping\(/)
  assert.doesNotMatch(page, /createItemFromProductGroup[\s\S]{0,500}importSnappfoodOrders/)
})

test('Food Partner mapping distinguishes an exact ID mapping from a name suggestion', () => {
  const page = read('src/pages/management/settings/ManagementSnappfoodPage.vue')
  const mapping = read('src/utils/snappfoodMapping.js')
  const sync = read('../restaurant/snapp_sync.py')

  assert.match(page, /product\.mapping_status === 'Mapped'/)
  assert.match(mapping, /row\.mapping_status === 'Mapped'/)
  assert.match(mapping, /row\.mapped_item/)
  assert.match(page, /mappingDrafts\[product\.key\] = product\.mapped_item\?\.name/)
  assert.match(page, /پیشنهاد بر اساس نام.*هنوز ثبت نشده/)
  assert.match(sync, /def _find_mapped_local_item\(/)
  assert.match(sync, /"mapping_status": "Mapped" if exact else "Unmapped"/)
})

test('Products list exposes the same exact Food Partner mapping status', () => {
  const productsApi = read('../restaurant/api.py')
  const productsPage = read('src/pages/management/catalog/ManagementProductsPage.vue')
  const viewSystem = read('src/utils/viewSystem.js')

  assert.match(productsApi, /"restaurant_external_mapping_status"/)
  assert.match(productsApi, /"restaurant_external_menu_item_id"/)
  assert.match(productsPage, /Food Partner: نگاشت واقعی/)
  assert.match(viewSystem, /restaurant_external_mapping_status/)
})

test('Food Partner mapping has an independent Item search and controlled automatic mapping actions', () => {
  const page = read('src/pages/management/settings/ManagementSnappfoodPage.vue')
  const api = read('src/utils/api.js')
  const backend = read('../restaurant/api.py')
  const sync = read('../restaurant/snapp_sync.py')

  assert.match(page, /جستجوی Item داخلی/)
  assert.match(page, /searchSnappfoodItems/)
  assert.match(page, /نگاشت خودکار موارد قطعی/)
  assert.match(page, /ساخت و نگاشت کالاهای غایب/)
  assert.match(api, /search_snappfood_items/)
  assert.match(api, /auto_map_snappfood_items/)
  assert.match(backend, /def search_snappfood_items\(/)
  assert.match(backend, /def auto_map_snappfood_items\(/)
  assert.match(sync, /def _plan_snappfood_auto_mapping\(/)
  const autoMappingFunction = page.slice(page.indexOf('async function runAutoMapping'), page.indexOf('async function syncToday'))
  assert.doesNotMatch(autoMappingFunction, /importSnappfoodOrders/)
})

test('Food Partner product mapping uses the shared searchable dropdown with server-side Item search', () => {
  const page = read('src/pages/management/settings/ManagementSnappfoodPage.vue')

  assert.match(page, /import SearchableDropdown from '@\/components\/SearchableDropdown\.vue'/)
  assert.match(page, /v-model="mappingDrafts\[product\.key\]"[\s\S]{0,360}:options="mappingItemOptions"[\s\S]{0,180}:search-fn="searchMappingItemOptions"/)
  assert.match(page, /searchMappingItemOptions\(search = ''\)/)
  assert.match(page, /searchSnappfoodItems\(\{ search: query, limit: 50 \}\)/)
  assert.match(page, /item\.item_name \|\| item\.name/)
})

test('Food Partner parent product keeps each variation as a modifier option in the same mapping group', () => {
  const sections = groupSnappfoodMappingRows([
    {
      category_id: 'rice-bowls',
      category_title: 'کاسه برنجین',
      product_id: '34911711',
      product_title: 'کاسه برنجین میگو',
      external_id: '34911711',
      variation_id: '34911711',
      variation_title: 'پلو میکس ساده',
      title: 'کاسه برنجین میگو پلو میکس ساده',
      price: 979000,
    },
    {
      category_id: 'rice-bowls',
      category_title: 'کاسه برنجین',
      product_id: '34911711',
      product_title: 'کاسه برنجین میگو',
      external_id: '34935660',
      variation_id: '34935660',
      variation_title: 'پلو میکس مکزیکی',
      title: 'کاسه برنجین میگو پلو میکس مکزیکی',
      price: 999000,
    },
  ])

  assert.equal(sections.length, 1)
  assert.equal(sections[0].products.length, 1)
  assert.equal(sections[0].products[0].title, 'کاسه برنجین میگو')
  assert.deepEqual(sections[0].products[0].rows.map((row) => row.variation_title), ['پلو میکس ساده', 'پلو میکس مکزیکی'])
})

test('Food Partner exposes a date-range preview and capped selected-order import flow', () => {
  const page = read('src/pages/management/settings/ManagementSnappfoodPage.vue')
  const api = read('src/utils/api.js')
  const backend = read('../restaurant/api.py')
  const sync = read('../restaurant/snapp_sync.py')

  assert.match(page, /سفارش‌های دیروز|سفارش‌های بازهٔ تاریخی/)
  assert.match(page, /previewSnappfoodOrders/)
  assert.match(page, /importSnappfoodOrders/)
  assert.match(page, /حداکثر ۳ سفارش/)
  assert.match(page, /orderWindow\.from_date/)
  assert.match(page, /مشتری Food Partner در مشتری ثانویه ثبت می‌شود/)
  assert.match(sync, /secondary_customer/)
  assert.match(api, /preview_snappfood_orders/)
  assert.match(api, /import_snappfood_orders/)
  assert.match(backend, /def preview_snappfood_orders\(/)
  assert.match(backend, /def import_snappfood_orders\(/)
  assert.match(sync, /_select_snapp_orders_for_import/)
})
