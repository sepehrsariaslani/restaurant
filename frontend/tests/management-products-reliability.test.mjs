import test from 'node:test'
import assert from 'node:assert/strict'
import { transformManagementProductsPage } from '../scripts/management-products-reliability-transform.mjs'

const fixture = `<script setup>
import { listManagementProducts, getMenuBoot } from '@/utils/api'
async function loadProducts() {
  const payload = await listManagementProducts({ search: '', active_only: 0, tag: '' })
  products.value = payload.products || []
}
</script>`

test('management products page uses safe product list endpoint', () => {
  const out = transformManagementProductsPage(fixture)
  assert.match(out, /listManagementProductsSafe/)
  assert.match(out, /from '@\/utils\/posReliabilityApi'/)
  assert.doesNotMatch(out, /await listManagementProducts\(/)
})
