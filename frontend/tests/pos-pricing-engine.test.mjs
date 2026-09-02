import test from 'node:test'
import assert from 'node:assert/strict'
import { normalizePosPercentageModifier } from '../src/utils/posPricingEngine.js'

test('switches an oversized service percentage to its fixed equivalent', () => {
  assert.deepEqual(
    normalizePosPercentageModifier('percent', 125, 400_000),
    { type: 'fixed', value: 500_000 },
  )
})

test('keeps a valid service percentage unchanged', () => {
  assert.deepEqual(
    normalizePosPercentageModifier('percent', 15, 400_000),
    { type: 'percent', value: 15 },
  )
})
