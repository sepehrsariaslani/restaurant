import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'

const src = new URL('../src/', import.meta.url)
const apiSource = fs.readFileSync(new URL('utils/api.js', src), 'utf8')
const detailSource = fs.readFileSync(new URL('pages/management/catalog/ManagementProductDetailPage.vue', src), 'utf8')
const detailTabsSource = fs.readFileSync(new URL('utils/managementProductDetail.js', src), 'utf8')

function sourceExists(path) {
  return fs.existsSync(new URL(path, src))
}

test('product detail exposes native, connections and inventory API contracts', () => {
  assert.match(apiSource, /getManagementProductConnections/)
  assert.match(apiSource, /getManagementProductInventory/)
  assert.match(apiSource, /updateManagementProductNative/)
  assert.match(apiSource, /get_management_product_connections/)
  assert.match(apiSource, /get_management_product_inventory/)
  assert.match(detailSource, /native/)
})

test('native product panel keeps Accounts item sections and editable child tables', () => {
  assert.ok(sourceExists('utils/managementProductNative.js'))
  assert.ok(sourceExists('components/management/catalog/ManagementProductNativePanel.vue'))
  const nativeConfigSource = fs.readFileSync(new URL('utils/managementProductNative.js', src), 'utf8')
  const nativePanelSource = fs.readFileSync(new URL('components/management/catalog/ManagementProductNativePanel.vue', src), 'utf8')
  for (const section of ['classification', 'sales', 'purchase', 'inventory', 'operations', 'accounting']) {
    assert.match(nativeConfigSource, new RegExp(section))
  }
  for (const key of ['attributes', 'barcodes', 'reorder_levels', 'uoms', 'supplier_items', 'customer_items', 'taxes', 'item_defaults']) {
    assert.match(nativeConfigSource, new RegExp(key))
  }
  assert.match(nativePanelSource, /ManagementEditableTable/)
})

test('native link fields use the shared remote-searchable dropdown contract', () => {
  const nativePanelSource = fs.readFileSync(new URL('components/management/catalog/ManagementProductNativePanel.vue', src), 'utf8')
  const searchableDropdownSource = fs.readFileSync(new URL('components/SearchableDropdown.vue', src), 'utf8')
  assert.match(nativePanelSource, /search-fn/)
  assert.match(nativePanelSource, /resolve-fn/)
  assert.match(searchableDropdownSource, /searchFn/)
  assert.match(searchableDropdownSource, /loadRemoteOptions/)
})

test('connections tab uses native document links and a read-only smart table', () => {
  assert.ok(sourceExists('components/management/catalog/ManagementProductConnectionsPanel.vue'))
  const connectionsSource = fs.readFileSync(new URL('components/management/catalog/ManagementProductConnectionsPanel.vue', src), 'utf8')
  assert.match(detailTabsSource, /connections/)
  assert.match(detailSource, /connections/)
  assert.match(connectionsSource, /ManagementSmartDataTable/)
  for (const type of ['Sales Invoice', 'Purchase Receipt', 'Stock Entry', 'BOM']) {
    assert.match(connectionsSource, new RegExp(type))
  }
})

test('inventory tab exposes warehouse balance, stock ledger and native operations', () => {
  assert.ok(sourceExists('components/management/catalog/ManagementProductInventoryPanel.vue'))
  const inventorySource = fs.readFileSync(new URL('components/management/catalog/ManagementProductInventoryPanel.vue', src), 'utf8')
  assert.match(detailSource, /activeTab === ['"]inventory['"]/)
  assert.match(inventorySource, /دفتر موجودی|Stock Ledger/)
  assert.match(inventorySource, /ManagementSmartDataTable/)
  assert.match(inventorySource, /management\/inventory\/count/)
  assert.match(apiSource, /get_management_product_inventory/)
})

test('product detail has the complete operational tab contract', async () => {
  const { PRODUCT_DETAIL_TABS } = await import('../src/utils/managementProductDetail.js')
  assert.deepEqual(PRODUCT_DETAIL_TABS.map((tab) => tab.value), [
    'overview', 'settings', 'formula', 'variants', 'inventory', 'connections', 'reports',
  ])
  assert.match(detailSource, /builder.*variants|legacy|changes.*reports/)
})

test('product classification uses the native Item Group hierarchy on the product card', () => {
  const nativePanelSource = fs.readFileSync(new URL('components/management/catalog/ManagementProductNativePanel.vue', src), 'utf8')
  const productsSource = fs.readFileSync(new URL('pages/management/catalog/ManagementProductsPage.vue', src), 'utf8')
  const apiSource = fs.readFileSync(new URL('../../restaurant/api.py', import.meta.url), 'utf8')
  assert.match(detailSource, /item_group_parent/)
  assert.match(detailSource, /item_group_path/)
  assert.doesNotMatch(detailSource, /v-model="settingsForm\.restaurant_category"/)
  assert.doesNotMatch(productsSource, /v-model="createForm\.restaurant_category"/)
  assert.match(productsSource, /(?:category_title|subcategory_title):\s*['"]item_group['"]/)
  assert.match(apiSource, /item_group_parents/)
  assert.match(apiSource, /parent_item_group/)
  assert.match(nativePanelSource, /activeSection/)
})
