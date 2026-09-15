import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'

const frontendSrc = new URL('../src/', import.meta.url)
const apiSource = readFileSync(new URL('utils/api.js', frontendSrc), 'utf8')
const appSource = readFileSync(new URL('App.vue', frontendSrc), 'utf8')
const layoutSource = readFileSync(new URL('components/management/ManagementLayout.vue', frontendSrc), 'utf8')
const pageSource = readFileSync(new URL('pages/management/inventory/ManagementProductStockLedgerPage.vue', frontendSrc), 'utf8')
const backendSource = readFileSync(new URL('../../restaurant/api_inventory.py', import.meta.url), 'utf8')

test('stock ledger has a paginated frontend and route contract', () => {
  assert.match(apiSource, /getManagementProductStockLedger/)
  assert.match(apiSource, /get_management_product_stock_ledger/)
  assert.match(pageSource, /ManagementSmartDataTable/)
  assert.match(pageSource, /page|limit|offset/)
  assert.match(pageSource, /date_from|date-to/)
  assert.match(appSource, /management-inventory-ledger/)
  assert.match(appSource, /inventory\/ledger/)
  assert.match(layoutSource, /دفتر گردش کالا|management-inventory-ledger/)
})

test('stock ledger backend limits and paginates database rows', () => {
  assert.match(backendSource, /def get_management_product_stock_ledger/)
  assert.match(backendSource, /limit_start|offset/)
  assert.match(backendSource, /COUNT\(\*\)|total_count|total_rows/)
  assert.match(backendSource, /LIMIT %\(limit\)s OFFSET %\(offset\)s|LIMIT %\(offset\)s, %\(limit\)s/)
})
