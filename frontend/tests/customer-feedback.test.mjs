import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import test from 'node:test'

const source = (path) => readFileSync(new URL(path, import.meta.url), 'utf8')

test('customer dashboard lets an authenticated customer submit and track feedback', () => {
  const page = source('../src/pages/CustomerDashboardPage.vue')
  const api = source('../src/utils/api.js')

  assert.match(api, /submit_my_customer_voice/)
  assert.match(api, /list_my_customer_voices/)
  assert.match(page, /submitMyCustomerVoice/)
  assert.match(page, /listMyCustomerVoices/)
  assert.match(page, /پیشنهادها و انتقادهای من/)
  assert.match(page, /v-model="voiceForm\.type"/)
  assert.match(page, /v-model(?:\.trim)?="voiceForm\.subject"/)
  assert.match(page, /v-model(?:\.trim)?="voiceForm\.message"/)
  assert.match(page, /v-model(?:\.trim)?="voiceForm\.order_code"/)
  assert.match(page, /voice\.status/)
  assert.match(page, /voice\.response/)
})

test('product detail keeps manager replies visible alongside public reviews', () => {
  const page = source('../src/pages/ItemDetailPage.vue')
  const backend = source('../../restaurant/api.py')

  assert.match(page, /rv\.manager_reply/)
  assert.match(page, /fetchItemReviews/)
  assert.match(backend, /"manager_reply": row\.get\("manager_reply"\) or ""/)
})
