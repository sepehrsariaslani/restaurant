import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'

test('background API wrapper keeps checkout and settlement calls explicit', () => {
  const api = fs.readFileSync(new URL('../src/utils/posReliabilityApi.js', import.meta.url), 'utf8')
  assert.match(api, /enqueuePOSBackgroundCheckout\(payload = \{\}, deliver_after = false\)/)
  assert.match(api, /enqueuePOSBackgroundSettlement\(order_name = '', payment = \{\}, deliver_after = false\)/)
  assert.match(api, /deliver_after: deliver_after \? 1 : 0/)
})

test('POS boot uses the reliability endpoint that includes offline replay support', () => {
  const api = fs.readFileSync(new URL('../src/utils/posReliabilityApi.js', import.meta.url), 'utf8')
  assert.match(api, /getReliablePOSBoot[\s\S]*restaurant\.api_pos_reliability\.get_management_pos_boot_reliable/)
})

test('offline POS mutation API uses the idempotent replay endpoint', () => {
  const api = fs.readFileSync(new URL('../src/utils/posReliabilityApi.js', import.meta.url), 'utf8')
  assert.match(api, /export function replayOfflinePOSMutation\(payload = \{\}\)/)
  assert.match(api, /restaurant\.api_pos_reliability\.replay_offline_pos_mutation/)
})
