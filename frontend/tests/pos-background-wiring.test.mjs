import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'

test('vite wires background POS and expiry-aware product transforms after reliability transforms', () => {
  const vite = fs.readFileSync(new URL('../vite.config.js', import.meta.url), 'utf8')
  assert.match(vite, /transformPosBackgroundPage/)
  assert.match(vite, /transformPosProductPanelAvailability/)
  assert.match(vite, /transformPosBackgroundPage\(\s*transformPosReliabilityPage\(transformManagementPosPage\(code\)\)/s)
  assert.match(vite, /transformPosProductPanelAvailability\(transformPosProductPanel\(code\)\)/)
})

test('reliable boot client uses fail-safe boot endpoint and exposes background job APIs', () => {
  const api = fs.readFileSync(new URL('../src/utils/posReliabilityApi.js', import.meta.url), 'utf8')
  assert.match(api, /api_pos_background\.get_management_pos_boot_safe/)
  assert.match(api, /enqueuePOSBackgroundCheckout/)
  assert.match(api, /enqueuePOSBackgroundSettlement/)
  assert.match(api, /getPOSBackgroundOperation/)
})
