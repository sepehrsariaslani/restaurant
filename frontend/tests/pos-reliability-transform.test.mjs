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

const uiFixture = `
<template>
<section class="pos-theme">
    <!-- Order Detail / Edit Modal -->
    <div v-if="orderDetailModal.open" class="od-modal-overlay" @click.self="closeOrderDetailModal"><div class="od-modal"></div></div>
    <OpenInvoiceSettlementModal :open="true" />
</section>
</template>
<script setup>
import { formatMoney } from '@/utils/format'
const isOffline = ref(typeof navigator !== 'undefined' ? !navigator.onLine : false)
async function loadPOSBoot() { const payload = await getManagementPOSBoot() }
function incrementProduct(item) {
  const itemSlug = getItemSlug(item)
  addToCart(item, 1)
}
async function lookupProductBarcode(raw) {
  const match = products.value[0]
  if (Number(match.out_of_stock || 0) === 1) { error.value = 'ناموجود'; return }
  addToCart(match, 1)
}
async function saveQuickEdit() {
  if (!quickEditForm.name) return
  quickEditSaving.value = true
  quickEditError.value = ''
  quickEditSuccess.value = ''
  try {
    await Promise.all([
      setManagementProductPrice({
        item_name: quickEditForm.name,
        price_list_rate: Number(quickEditForm.price || 0),
      }),
      updateManagementProductSettings({
        item_name: quickEditForm.name,
        restaurant_short_desc: quickEditForm.restaurant_short_desc,
        restaurant_long_desc: quickEditForm.restaurant_long_desc,
        item_group: quickEditForm.item_group,
        restaurant_out_of_stock: quickEditForm.out_of_stock ? 1 : 0,
        restaurant_out_of_stock_until: quickEditForm.out_of_stock ? quickEditForm.out_of_stock_until : '',
      }),
    ])
    quickEditSuccess.value = 'تغییرات ذخیره شد و محصولات به‌روز شد.'
    await loadPOSBoot()
  } catch (errObj) {}
}
</script>
<style scoped>
.ops-overlay-backdrop { position: fixed; inset: 0; z-index: 10000; }
.print-editor-backdrop { position: fixed; inset: 0; z-index: 60; }
.quick-edit-backdrop { position: fixed; inset: 0; z-index: 14000; }
.od-modal-overlay { position: fixed; inset: 0; z-index: 14500; }
.print-target-backdrop { position: fixed; inset: 0; z-index: 14600; }
</style>
`

test('stabilizes POS overlays and guards unavailable product sale paths', () => {
  const out = transformPosReliabilityPage(uiFixture)
  assert.match(out, /--pos-z-operations:\s*12000/)
  assert.match(out, /--pos-z-dialog:\s*13000/)
  assert.match(out, /--pos-z-nested:\s*14000/)
  assert.match(out, /--pos-z-detail:\s*15000/)
  assert.match(out, /<Teleport to="body">[\s\S]*orderDetailModal\.open/)
  assert.match(out, /isProductUnavailable/)
  assert.match(out, /فعلاً ناموجود است/)
  assert.match(out, /updatePOSProductAtomic/)
  assert.doesNotMatch(out, /await Promise\.all\(\[\s*setManagementProductPrice/s)
  assert.match(out, /ویرایش محصول نیاز به اتصال اینترنت دارد/)
})

test('makes quick edit online-only and atomic', () => {
  const quickEditFixture = `
<script setup>
import { formatMoney } from '@/utils/format'
const isOffline = ref(typeof navigator !== 'undefined' ? !navigator.onLine : false)
async function loadPOSBoot() { const payload = await getManagementPOSBoot() }
async function saveQuickEdit() {
  if (!quickEditForm.name) return
  quickEditSaving.value = true
  quickEditError.value = ''
  try {
    await Promise.all([
      setManagementProductPrice({ item_name: quickEditForm.name, price_list_rate: Number(quickEditForm.price || 0) }),
      updateManagementProductSettings({
        item_name: quickEditForm.name,
        restaurant_short_desc: quickEditForm.restaurant_short_desc,
        restaurant_long_desc: quickEditForm.restaurant_long_desc,
        item_group: quickEditForm.item_group,
        restaurant_out_of_stock: quickEditForm.out_of_stock ? 1 : 0,
        restaurant_out_of_stock_until: quickEditForm.out_of_stock ? quickEditForm.out_of_stock_until : '',
      }),
    ])
    quickEditSuccess.value = 'تغییرات ذخیره شد و محصولات به‌روز شد.'
    await loadPOSBoot()
  } catch (errObj) { quickEditError.value = errObj.message }
}
</script>`
  const out = transformPosReliabilityPage(quickEditFixture)
  assert.match(out, /ویرایش محصول نیاز به اتصال اینترنت دارد/)
  assert.match(out, /await updatePOSProductAtomic\(/)
  assert.doesNotMatch(out, /await Promise\.all\(\[\s*setManagementProductPrice/s)
})

test('teleports order detail and applies semantic overlay z-index scale', () => {
  const modalFixture = `
<template>
  <section class="pos-theme pos-fullpage"></section>
  <!-- Order Detail / Edit Modal -->
  <div v-if="orderDetailModal.open" class="od-modal-overlay" @click.self="closeOrderDetailModal">
    <div class="od-modal">detail</div>
  </div>
  <!-- Return Invoice Confirmation Modal -->
</template>
<script setup>
import { formatMoney } from '@/utils/format'
const isOffline = ref(typeof navigator !== 'undefined' ? !navigator.onLine : false)
async function loadPOSBoot() { const payload = await getManagementPOSBoot() }
</script>
<style scoped>
.ops-overlay-backdrop { z-index: 10000; }
.pos-modal-backdrop { z-index: 12500; }
.quick-edit-backdrop { z-index: 14000; }
.od-modal-overlay { position: fixed; inset: 0; z-index: 14500; }
.print-target-backdrop { z-index: 14600; }
</style>`
  const out = transformPosReliabilityPage(modalFixture)
  assert.match(out, /<!-- Order Detail \/ Edit Modal -->\s*<Teleport to="body">/s)
  assert.match(out, /<\/Teleport>\s*<!-- Return Invoice Confirmation Modal -->/s)
  assert.match(out, /--pos-z-operations:\s*12000/)
  assert.match(out, /--pos-z-dialog:\s*13000/)
  assert.match(out, /--pos-z-nested:\s*14000/)
  assert.match(out, /--pos-z-detail:\s*15000/)
  assert.match(out, /--pos-z-top:\s*16000/)
  assert.match(out, /z-index:\s*var\(--pos-z-detail(?:,\s*15000)?\)/)
})
