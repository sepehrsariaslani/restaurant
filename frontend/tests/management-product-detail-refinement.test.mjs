import test from 'node:test'
import assert from 'node:assert/strict'
import { existsSync, readFileSync } from 'node:fs'

const sourceRoot = new URL('../src/', import.meta.url)
const read = (path) => readFileSync(new URL(path, sourceRoot), 'utf8')
const exists = (path) => existsSync(new URL(path, sourceRoot))

test('product detail exposes reusable overview and tab components', () => {
  assert.ok(exists('components/management/catalog/ManagementProductOverviewCard.vue'))
  assert.ok(exists('components/management/catalog/ManagementProductDetailTabs.vue'))
  const page = read('pages/management/catalog/ManagementProductDetailPage.vue')
  assert.match(page, /ManagementProductOverviewCard/)
  assert.match(page, /ManagementProductDetailTabs/)
})

test('product detail keeps important identity and status content visible on small screens', () => {
  const page = read('pages/management/catalog/ManagementProductDetailPage.vue')
  const overview = read('components/management/catalog/ManagementProductOverviewCard.vue')
  assert.doesNotMatch(page, /product-general-card--compact \.pg-name-field,\s*\n\s*\.product-general-card--compact \.pg-status-row/)
  assert.match(overview, /general-image-shell[\s\S]*min-height: 220px/)
  assert.match(overview, /pg-status-row[\s\S]*flex-wrap: wrap/)
})

test('product detail has one Persian history component and no data-boundaries card', () => {
  assert.ok(exists('components/management/catalog/ManagementProductHistoryPanel.vue'))
  const page = read('pages/management/catalog/ManagementProductDetailPage.vue')
  const connections = read('components/management/catalog/ManagementProductConnectionsPanel.vue')
  const history = read('components/management/catalog/ManagementProductHistoryPanel.vue')
  assert.match(page, /ManagementProductHistoryPanel/)
  assert.doesNotMatch(connections, /مرزهای داده/)
  assert.match(history, /ManagementSmartDataTable/)
  assert.doesNotMatch(history, /ERPNext|Stock Ledger Entry|>Version<|>Comment</)
})

test('product detail links to a dedicated stock ledger page', () => {
  const page = read('pages/management/catalog/ManagementProductDetailPage.vue')
  const inventory = read('components/management/catalog/ManagementProductInventoryPanel.vue')
  assert.ok(exists('pages/management/inventory/ManagementProductStockLedgerPage.vue'))
  assert.match(page, /ManagementProductInventoryPanel/)
  assert.match(inventory, /management\/inventory\/ledger/)
  assert.doesNotMatch(inventory, /<ManagementSmartDataTable[\s\S]*:rows="ledger"/)
})
