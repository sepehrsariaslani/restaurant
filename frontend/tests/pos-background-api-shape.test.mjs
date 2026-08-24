import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'

test('background API wrapper keeps checkout and settlement calls explicit', () => {
  const api = fs.readFileSync(new URL('../src/utils/posReliabilityApi.js', import.meta.url), 'utf8')
  assert.match(api, /enqueuePOSBackgroundCheckout\(payload = \{\}, deliver_after = false\)/)
  assert.match(api, /enqueuePOSBackgroundSettlement\(order_name = '', payment = \{\}, deliver_after = false\)/)
  assert.match(api, /deliver_after: deliver_after \? 1 : 0/)
})
