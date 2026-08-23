import test from 'node:test'
import assert from 'node:assert/strict'
import { transformPosReliabilityPage } from '../scripts/pos-reliability-transform.mjs'

const fixture = `
<template>
  <section class="pos-theme pos-fullpage">
    <p class="offline-banner" v-if="isOffline">اینترنت قطع است.</p>
  </section>
</template>
<script setup>
import { formatMoney } from '@/utils/format'
const syncReminder = ref('')
const customerOptions = ref([])
const isOffline = ref(typeof navigator !== 'undefined' ? !navigator.onLine : false)
function updateNetworkState() {
  const wasOffline = isOffline.value
  isOffline.value = !navigator.onLine
  if (wasOffline && !isOffline.value) {
    syncReminder.value = 'اینترنت وصل شد. لطفا اگر سفارشی آفلاین مانده، دکمه Sync را بزنید.'
  }
}
async function loadPOSBoot() {
  try {
    const payload = await getManagementPOSBoot()
    products.value = payload.items || []
  } catch (err) { error.value = err.message }
}
async function loadCustomers(search = '') {
  try {
    const payload = await listManagementCustomers({ search })
    const customers = payload?.customers || []
    const mapped = customers.map(c => ({ key: c.name, label: c.customer_name, mobile: c.mobile || '' }))
    if (search) {
      // Merge results preserving existing
      customerOptions.value = mapped
    } else {
      customerOptions.value = mapped
    }
  } catch (err) {
    console.error('Failed to load customers:', err)
  }
}
onMounted(async () => {
  hydrateReceiptSettings()
  await loadPOSBoot()
})
async function submitPOSOrder(payNow = true, paymentMeta = {}, withProduction = false) {
  if (!cart.length) {
    error.value = 'حداقل یک محصول به سبد اضافه کنید.'
    return
  }
  const payload = {
    customer_name: form.customer_name || 'مشتری POS',
    items: [],
    payment: paymentPayload,
  }

  submitting.value = true
  error.value = ''
}
</script>
`

test('injects offline boot/customer cache and idempotent order queue integration', () => {
  const out = transformPosReliabilityPage(fixture)
  assert.match(out, /createPosOfflineStore/)
  assert.match(out, /getReliablePOSBoot/)
  assert.match(out, /loadPosBootSnapshot/)
  assert.match(out, /savePosBootSnapshot/)
  assert.match(out, /searchCachedCustomers/)
  assert.match(out, /mergeCustomerCache/)
  assert.match(out, /pendingOfflineOrderCount/)
  assert.match(out, /syncPendingOfflineOrders/)
  assert.match(out, /replayOfflinePOSOrder/)
  assert.match(out, /ذخیره آفلاین شد/)
  assert.match(out, /پرداخت یا تسویه نیاز به اتصال اینترنت دارد/)
  assert.match(out, /queued\.persisted/)
})

test('keeps a visible manual sync action when queued orders exist', () => {
  const out = transformPosReliabilityPage(fixture)
  assert.match(out, /pendingOfflineOrderCount/)
  assert.match(out, /@click="syncPendingOfflineOrders"/)
  assert.match(out, /همگام/)
})
