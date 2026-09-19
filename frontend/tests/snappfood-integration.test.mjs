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
  assert.match(page, /mappingLoading \|\| !status\.schema_ready/)
  assert.match(page, /syncing \|\| !status\.schema_ready/)
})

test('Food Partner settings keeps orders and invoices on the shared POS flow', () => {
  const page = read('src/pages/management/settings/ManagementSnappfoodPage.vue')

  assert.match(page, /همان سفارش فروش و فاکتور POS/)
  assert.match(page, /همان سفارش‌های فروش و فاکتورهای POS ثبت می‌شوند/)
})
