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

test('background POS API exposes invoice purge as a queued operation', () => {
  const api = fs.readFileSync(new URL('../../restaurant/api_pos_background.py', import.meta.url), 'utf8')
  assert.match(api, /def enqueue_pos_purge\(order_name=""\)/)
  assert.match(api, /def run_pos_background_purge\(job_key, order_name\)/)
  assert.match(api, /purge_management_pos_order\(order_name\)/)
  assert.match(api, /summary = result\.get\("summary"\)/)
  assert.match(api, /"summary": summary if isinstance\(summary, dict\) else \{\}/)
})
