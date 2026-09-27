import test from 'node:test'
import assert from 'node:assert/strict'
import { discountInputIsManual, resolvePosDiscount } from '../src/utils/posDiscountPolicy.js'

test('customer group discount becomes the effective POS discount automatically', () => {
  assert.deepEqual(
    resolvePosDiscount({ groupDiscountPercent: 12 }),
    { type: 'percent', value: 12, source: 'customer_group', groupPercent: 12 },
  )
})

test('manual discount replaces the customer group discount even when smaller', () => {
  assert.deepEqual(
    resolvePosDiscount({
      groupDiscountPercent: 20,
      manualDiscountActive: true,
      discountType: 'percent',
      discountValue: 5,
    }),
    { type: 'percent', value: 5, source: 'manual', groupPercent: 20 },
  )
})

test('clearing manual discount returns to the customer group discount', () => {
  assert.equal(discountInputIsManual({ discountType: 'percent', discountValue: 0 }), false)
  assert.deepEqual(
    resolvePosDiscount({ groupDiscountPercent: 10, manualDiscountActive: false, discountValue: 0 }),
    { type: 'percent', value: 10, source: 'customer_group', groupPercent: 10 },
  )
})
