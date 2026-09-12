function injectBefore(source, marker, insertion) {
  if (!marker || source.includes(insertion.trim())) return source
  if (!source.includes(marker)) return source
  return source.replace(marker, `${insertion}\n${marker}`)
}

export function transformPosReliabilityPage(input) {
  let code = String(input || '')

  // Thermal paper containment is applied after the legacy print transform.
  code = code.replaceAll(
    '@page { size: ${paperWidthMm}mm auto; margin: 0 !important; }',
    '@page { size: ${paperWidthMm}mm auto; margin: 0 !important; }\n*, *::before, *::after { box-sizing: border-box; }',
  )
  code = code.replaceAll(
    'html, body { width: ${paperWidthMm}mm; max-width: ${paperWidthMm}mm; min-height: 0; margin: 0 !important; padding: 0 !important; overflow: visible; }',
    'html, body { width: ${paperWidthMm}mm; max-width: ${paperWidthMm}mm; min-height: 0; margin: 0 !important; padding: 0 !important; overflow-x: hidden; overflow-y: visible; }',
  )
  code = code.replaceAll(
    '.receipt { width: ${paperWidthMm}mm; max-width: ${paperWidthMm}mm; min-height: 0; margin: 0 !important; padding: 2mm ${horizontalPaddingMm}mm 3mm; font-size: ${receiptFontSizePx()}px; line-height: 1.45; overflow: visible; }',
    '.receipt { width: ${paperWidthMm}mm; max-width: 100%; min-height: 0; margin: 0 !important; padding: 2mm ${horizontalPaddingMm}mm 3mm; font-size: ${receiptFontSizePx()}px; line-height: 1.45; overflow: hidden; }\n.receipt table, .receipt img, .receipt svg { max-width: 100%; }\n.receipt td, .receipt th, .receipt span, .receipt p { min-width: 0; overflow-wrap: anywhere; word-break: break-word; }',
  )

  const isManagementPos = code.includes('async function loadPOSBoot()') && code.includes('const isOffline = ref(')
  if (!isManagementPos) return code

  const imports = `import { createOfflineOrderRecord, createPosOfflineStore } from '@/utils/posOfflineStore'
import { createOfflineSyncEngine } from '@/utils/offlineSyncEngine'
import { getReliablePOSBoot, replayOfflinePOSOrder, replayOfflinePOSMutation, updatePOSProductAtomic } from '@/utils/posReliabilityApi'`
  code = injectBefore(code, "import { formatMoney", imports)

  const offlineState = "const isOffline = ref(typeof navigator !== 'undefined' ? !navigator.onLine : false)"
  code = code.replace(
    offlineState,
    `${offlineState}\nconst posOfflineStore = createPosOfflineStore()\nconst pendingOfflineOrderCount = ref(0)\nconst needsAttentionOfflineOrderCount = ref(0)\nconst offlineSyncing = ref(false)\nconst pendingOfflineMutationCount = ref(0)\nconst needsAttentionOfflineMutationCount = ref(0)`,
  )

  const offlineBanner = '<p class="offline-banner" v-if="isOffline">اینترنت قطع است.</p>'
  const syncPanel = `<div class="offline-banner" v-if="isOffline">اینترنت قطع است؛ اطلاعات ذخیره‌شده محلی در دسترس است.</div>`
  if (code.includes(offlineBanner)) code = code.replace(offlineBanner, syncPanel)

  const reliabilityHelpers = `function isPOSNetworkError(error) {
  const message = String(error?.message || error || '').toLowerCase()
  return isOffline.value || /network|failed to fetch|fetch failed|load failed|connection|ارتباط|اینترنت/.test(message)
}

async function refreshPendingOfflineOrderCount() {
  pendingOfflineOrderCount.value = await posOfflineStore.pendingOrderCount()
  needsAttentionOfflineOrderCount.value = await posOfflineStore.needsAttentionOrderCount()
  pendingOfflineMutationCount.value = await posOfflineStore.pendingMutationCount()
  needsAttentionOfflineMutationCount.value = await posOfflineStore.needsAttentionMutationCount()
  return pendingOfflineOrderCount.value
}

async function enqueuePOSOfflineMutation(type, payload, message = 'عملیات آفلاین ذخیره شد و پس از اتصال همگام می‌شود.') {
  const queued = await posOfflineStore.enqueueOfflineMutation(type, payload)
  if (!queued.persisted) {
    error.value = 'ذخیره آفلاین روی این دستگاه ممکن نیست؛ فضای ذخیره‌سازی مرورگر را بررسی کنید.'
    return false
  }
  await refreshPendingOfflineOrderCount()
  successMessage.value = message
  return true
}

async function queueProvisionalInvoiceSettlement(invoice, paymentData = {}, message = 'تسویه فاکتور به‌صورت موقت ذخیره شد و پس از اتصال خودکار نهایی می‌شود.') {
  const orderName = String(invoice?.name || invoice?.order_name || '').trim()
  if (!orderName) {
    error.value = 'شناسه فاکتور برای تسویه موقت معتبر نیست.'
    return false
  }
  return enqueuePOSOfflineMutation('invoice_settlement_claim', {
    order_name: orderName,
    payment_method: paymentData.method || payment.method || 'cash',
    mode_of_payment: paymentData.mode_of_payment || '',
    reference_no: paymentData.reference_no || payment.reference_no || '',
    rrn: paymentData.rrn || payment.rrn || '',
    deliver_after: paymentData.deliver_after ? 1 : 0,
  }, message)
}

const syncEngine = createOfflineSyncEngine({
  store: posOfflineStore,
  replayOrder: replayOfflinePOSOrder,
  replayMutation: replayOfflinePOSMutation,
  isOnline: () => !isOffline.value,
  isBusinessError: (errorObj) => !isPOSNetworkError(errorObj),
})

async function readPOSOfflineContext() {
  const snapshot = await posOfflineStore.loadPosBootSnapshot('pos_context')
  return snapshot?.payload && typeof snapshot.payload === 'object' ? snapshot.payload : {}
}

async function savePOSOfflineContext(patch = {}) {
  const current = await readPOSOfflineContext()
  return posOfflineStore.savePosBootSnapshot('pos_context', { ...current, ...patch })
}

async function getCachedPOSOrders() {
  const context = await readPOSOfflineContext()
  return Array.isArray(context.orders) ? context.orders : []
}

async function getCachedPOSTables() {
  const context = await readPOSOfflineContext()
  return Array.isArray(context.tables) ? context.tables : []
}

async function getCachedPOSWaiters() {
  const context = await readPOSOfflineContext()
  return Array.isArray(context.waiters) ? context.waiters : []
}

async function getCachedPOSHardware() {
  const context = await readPOSOfflineContext()
  return context.hardware && typeof context.hardware === 'object' ? context.hardware : null
}

async function getCachedInvoiceDetail(orderName) {
  const snapshot = await posOfflineStore.loadPosBootSnapshot(\`invoice_detail:\${String(orderName || '').trim()}\`)
  return snapshot?.payload || null
}

async function cacheInvoiceDetail(orderName, payload) {
  const key = String(orderName || payload?.order?.name || '').trim()
  if (key && payload) await posOfflineStore.savePosBootSnapshot(\`invoice_detail:\${key}\`, payload)
  return payload
}

async function cacheTodayInvoiceDetails(rows) {
  if (isOffline.value) return
  const invoices = Array.isArray(rows) ? rows.slice(0, 200) : []
  let cursor = 0
  const worker = async () => {
    while (cursor < invoices.length && !isOffline.value) {
      const invoice = invoices[cursor++]
      const orderName = String(invoice?.name || '').trim()
      if (!orderName) continue
      try {
        const cached = await getCachedInvoiceDetail(orderName)
        if (!cached) await cacheInvoiceDetail(orderName, await getManagementOrderDetail(orderName, invoice.source || 'web'))
      } catch (_) {}
    }
  }
  await Promise.all(Array.from({ length: Math.min(4, invoices.length) }, worker))
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
  try {
    const result = await syncEngine.syncPendingMutations()
    await refreshPendingOfflineOrderCount()
    if (result.synced) {
      successMessage.value = \`\${result.synced} سفارش آفلاین با سرور همگام شد.\`
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
    'async function settleSelectedOpenInvoice() {\n',
    `async function settleSelectedOpenInvoice() {
  if (isOffline.value) {
    await queueProvisionalInvoiceSettlement(selectedOpenInvoice.value, { method: payment.method, reference_no: payment.reference_no, rrn: payment.rrn })
    return
  }
`,
  )
  code = code.replace(
    'async function settleSelectedInvoice(invoice, paymentSelection = {}) {\n',
    `async function settleSelectedInvoice(invoice, paymentSelection = {}) {
  if (isOffline.value) {
    await queueProvisionalInvoiceSettlement(invoice, paymentSelection)
    return
  }
`,
  )
  code = code.replace(
    'async function settleAndDeliverFromInvoice(invoice, paymentSelection = {}) {\n',
    `async function settleAndDeliverFromInvoice(invoice, paymentSelection = {}) {
  if (isOffline.value) {
    await queueProvisionalInvoiceSettlement(invoice, { ...paymentSelection, deliver_after: true }, 'تسویه و تحویل به‌صورت موقت ذخیره شد و پس از اتصال خودکار نهایی می‌شود.')
    return
  }
`,
  )
  code = code.replace(
    'const payload = await getManagementOrderDetail(orderName)',
    "const payload = isOffline.value ? await getCachedInvoiceDetail(orderName) : await cacheInvoiceDetail(orderName, await getManagementOrderDetail(orderName))",
  )
  code = code.replace(
    '  try {\n    await updateManagementOrder({',
    `  if (isOffline.value) {
    await enqueuePOSOfflineMutation('invoice_edit', {
      order_name: orderDetailModal.order.name,
      payment_method: orderDetailModal.editForm.payment_method || '',
      note: orderDetailModal.editForm.note || '',
      customer_name: orderDetailModal.editForm.customer_name || '',
      secondary_customer: orderDetailModal.editForm.secondary_customer || '',
    }, 'ویرایش فاکتور آفلاین ذخیره شد و پس از اتصال بررسی می‌شود.')
    return
  }
  try {
    await updateManagementOrder({`,
  )
  code = code.replace(
    '  try {\n    const result = await settlePOSOrder(orderDetailModal.order.name, {',
    `  if (isOffline.value) {
    await enqueuePOSOfflineMutation('invoice_settlement_claim', {
      order_name: orderDetailModal.order.name,
      payment_method: selectedMethod,
      reference_no: orderDetailModal.settleReference || payment.reference_no || '',
      rrn: payment.rrn || '',
    }, 'تسویه فاکتور به‌صورت موقت ذخیره شد و پس از اتصال خودکار نهایی می‌شود.')
    return
  }
  try {
    const result = await settlePOSOrder(orderDetailModal.order.name, {`,
  )

  code = code.replace(
    'const orderPayload = await listManagementOrders({',
    'const orderPayload = isOffline.value ? { orders: await getCachedPOSOrders() } : await listManagementOrders({',
  )
  code = code.replaceAll(
    'const payload = await listManagementOrders({',
    'const payload = isOffline.value ? { orders: await getCachedPOSOrders() } : await listManagementOrders({',
  )
  code = code.replace(
    'const orderPayload = isOffline.value ? { orders: await getCachedPOSOrders() } : await listManagementOrders({',
    "const orderPayload = isOffline.value ? { orders: await posOfflineStore.loadDailyInvoiceSnapshots(String(openInvoicesDate.value || '').trim()) } : await listManagementOrders({",
  )
  code = code.replace(
    'const allOrders = orderPayload?.orders || []\n    setOpenInvoices(allOrders, preserveSelection)',
    "const allOrders = orderPayload?.orders || []\n    if (!isOffline.value) {\n      await posOfflineStore.saveDailyInvoiceSnapshots(String(openInvoicesDate.value || '').trim(), allOrders)\n      void cacheTodayInvoiceDetails(allOrders)\n    }\n    setOpenInvoices(allOrders, preserveSelection)",
  )
  code = code.replace(
    'const allOrders = orderPayload?.orders || []\n  setOpenInvoices(allOrders, true)',
    "const allOrders = orderPayload?.orders || []\n  if (!isOffline.value) {\n    await posOfflineStore.saveDailyInvoiceSnapshots(selectedDate, allOrders)\n    void cacheTodayInvoiceDetails(allOrders)\n  }\n  setOpenInvoices(allOrders, true)",
  )
  code = code.replace(
    'const allOrders = orderPayload?.orders || []\n      setOpenInvoices(allOrders, true)',
    'const allOrders = orderPayload?.orders || []\n      if (!isOffline.value) void savePOSOfflineContext({ orders: allOrders })\n      setOpenInvoices(allOrders, true)',
  )
  code = code.replace(
    'const tablePayload = await getTableOverview()',
    'const tablePayload = isOffline.value ? { tables: await getCachedPOSTables() } : await getTableOverview()',
  )
  code = code.replace(
    'tableOptions.value = buildDineInTableOptions(tablePayload?.tables || [])',
    'tableOptions.value = buildDineInTableOptions(tablePayload?.tables || [])\n      if (!isOffline.value) void savePOSOfflineContext({ tables: tablePayload?.tables || [] })',
  )
  code = code.replace(
    'async function loadWaitersOnce() {\n  if (waiterOptions.value.length || waiterبارگذاری.value) return',
    "async function loadWaitersOnce() {\n  if (waiterOptions.value.length || waiterبارگذاری.value) return\n  if (isOffline.value) {\n    waiterOptions.value = await getCachedPOSWaiters()\n    return\n  }",
  )
  code = code.replace(
    "      }))\n  } catch (errObj) {\n    waiterOptions.value = []",
    "      }))\n    void savePOSOfflineContext({ waiters: waiterOptions.value })\n  } catch (errObj) {\n    waiterOptions.value = []",
  )
  code = code.replace(
    'async function refreshHardwareStatus() {\n  hardwareبارگذاری.value = true',
    "async function refreshHardwareStatus() {\n  if (isOffline.value) {\n    const cached = await getCachedPOSHardware()\n    if (cached) Object.assign(hardwareStatus, cached)\n    return\n  }\n  hardwareبارگذاری.value = true",
  )
  code = code.replace(
    "    hardwareStatus.latency_ms = Number(payload.latency_ms || 0)",
    "    hardwareStatus.latency_ms = Number(payload.latency_ms || 0)\n    void savePOSOfflineContext({ hardware: { ...hardwareStatus } })",
  )
  code = code.replace(
    '    if (search) {\n      // Merge results preserving existing',
    "    if (search) await posOfflineStore.mergeCustomerCache(mapped)\n    else await posOfflineStore.replaceCustomerCache(mapped)\n\n    if (search) {\n      // Merge results preserving existing",
  )
  code = code.replaceAll(
    "console.error('Failed to load customers:', err)",
    "if (!isPOSNetworkError(err)) console.error('Failed to load customers:', err)",
  )

  code = code.replace(
    '  hydrateReceiptSettings()\n  await loadPOSBoot()',
    "  hydrateReceiptSettings()\n  customerOptions.value = await posOfflineStore.searchCachedCustomers('', 50)\n  await refreshPendingOfflineOrderCount()\n  await loadPOSBoot()\n  if (!isOffline.value) {\n    void loadCustomers('')\n    void syncPendingOfflineOrders()\n  }",
  )

  code = code.replace(
    "    syncReminder.value = 'اینترنت وصل شد. لطفا اگر سفارشی آفلاین مانده، دکمه Sync را بزنید.'",
    "    void syncPendingOfflineOrders()",
  )

  code = code.replaceAll('syncEngine.syncPendingOrders()', 'syncEngine.syncPendingMutations()')
  code = code.replaceAll('سفارش آفلاین با سرور همگام شد.', 'عملیات آفلاین با سرور همگام شد.')
  code = code.replaceAll('سفارش‌های باقی‌مانده در صف می‌مانند.', 'عملیات باقی‌مانده در صف می‌مانند.')
  code = code.replaceAll('سفارش نیازمند بررسی است.', 'عملیات نیازمند بررسی است.')
  code = code.replaceAll('if (!pendingOfflineOrderCount.value) syncReminder.value = \'\'', 'if (!pendingOfflineOrderCount.value && !pendingOfflineMutationCount.value) syncReminder.value = \'\'')

  code = code.replace(
    '  try {\n    await updateTableOrderItem({',
    `  if (isOffline.value) {
    await enqueuePOSOfflineMutation('table_update_item', {
      order_name: order.name,
      row_name: item.row_name,
      quantity_delta: qtyDelta,
    }, 'ویرایش آیتم میز آفلاین ذخیره شد و پس از اتصال بررسی می‌شود.')
    return
  }
  try {
    await updateTableOrderItem({`,
  )
  code = code.replace(
    '  try {\n    await assignTableSessionCustomer({',
    `  if (isOffline.value) {
    await enqueuePOSOfflineMutation('table_assign_customer', {
      table_name: selectedTable.name,
      customer_name: form.customer_name || '',
      mobile: form.mobile || '',
      customer_type: form.customer_type || '',
      guest_count: form.guest_count || 1,
    }, 'ثبت مشتری روی میز آفلاین ذخیره شد و پس از اتصال بررسی می‌شود.')
    return
  }
  try {
    await assignTableSessionCustomer({`,
  )
  code = code.replace(
    '  try {\n    await closeTableSession(activeSession)',
    `  if (isOffline.value) {
    await enqueuePOSOfflineMutation('table_close', { session_name: activeSession }, 'بستن میز آفلاین ذخیره شد و پس از اتصال بررسی می‌شود.')
    return
  }
  try {
    await closeTableSession(activeSession)`,
  )
  code = code.replace(
    '  try {\n    await moveTableSession({',
    `  if (isOffline.value) {
    await enqueuePOSOfflineMutation('table_move', {
      session_name: selectedTablePreview.value.session.name,
      target_table: moveTableTarget.value,
    }, 'انتقال میز آفلاین ذخیره شد و پس از اتصال بررسی می‌شود.')
    return
  }
  try {
    await moveTableSession({`,
  )
  code = code.replace(
    '  try {\n    await mergeTableSessions({',
    `  if (isOffline.value) {
    await enqueuePOSOfflineMutation('table_merge', {
      source_session: selectedTablePreview.value.session.name,
      target_table: mergeTableTarget.value,
    }, 'ترکیب میز آفلاین ذخیره شد و پس از اتصال بررسی می‌شود.')
    return
  }
  try {
    await mergeTableSessions({`,
  )

  code = code.replace(
    "async function submitPOSOrder(payNow = true, paymentMeta = {}, withProduction = false) {\n  if (!cart.length) {",
    "async function submitPOSOrder(payNow = true, paymentMeta = {}, withProduction = false) {\n  if (isOffline.value && editingOriginalOrder.isEditing) {\n    error.value = 'ویرایش یا جایگزینی فاکتور باز نیاز به اتصال اینترنت دارد.'\n    return\n  }\n  if (!cart.length) {",
  )

  code = code.replace(
    "    submitting.value = true\n    error.value = ''\n    successMessage.value = ''\n    try {\n      await createManagementTableOrderFromPOS({",
    `    if (isOffline.value) {
      const queued = await enqueuePOSOfflineMutation('table_add_items', {
        table_name: selectedTable.name,
        note: buildOrderNote(),
        items: cart.map((line) => ({
          item_code: line.item_code || '', title: line.title || '', qty: line.qty, unit_price: line.price, note: line.note || '',
        })),
      }, 'افزودن به میز آفلاین ذخیره شد و پس از اتصال بررسی می‌شود.')
      if (queued) {
        resetCurrentInvoiceState({ preserveFeedback: true })
        form.order_mode = 'dine_in'
        form.place = selectedTable.label
        saveActiveTicketSnapshot()
      }
      return
    }
    submitting.value = true
    error.value = ''
    successMessage.value = ''
    try {
      await createManagementTableOrderFromPOS({`,
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
    if (payNow) {
      const paymentQueued = await enqueuePOSOfflineMutation('manual_payment_claim', {
        client_order_key: queued.id,
        payment: paymentPayload,
      }, 'پرداخت دستی به‌صورت موقت ذخیره شد و پس از اتصال خودکار نهایی می‌شود.')
      if (!paymentQueued) return
    } else {
      await refreshPendingOfflineOrderCount()
      successMessage.value = 'سفارش ذخیره آفلاین شد و پس از اتصال همگام می‌شود.'
    }
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
  const end = new Date(\`\${until}T23:59:59\`)
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
