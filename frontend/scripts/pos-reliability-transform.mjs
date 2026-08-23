function injectBefore(source, marker, insertion) {
  if (!marker || source.includes(insertion.trim())) return source
  if (!source.includes(marker)) return source
  return source.replace(marker, `${insertion}\n${marker}`)
}

export function transformPosReliabilityPage(input) {
  let code = String(input || '')

  // Thermal paper containment is applied after the legacy print transform.
  code = code.replaceAll(
    '@page { margin: 0; }',
    '@page { margin: 0; }\n*, *::before, *::after { box-sizing: border-box; }',
  )
  code = code.replaceAll(
    'html, body { width: ${paperWidthMm}mm; max-width: ${paperWidthMm}mm; min-height: 0; margin: 0; padding: 0; overflow: visible; }',
    'html, body { width: ${paperWidthMm}mm; max-width: ${paperWidthMm}mm; min-height: 0; margin: 0; padding: 0; overflow-x: hidden; overflow-y: visible; }',
  )
  code = code.replaceAll(
    '.receipt { width: ${paperWidthMm}mm; max-width: ${paperWidthMm}mm; min-height: 0; margin: 0; padding: 2mm ${horizontalPaddingMm}mm 3mm; font-size: ${receiptFontSizePx()}px; line-height: 1.45; overflow: visible; }',
    '.receipt { width: ${paperWidthMm}mm; max-width: 100%; min-height: 0; margin: 0; padding: 2mm ${horizontalPaddingMm}mm 3mm; font-size: ${receiptFontSizePx()}px; line-height: 1.45; overflow: hidden; }\n.receipt table, .receipt img, .receipt svg { max-width: 100%; }\n.receipt td, .receipt th, .receipt span, .receipt p { min-width: 0; overflow-wrap: anywhere; word-break: break-word; }',
  )

  const isManagementPos = code.includes('async function loadPOSBoot()') && code.includes('const isOffline = ref(')
  if (!isManagementPos) return code

  const imports = `import { createOfflineOrderRecord, createPosOfflineStore } from '@/utils/posOfflineStore'
import { getReliablePOSBoot, replayOfflinePOSOrder, updatePOSProductAtomic } from '@/utils/posReliabilityApi'`
  code = injectBefore(code, "import { formatMoney", imports)

  const offlineState = "const isOffline = ref(typeof navigator !== 'undefined' ? !navigator.onLine : false)"
  code = code.replace(
    offlineState,
    `${offlineState}\nconst posOfflineStore = createPosOfflineStore()\nconst pendingOfflineOrderCount = ref(0)\nconst offlineSyncing = ref(false)`,
  )

  const offlineBanner = '<p class="offline-banner" v-if="isOffline">اینترنت قطع است.</p>'
  const syncPanel = `<div class="offline-banner" v-if="isOffline">اینترنت قطع است؛ اطلاعات ذخیره‌شده محلی در دسترس است.</div>
    <div v-if="pendingOfflineOrderCount || syncReminder" class="sync-banner pos-sync-banner">
      <span>{{ syncReminder || (pendingOfflineOrderCount + ' سفارش آفلاین در صف همگام‌سازی است.') }}</span>
      <button
        v-if="pendingOfflineOrderCount"
        type="button"
        class="secondary-btn pos-sync-btn"
        :disabled="isOffline || offlineSyncing"
        @click="syncPendingOfflineOrders"
      >{{ offlineSyncing ? 'در حال همگام‌سازی...' : 'همگام‌سازی' }}</button>
    </div>`
  if (code.includes(offlineBanner)) code = code.replace(offlineBanner, syncPanel)

  const reliabilityHelpers = `function isPOSNetworkError(error) {
  const message = String(error?.message || error || '').toLowerCase()
  return isOffline.value || /network|failed to fetch|fetch failed|load failed|connection|ارتباط|اینترنت/.test(message)
}

async function refreshPendingOfflineOrderCount() {
  pendingOfflineOrderCount.value = await posOfflineStore.pendingOrderCount()
  return pendingOfflineOrderCount.value
}

async function loadReliablePOSBootPayload() {
  let networkError = null
  if (!isOffline.value) {
    try {
      const payload = await getReliablePOSBoot()
      await posOfflineStore.savePosBootSnapshot('default', payload)
      return payload
    } catch (errorObj) {
      networkError = errorObj
    }
  }
  const cached = await posOfflineStore.loadPosBootSnapshot('default')
  if (cached?.payload) {
    const cachedAt = cached.updated_at ? new Date(cached.updated_at).toLocaleString('fa-IR') : ''
    syncReminder.value = cachedAt ? \`حالت آفلاین؛ اطلاعات ذخیره‌شده \${cachedAt} نمایش داده می‌شود.\` : 'حالت آفلاین؛ اطلاعات ذخیره‌شده نمایش داده می‌شود.'
    return cached.payload
  }
  if (networkError) throw networkError
  throw new Error('برای استفاده آفلاین، این دستگاه باید حداقل یک‌بار POS را آنلاین بارگذاری کند.')
}

async function syncPendingOfflineOrders() {
  if (offlineSyncing.value || isOffline.value) return
  offlineSyncing.value = true
  let syncedCount = 0
  try {
    const pending = await posOfflineStore.listPendingOfflineOrders()
    for (const record of pending) {
      try {
        await replayOfflinePOSOrder(record.payload)
        await posOfflineStore.markOfflineOrderSynced(record.id)
        syncedCount += 1
      } catch (errorObj) {
        if (isPOSNetworkError(errorObj)) {
          syncReminder.value = 'ارتباط با سرور قطع شد؛ سفارش‌های باقی‌مانده در صف می‌مانند.'
          break
        }
        await posOfflineStore.markOfflineOrderNeedsAttention(record.id, errorObj?.message || String(errorObj || ''))
      }
    }
    await refreshPendingOfflineOrderCount()
    if (syncedCount) {
      successMessage.value = \`\${syncedCount} سفارش آفلاین با سرور همگام شد.\`
      if (!pendingOfflineOrderCount.value) syncReminder.value = ''
      void loadPOSBoot()
      void loadCustomers('')
    }
  } finally {
    offlineSyncing.value = false
  }
}
`
  code = injectBefore(code, 'async function loadPOSBoot()', reliabilityHelpers)
  code = code.replace('const payload = await getManagementPOSBoot()', 'const payload = await loadReliablePOSBootPayload()')

  code = code.replace(
    "async function loadCustomers(search = '') {\n  try {",
    "async function loadCustomers(search = '') {\n  const cachedCustomers = await posOfflineStore.searchCachedCustomers(search, 50)\n  if (cachedCustomers.length || isOffline.value) customerOptions.value = cachedCustomers\n  if (isOffline.value) return\n  try {",
  )
  code = code.replace(
    '    if (search) {\n      // Merge results preserving existing',
    "    if (search) await posOfflineStore.mergeCustomerCache(mapped)\n    else await posOfflineStore.replaceCustomerCache(mapped)\n\n    if (search) {\n      // Merge results preserving existing",
  )

  code = code.replace(
    '  hydrateReceiptSettings()\n  await loadPOSBoot()',
    "  hydrateReceiptSettings()\n  customerOptions.value = await posOfflineStore.searchCachedCustomers('', 50)\n  await refreshPendingOfflineOrderCount()\n  await loadPOSBoot()\n  if (!isOffline.value) void loadCustomers('')",
  )

  code = code.replace(
    "    syncReminder.value = 'اینترنت وصل شد. لطفا اگر سفارشی آفلاین مانده، دکمه Sync را بزنید.'",
    "    syncReminder.value = 'اینترنت وصل شد؛ سفارش‌های آفلاین در حال بررسی برای همگام‌سازی هستند.'\n    void syncPendingOfflineOrders()",
  )

  code = code.replace(
    "async function submitPOSOrder(payNow = true, paymentMeta = {}, withProduction = false) {\n  if (!cart.length) {",
    "async function submitPOSOrder(payNow = true, paymentMeta = {}, withProduction = false) {\n  if (isOffline.value && payNow) {\n    error.value = 'پرداخت یا تسویه نیاز به اتصال اینترنت دارد.'\n    return\n  }\n  if (isOffline.value && editingOriginalOrder.isEditing) {\n    error.value = 'ویرایش یا جایگزینی فاکتور باز نیاز به اتصال اینترنت دارد.'\n    return\n  }\n  if (isOffline.value && form.order_mode === 'dine_in') {\n    error.value = 'ثبت آفلاین سفارش میز به دلیل احتمال تغییر وضعیت میز غیرفعال است؛ سفارش بیرون‌بر یا ارسال را می‌توانید آفلاین ذخیره کنید.'\n    return\n  }\n  if (!cart.length) {",
  )

  code = code.replace(
    '    payment: paymentPayload,\n  }\n\n  submitting.value = true',
    `    payment: paymentPayload,
  }

  if (isOffline.value) {
    const queued = await posOfflineStore.enqueueOfflineOrder(payload)
    if (!queued.persisted) {
      error.value = 'ذخیره آفلاین روی این دستگاه ممکن نیست؛ فضای ذخیره‌سازی مرورگر را بررسی کنید.'
      return
    }
    await refreshPendingOfflineOrderCount()
    successMessage.value = 'سفارش ذخیره آفلاین شد و پس از اتصال همگام می‌شود.'
    resetCurrentInvoiceState({ preserveFeedback: true })
    saveActiveTicketSnapshot()
    return
  }

  submitting.value = true`,
  )

  // Plain online orders also go through the idempotent endpoint.
  code = code.replace(
    '      result = await createPOSOrder(payload)',
    "      if (!payload.client_order_key) payload.client_order_key = createOfflineOrderRecord(payload).id\n      result = await replayOfflinePOSOrder(payload)",
  )

  if (code.includes('<style scoped>') && !code.includes('.pos-sync-banner {')) {
    code = code.replace(
      '<style scoped>',
      `<style scoped>
.pos-sync-banner { display: flex; align-items: center; justify-content: space-between; gap: 0.65rem; }
.pos-sync-btn { flex: 0 0 auto; }
@media (max-width: 720px) { .pos-sync-banner { align-items: stretch; flex-direction: column; } }`,
    )
  }

  return code
}
