import test from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { resolvePickupCompanySelection } from '../src/utils/orderBranches.js'

const veederakht = {
  id: 'وی‌درخت',
  name: 'وی‌درخت',
  title: 'شرکت وی‌درخت',
  company: 'وی‌درخت',
  is_active: 1,
  pickup_available: true,
}

test('pickup selects its only eligible company automatically', () => {
  assert.equal(resolvePickupCompanySelection([veederakht]), 'وی‌درخت')
})

test('pickup keeps an existing valid selection by id or customer-facing title', () => {
  const second = { ...veederakht, id: 'شعبه دوم', name: 'شعبه دوم', company: 'شعبه دوم' }

  assert.equal(resolvePickupCompanySelection([veederakht, second], 'شعبه دوم'), 'شعبه دوم')
  assert.equal(resolvePickupCompanySelection([veederakht], 'شرکت وی‌درخت'), 'وی‌درخت')
  assert.equal(resolvePickupCompanySelection([veederakht, second]), '')
})

test('pickup does not select unavailable or non-company locations', () => {
  const diningLocation = { id: 'Main Hall', name: 'Main Hall', pickup_available: true, is_active: 1 }
  const closedCompany = { ...veederakht, id: 'بسته', name: 'بسته', company: 'بسته', isOpen: false }

  assert.equal(resolvePickupCompanySelection([veederakht, diningLocation], 'Main Hall'), 'وی‌درخت')
  assert.equal(resolvePickupCompanySelection([diningLocation], 'Main Hall'), '')
  assert.equal(resolvePickupCompanySelection([closedCompany]), '')
})

test('pickup selection styling is compact and follows the saved theme', async () => {
  const page = await readFile(new URL('../src/pages/OrderPickupPage.vue', import.meta.url), 'utf8')

  assert.match(page, /order-flow-page--pickup/)
  assert.match(page, /\.pickup-branch-card\s*\{\s*min-height:\s*0;/)
  assert.match(page, /border-inline-start:\s*3px solid var\(--ds-color-action-primary\)/)
  assert.match(page, /var\(--ds-color-border\)/)
  assert.match(page, /class="pickup-order-summary"/)
  assert.match(page, /order-flow-summary-line:nth-child\(-n \+ 4\)/)
})
