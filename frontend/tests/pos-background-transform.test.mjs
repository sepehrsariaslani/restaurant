import test from 'node:test'
import assert from 'node:assert/strict'
import {
  transformPosBackgroundPage,
  transformPosProductPanelAvailability,
} from '../scripts/pos-background-transform.mjs'

const fixture = `
<template>
<section class="pos-theme pos-fullpage">
  <p class="error pos-inline-error" v-if="error">{{ error }}</p>
  <div class="qe-field">
    <span>موجودی</span>
    <div class="stock-toggle-row">
      <button @click="quickEditForm.out_of_stock = !quickEditForm.out_of_stock">stock</button>
    </div>
    <template v-if="quickEditForm.out_of_stock"><PersianDateInput /></template>
  </div>
</section>
</template>
<script setup>
import { formatMoney } from '@/utils/format'
const offlineSyncing = ref(false)
async function submitPOSOrder(payNow = true, paymentMeta = {}, withProduction = false) {
  if (!cart.length) return
  const payload = { items: [], payment: paymentPayload }
  if (isOffline.value) return
  submitting.value = true
  try {
    let result
    if (payNow) {
      if (editingOriginalOrder.isEditing && editingOriginalOrder.name) {
        result = await settlePOSOrder(editingOriginalOrder.name, {})
      } else if (withProduction) {
        result = await createAndSettlePOSOrder(payload)
      } else {
        result = await createAndPayPOSOrder(payload)
      }
    }
  } finally { submitting.value = false }
}
async function settleSelectedInvoice(invoice, paymentSelection = {}) {
  if (!invoice?.name) return
  settlingOpenInvoice.value = true
}
async function settleAndDeliverFromInvoice(invoice, paymentSelection = {}) {
  if (!invoice?.name) return
  settlingOpenInvoice.value = true
}
async function confirmSettleOrder() {
  if (!orderDetailModal.order?.name) return
  const selectedMethod = 'cash'
  const selectedOption = null
  orderDetailModal.settling = true
}
</script>
<style scoped>.stock-toggle-row { display:flex }</style>
`

test('routes pay flows through background checkout and settlement APIs', () => {
  const out = transformPosBackgroundPage(fixture)
  assert.match(out, /enqueuePOSBackgroundCheckout/)
  assert.match(out, /enqueuePOSBackgroundSettlement/)
  assert.match(out, /getPOSBackgroundOperation/)
  assert.match(out, /trackPOSBackgroundJob/)
  assert.match(out, /if \(payNow\) \{/)
  assert.match(out, /return/)
})

test('removes stock availability controls from quick edit sidebar', () => {
  const out = transformPosBackgroundPage(fixture)
  assert.doesNotMatch(out, /stock-toggle-row/)
  assert.doesNotMatch(out, />موجودی</)
})

test('adds compact background job status UI', () => {
  const out = transformPosBackgroundPage(fixture)
  assert.match(out, /pos-background-jobs/)
  assert.match(out, /در صف/)
  assert.match(out, /انجام شد/)
})

test('product availability uses expiry-aware helper instead of raw flag', () => {
  const productFixture = `
<template>
  <button :disabled="Number(item.out_of_stock) === 1">add</button>
  <small v-if="Number(item.out_of_stock) === 1">ناموجود</small>
</template>
<script setup>
function quantityValue(slug) { return 0 }
</script>`
  const out = transformPosProductPanelAvailability(productFixture)
  assert.match(out, /function isProductUnavailableForDisplay/)
  assert.doesNotMatch(out, /Number\(item\.out_of_stock\) === 1/)
  assert.match(out, /out_of_stock_until/)
})
