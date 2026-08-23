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

  const unavailableHelper = `function isProductUnavailable(item) {
  const flag = Number(item?.out_of_stock ?? item?.restaurant_out_of_stock ?? 0) === 1
  if (!flag) return false
  const until = String(item?.out_of_stock_until || item?.restaurant_out_of_stock_until || '').trim()
  if (!until) return true
  const end = new Date(\`${until}T23:59:59\`)
  if (!Number.isFinite(end.getTime())) return true
  return end.getTime() >= Date.now()
}
`
  code = injectBefore(code, 'function incrementProduct(item)', unavailableHelper)
  code = code.replace(
    'function incrementProduct(item) {\n  const itemSlug = getItemSlug(item)',
    "function incrementProduct(item) {\n  if (isProductUnavailable(item)) {\n    error.value = `«${item?.title || item?.item_name || item?.name || 'محصول'}» فعلاً ناموجود است.`\n    return\n  }\n  const itemSlug = getItemSlug(item)",
  )
  code = code.replaceAll(
    'if (Number(match.out_of_stock || 0) === 1) {',
    'if (isProductUnavailable(match)) {',
  )

  code = code.replace(
    'async function saveQuickEdit() {\n  if (!quickEditForm.name) {',
    "async function saveQuickEdit() {\n  if (isOffline.value) {\n    quickEditError.value = 'ویرایش محصول نیاز به اتصال اینترنت دارد.'\n    return\n  }\n  if (!quickEditForm.name) {",
  )
  code = code.replace(
    'async function saveQuickEdit() {\n  if (!quickEditForm.name) return',
    "async function saveQuickEdit() {\n  if (isOffline.value) {\n    quickEditError.value = 'ویرایش محصول نیاز به اتصال اینترنت دارد.'\n    return\n  }\n  if (!quickEditForm.name) return",
  )

  const legacyQuickEdit = `    await Promise.all([
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
    ])`
  const atomicQuickEdit = `    await updatePOSProductAtomic({
      item_name: quickEditForm.name,
      price_list_rate: Number(quickEditForm.price || 0),
      restaurant_short_desc: quickEditForm.restaurant_short_desc,
      restaurant_long_desc: quickEditForm.restaurant_long_desc,
      item_group: quickEditForm.item_group,
      restaurant_out_of_stock: quickEditForm.out_of_stock ? 1 : 0,
      restaurant_out_of_stock_until: quickEditForm.out_of_stock ? quickEditForm.out_of_stock_until : '',
    })`
  code = code.replace(legacyQuickEdit, atomicQuickEdit)
  if (code.includes('await Promise.all([') && code.includes('setManagementProductPrice(') && code.includes('updateManagementProductSettings(')) {
    code = code.replace(
      /    await Promise\.all\(\[\s*setManagementProductPrice\(\{[\s\S]*?\}\),\s*updateManagementProductSettings\(\{[\s\S]*?\}\),?\s*\]\)/,
      atomicQuickEdit,
    )
  }

  const orderDetailOpenPattern = /(\n[ \t]*<!-- Order Detail \/ Edit Modal -->\s*\n)([ \t]*)<div v-if="orderDetailModal\.open" class="od-modal-overlay" @click\.self="closeOrderDetailModal">/
  if (!/<!-- Order Detail \/ Edit Modal -->\s*<Teleport to="body">/.test(code) && orderDetailOpenPattern.test(code)) {
    code = code.replace(
      orderDetailOpenPattern,
      (_, commentLine, indent) => `${commentLine}${indent}<Teleport to="body">\n${indent}<div v-if="orderDetailModal.open" class="od-modal-overlay" @click.self="closeOrderDetailModal">`,
    )
    const closePattern = /(\n)([ \t]*)(<OpenInvoiceSettlementModal|<!-- Return Invoice Confirmation Modal -->)/
    if (closePattern.test(code)) {
      code = code.replace(
        closePattern,
        (_, newline, indent, marker) => `${newline}${indent}</Teleport>\n\n${indent}${marker}`,
      )
    }
  }

  const zIndexVars = `:global(:root) {
  --pos-z-floating: 11000;
  --pos-z-operations: 12000;
  --pos-z-dialog: 13000;
  --pos-z-nested: 14000;
  --pos-z-detail: 15000;
  --pos-z-top: 16000;
}`
  if (code.includes('<style scoped>') && !code.includes('--pos-z-operations:')) {
    code = code.replace('<style scoped>', `<style scoped>\n${zIndexVars}`)
  }
  code = code.replaceAll('z-index: 10000;', 'z-index: var(--pos-z-operations, 12000);')
  code = code.replaceAll('z-index: 12500;', 'z-index: var(--pos-z-dialog, 13000);')
  code = code.replaceAll('z-index: 14000;', 'z-index: var(--pos-z-nested, 14000);')
  code = code.replaceAll('z-index: 14500;', 'z-index: var(--pos-z-detail, 15000);')
  code = code.replaceAll('z-index: 14600;', 'z-index: var(--pos-z-top, 16000);')
  code = code.replace(
    '.print-editor-backdrop {\n  position: fixed;\n  inset: 0;\n  z-index: 60;',
    '.print-editor-backdrop {\n  position: fixed;\n  inset: 0;\n  z-index: var(--pos-z-top, 16000);',
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

export function transformPosProductPanel(input) {
  let code = String(input || '')

  code = code.replaceAll(
    `:class="{ 'has-qty': quantityValue(item.slug) > 0 }"`,
    `:class="{ 'has-qty': quantityValue(item.slug) > 0, 'out-of-stock': Number(item.out_of_stock) === 1 }"`,
  )

  code = code.replaceAll(
    `class="compact-main-btn"\n\t\t\t\t\t\t@click="$emit('increment-product', item)"`,
    `class="compact-main-btn"\n\t\t\t\t\t\t:disabled="Number(item.out_of_stock) === 1"\n\t\t\t\t\t\t@click="$emit('increment-product', item)"`,
  )
  code = code.replaceAll(
    `class="compact-action-btn compact-action-btn--primary"\n\t\t\t\t\t\t\ttitle=`,
    `class="compact-action-btn compact-action-btn--primary"\n\t\t\t\t\t\t\t:disabled="Number(item.out_of_stock) === 1"\n\t\t\t\t\t\t\ttitle=`,
  )

  // Formatting-tolerant fallbacks for future template cleanup.
  code = code.replace(
    /class="compact-main-btn"(?![^>]*:disabled=)/g,
    'class="compact-main-btn" :disabled="Number(item.out_of_stock) === 1"',
  )
  code = code.replace(
    /class="compact-action-btn compact-action-btn--primary"(?![^>]*:disabled=)/g,
    'class="compact-action-btn compact-action-btn--primary" :disabled="Number(item.out_of_stock) === 1"',
  )

  if (!code.includes('compact-oos-badge')) {
    code = code.replaceAll(
      `<span class="compact-name">{{ item.title || item.name }}</span>`,
      `<span class="compact-name">{{ item.title || item.name }}</span>\n\t\t\t\t\t\t<span v-if="Number(item.out_of_stock) === 1" class="compact-oos-badge">ناموجود</span>`,
    )
  }

  if (code.includes('<style scoped>') && !code.includes('.compact-card.out-of-stock')) {
    code = code.replace(
      '<style scoped>',
      `<style scoped>\n.compact-card.out-of-stock { opacity: 0.68; }\n.compact-card.out-of-stock .compact-main-btn,\n.compact-card.out-of-stock .compact-action-btn--primary { cursor: not-allowed; }\n.compact-oos-badge { font-size: 0.7rem; font-weight: 800; color: var(--mg-danger); }`,
    )
  }

  return code
}
