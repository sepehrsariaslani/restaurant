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
  assert.match(out, /createOfflineSyncEngine/)
  assert.match(out, /getReliablePOSBoot/)
  assert.match(out, /loadPosBootSnapshot/)
  assert.match(out, /savePosBootSnapshot/)
  assert.match(out, /searchCachedCustomers/)
  assert.match(out, /mergeCustomerCache/)
  assert.match(out, /pendingOfflineOrderCount/)
  assert.match(out, /needsAttentionOfflineOrderCount/)
  assert.match(out, /syncPendingOfflineOrders/)
  assert.match(out, /replayOfflinePOSOrder/)
  assert.match(out, /ذخیره آفلاین شد/)
  assert.match(out, /پرداخت دستی به‌صورت موقت ذخیره شد/)
  assert.match(out, /queued\.persisted/)
  assert.match(out, /syncEngine\.syncPendingMutations\(\)/)
  assert.match(out, /savePOSOfflineContext/)
  assert.match(out, /getCachedPOSOrders/)
  assert.match(out, /getCachedPOSTables/)
  assert.match(out, /getCachedPOSWaiters/)
})

test('keeps a visible manual sync action when queued orders exist', () => {
  const out = transformPosReliabilityPage(fixture)
  assert.match(out, /pendingOfflineOrderCount/)
  assert.match(out, /needsAttentionOfflineOrderCount/)
  assert.match(out, /@click="syncPendingOfflineOrders"/)
  assert.match(out, /همگام/)
})

test('uses cached POS context for invoices, history, recent orders, tables and waiters while offline', () => {
  const contextFixture = `
<script setup>
const isOffline = ref(false)
async function loadPOSBoot() {}
async function loadOpenInvoices() {
  const payload = await listManagementOrders({ source: 'web' })
  openInvoices.value = payload?.orders || []
}
async function loadTodayTransactions() {
  const payload = await listManagementOrders({ source: 'web' })
  todayTransactions.value = payload?.orders || []
}
async function loadRecentOrders() {
  const payload = await listManagementOrders({ source: 'web' })
  recentOrders.value = payload?.orders || []
}
async function loadWaitersOnce() {
  if (waiterOptions.value.length || waiterبارگذاری.value) return
  const payload = await listManagementUsers({ search: '' })
  waiterOptions.value = payload?.users || []
}
</script>`
  const out = transformPosReliabilityPage(contextFixture)
  assert.match(out, /isOffline\.value \? \{ orders: await getCachedPOSOrders\(\) \} : await listManagementOrders/g)
  assert.match(out, /if \(isOffline\.value\) \{\s*waiterOptions\.value = await getCachedPOSWaiters\(\)/s)
})

test('does not log expected customer fetch failures during a network transition', () => {
  const customerFixture = `
<script setup>
const isOffline = ref(false)
async function loadPOSBoot() {}
async function loadCustomers(search = '') {
  try { await listManagementCustomers({ search }) }
  catch (err) { console.error('Failed to load customers:', err) }
}
</script>`
  const out = transformPosReliabilityPage(customerFixture)
  assert.match(out, /if \(!isPOSNetworkError\(err\)\) console\.error\('Failed to load customers:'/)
})

test('queues table actions instead of losing them offline', () => {
  const tableFixture = `
<script setup>
import { formatMoney } from '@/utils/format'
const isOffline = ref(typeof navigator !== 'undefined' ? !navigator.onLine : false)
async function loadPOSBoot() {}
async function changeTableOrderItemQty(order, item, delta) {
  try {
    await updateTableOrderItem({ order_name: order.name, row_name: item.row_name, quantity_delta: delta })
  } catch (updateErr) {}
}
async function assignCustomerToSelectedTable() {
  try {
    await assignTableSessionCustomer({ table_name: selectedTable.name, customer_name: form.customer_name || '' })
  } catch (assignErr) {}
}
async function clearTableSession(table) {
  const activeSession = table.active_session
  try {
    await closeTableSession(activeSession)
  } catch (closeErr) {}
}
async function moveSelectedTableSession() {
  try {
    await moveTableSession({ session_name: selectedTablePreview.value.session.name, target_table: moveTableTarget.value })
  } catch (moveErr) {}
}
async function mergeSelectedTableSession() {
  try {
    await mergeTableSessions({ source_session: selectedTablePreview.value.session.name, target_table: mergeTableTarget.value })
  } catch (mergeErr) {}
}
async function submitPOSOrder(payNow = true, paymentMeta = {}, withProduction = false) {
  if (!cart.length) return
  const payload = { items: [], payment: paymentPayload }
  submitting.value = true
}
</script>`
  const out = transformPosReliabilityPage(tableFixture)
  assert.match(out, /replayOfflinePOSMutation/)
  assert.match(out, /enqueuePOSOfflineMutation/)
  assert.match(out, /'table_update_item'/)
  assert.match(out, /'table_assign_customer'/)
  assert.match(out, /'table_close'/)
  assert.match(out, /'table_move'/)
  assert.match(out, /'table_merge'/)
  assert.match(out, /syncEngine\.syncPendingMutations\(\)/)
})

test('uses cached invoice details and queues invoice edit and provisional settlement offline', () => {
  const invoiceFixture = `
<script setup>
import { formatMoney } from '@/utils/format'
const isOffline = ref(typeof navigator !== 'undefined' ? !navigator.onLine : false)
async function loadPOSBoot() {}
async function openOrderDetailModal(tx) {
  const orderName = String(tx.name || '').trim()
  const payload = await getManagementOrderDetail(orderName)
  orderDetailModal.order = payload?.order || null
}
async function saveOrderDetailEdit() {
  try {
    await updateManagementOrder({ order_name: orderDetailModal.order.name, note: orderDetailModal.editForm.note })
  } catch (err) {}
}
async function confirmSettleOrder() {
  try {
    const result = await settlePOSOrder(orderDetailModal.order.name, { method: 'cash' })
  } catch (err) {}
}
</script>`
  const out = transformPosReliabilityPage(invoiceFixture)
  assert.match(out, /invoice_detail:/)
  assert.match(out, /'invoice_edit'/)
  assert.match(out, /'invoice_settlement_claim'/)
})

test('preloads today invoice details for offline access', () => {
  const fixture = `
<script setup>
const isOffline = ref(false)
async function loadPOSBoot() {}
async function loadOpenInvoices() {
  const selectedDate = String(openInvoicesDate.value || '').trim()
  const orderPayload = await listManagementOrders({ date_from: selectedDate, date_to: selectedDate })
  const allOrders = orderPayload?.orders || []
  setOpenInvoices(allOrders, true)
}
</script>`
  const out = transformPosReliabilityPage(fixture)
  assert.match(out, /cacheTodayInvoiceDetails/)
  assert.match(out, /slice\(0, 200\)/)
})

test('queues every open-invoice settlement path as a provisional claim offline', () => {
  const settlementFixture = `
<script setup>
import { formatMoney } from '@/utils/format'
const isOffline = ref(typeof navigator !== 'undefined' ? !navigator.onLine : false)
async function loadPOSBoot() {}
async function settleSelectedOpenInvoice() {
  try { await markManagementOrderPaid({ order_name: selectedOpenInvoice.value.name }) } catch (err) {}
}
async function settleSelectedInvoice(invoice, paymentSelection = {}) {
  try { const result = await markManagementOrderPaid({ order_name: invoice.name }) } catch (err) {}
}
async function settleAndDeliverFromInvoice(invoice, paymentSelection = {}) {
  try { const payResult = await markManagementOrderPaid({ order_name: invoice.name }) } catch (err) {}
}
</script>`
  const out = transformPosReliabilityPage(settlementFixture)
  assert.match(out, /queueProvisionalInvoiceSettlement/)
  assert.match(out, /'invoice_settlement_claim'/)
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
