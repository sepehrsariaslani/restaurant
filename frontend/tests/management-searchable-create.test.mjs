import test from 'node:test'
import assert from 'node:assert/strict'
import { existsSync, readFileSync } from 'node:fs'

const src = new URL('../src/', import.meta.url)
const read = (path) => readFileSync(new URL(path, src), 'utf8')

test('searchable dropdown has a generic side-panel creation contract', () => {
  const dropdown = read('components/SearchableDropdown.vue')
  assert.match(dropdown, /createConfig|create-config/)
  assert.match(dropdown, /ManagementSearchableCreateDrawer/)
  assert.match(dropdown, /createRecord|create-request|create-record/)
  assert.match(dropdown, /multiple/)
})

test('generic creation registry covers native restaurant master records', () => {
  assert.ok(existsSync(new URL('utils/managementSearchableCreate.js', src)))
  const registry = read('utils/managementSearchableCreate.js')
  for (const doctype of ['Item', 'Item Group', 'Warehouse', 'Supplier', 'Customer', 'Account', 'Price List']) {
    assert.match(registry, new RegExp(doctype.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')))
  }
  assert.match(registry, /فیلدهای ایجاد|fields/)
})

test('product grouping and master link controls opt into dynamic creation', () => {
  const product = read('pages/management/catalog/ManagementProductDetailPage.vue')
  const native = read('components/management/catalog/ManagementProductNativePanel.vue')
  assert.match(product, /create-config|createConfig/)
  assert.match(native, /create-config|createConfig/)
  assert.match(product, /multiple/)
})
