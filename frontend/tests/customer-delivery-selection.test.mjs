import test from 'node:test'
import assert from 'node:assert/strict'
import { resolveDeliveryCompanySelection } from '../src/utils/orderBranches.js'

const veederakht = {
  id: 'وی‌درخت',
  name: 'وی‌درخت',
  company: 'وی‌درخت',
  is_active: 1,
  delivery_available: true,
}

test('delivery selects its only eligible company automatically', () => {
  assert.equal(resolveDeliveryCompanySelection([veederakht]), 'وی‌درخت')
})

test('delivery preserves a valid selection when several companies are available', () => {
  const second = { ...veederakht, id: 'شعبه دوم', name: 'شعبه دوم', company: 'شعبه دوم' }

  assert.equal(resolveDeliveryCompanySelection([veederakht, second], 'شعبه دوم'), 'شعبه دوم')
  assert.equal(resolveDeliveryCompanySelection([veederakht, second]), '')
})

test('delivery clears unavailable selections and excludes non-company locations', () => {
  const diningLocation = { id: 'Main Hall', name: 'Main Hall', delivery_available: true, is_active: 1 }

  assert.equal(resolveDeliveryCompanySelection([veederakht, diningLocation], 'Main Hall'), 'وی‌درخت')
  assert.equal(resolveDeliveryCompanySelection([diningLocation], 'Main Hall'), '')
})
