import test from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'

const page = await readFile(new URL('../src/pages/OrderSuccessPage.vue', import.meta.url), 'utf8')

test('order success page does not claim success when the URL has no order code', () => {
  assert.match(page, /orderCode \? 'سفارش شما ثبت شد' : 'پیگیری سفارش'/)
  assert.match(page, /<button v-if="orderCode" class="primary-btn"[^>]*@click="loadOrder"/s)
  assert.match(page, /v-if="!orderCode"[^]*کد سفارش در آدرس پیدا نشد/)
})
