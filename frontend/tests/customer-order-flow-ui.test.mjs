import test from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'

const root = new URL('../src/', import.meta.url)

async function source(path) {
  return readFile(new URL(path, root), 'utf8')
}

test('cart line keeps the product image as a large, stable visual anchor', async () => {
  const page = await source('components/CartLineEditor.vue')

  assert.match(page, /class="product-visual"/)
  assert.match(page, /width:\s*clamp\(112px, 20vw, 144px\)/)
  assert.match(page, /aspect-ratio:\s*1/)
  assert.match(page, /object-fit:\s*cover/)
})

test('customer order flow uses company language without changing the branch data key', async () => {
  const [dineIn, pickup, delivery, orderType, cart] = await Promise.all([
    source('pages/OrderDineInPage.vue'),
    source('pages/OrderPickupPage.vue'),
    source('pages/OrderDeliveryPage.vue'),
    source('pages/OrderTypePage.vue'),
    source('pages/CartPage.vue'),
  ])

  assert.match(dineIn, />شرکت</)
  assert.match(pickup, /شرکت/)
  assert.match(delivery, /انتخاب شرکت/)
  assert.match(delivery, /branch:\s*selectedCompany\.value\?\.(id|name)/)
  assert.match(orderType, /شرکت/)
  assert.doesNotMatch(orderType, /شعبه/)
  assert.doesNotMatch(cart, /شعبه/)
})

test('checkout summarizes the selected order context in editable confirmation cards', async () => {
  const page = await source('pages/CheckoutPage.vue')

  assert.match(page, /class="[^"]*checkout-confirmation-card[^"]*"/)
  assert.match(page, /ویرایش نوع سفارش/)
  assert.match(page, /class="checkout-product-summary"/)
  assert.match(page, /if \(!context\.value\.branch\) return 'برای ارسال، انتخاب شرکت الزامی است\.'/)
})

test('cart switches to one column before image-first cards become cramped', async () => {
  const page = await source('pages/CartPage.vue')

  assert.match(page, /@media \(max-width: 760px\)/)
})
