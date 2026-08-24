function injectBefore(source, marker, insertion) {
  if (!marker || source.includes(insertion.trim()) || !source.includes(marker)) return source
  return source.replace(marker, `${insertion}\n${marker}`)
}

function injectWithin(source, startMarker, anchor, insertion) {
  const start = source.indexOf(startMarker)
  if (start < 0) return source
  const at = source.indexOf(anchor, start)
  if (at < 0) return source
  if (source.slice(start, at).includes(insertion.trim())) return source
  return `${source.slice(0, at)}${insertion}\n${source.slice(at)}`
}

function removeQuickEditStockField(source) {
  let code = source
  const full = /\s*<div class="qe-field">\s*<span>موجودی<\/span>\s*<div class="stock-toggle-row">[\s\S]*?<\/div>\s*<template v-if="quickEditForm\.out_of_stock">[\s\S]*?<\/template>\s*<\/div>/
  code = code.replace(full, '')
  const noDate = /\s*<div class="qe-field">\s*<span>موجودی<\/span>\s*<div class="stock-toggle-row">[\s\S]*?<\/div>\s*<\/div>/
  code = code.replace(noDate, '')
  code = code.replace(/\n?\.stock-toggle-row\s*\{[^}]*\}/g, '')
  code = code.replace(/\n?\.stock-toggle-btn(?:\.[\w-]+)?\s*\{[^}]*\}/g, '')
  return code
}

export function transformPosBackgroundPage(input) {
  let code = String(input || '')
  if (!code.includes('async function submitPOSOrder(')) return code

  const imports = `import {
  enqueuePOSBackgroundCheckout,
  enqueuePOSBackgroundSettlement,
  getPOSBackgroundOperation,
} from '@/utils/posReliabilityApi'`
  code = injectBefore(code, "import { formatMoney", imports)

  const stateMarker = 'const offlineSyncing = ref(false)'
  if (code.includes(stateMarker) && !code.includes('const posBackgroundOperations = ref([])')) {
    code = code.replace(
      stateMarker,
      `${stateMarker}\nconst posBackgroundOperations = ref([])`,
    )
  }

  const helperBlock = `function posBackgroundStatusLabel(status) {
  const key = String(status || '').toLowerCase()
  if (key === 'queued') return 'در صف'
  if (key === 'running') return 'در حال انجام'
  if (key === 'done') return 'انجام شد'
  if (key === 'failed') return 'خطا'
  return 'نامشخص'
}

function trackPOSBackgroundJob(response, label = 'عملیات POS') {
  const jobKey = String(response?.job_key || '').trim()
  if (!jobKey) return
  const current = {
    job_key: jobKey,
    order_id: String(response?.order_id || '').trim(),
    status: String(response?.status || 'queued'),
    label,
    error: '',
  }
  posBackgroundOperations.value = [
    current,
    ...posBackgroundOperations.value.filter((row) => row.job_key !== jobKey),
  ].slice(0, 5)
  void watchPOSBackgroundJob(current)
}

async function watchPOSBackgroundJob(job) {
  for (let attempt = 0; attempt < 180; attempt += 1) {
    await new Promise((resolve) => setTimeout(resolve, 2000))
    try {
      const state = await getPOSBackgroundOperation(job.job_key)
      Object.assign(job, state || {})
      posBackgroundOperations.value = [...posBackgroundOperations.value]
      if (job.status === 'done') {
        successMessage.value = job.order_id
          ? \`عملیات فاکتور \${job.order_id} در پس‌زمینه تکمیل شد.\`
          : 'عملیات POS در پس‌زمینه تکمیل شد.'
        void loadPOSBoot()
        void loadRecentOrders(true)
        void loadOpenInvoices(true)
        return
      }
      if (job.status === 'failed') {
        error.value = job.error || \`عملیات \${job.order_id || ''} در پس‌زمینه ناموفق بود.\`
        return
      }
    } catch (_) {
      if (isOffline.value) return
    }
  }
}`

  code = injectBefore(code, 'async function submitPOSOrder(', helperBlock)

  const bgSubmit = `  if (payNow) {
    submitting.value = true
    error.value = ''
    successMessage.value = ''
    try {
      if (!payload.client_order_key) {
        payload.client_order_key = createOfflineOrderRecord(payload).id
      }
      const queued = await enqueuePOSBackgroundCheckout(payload, withProduction)
      trackPOSBackgroundJob(
        queued,
        withProduction ? 'تسویه و تحویل' : 'تسویه',
      )
      successMessage.value = queued?.order_id
        ? \`فاکتور \${queued.order_id} در صف پردازش پس‌زمینه قرار گرفت؛ می‌توانید فاکتور بعدی را ثبت کنید.\`
        : 'عملیات در صف پس‌زمینه قرار گرفت؛ می‌توانید فاکتور بعدی را ثبت کنید.'
      resetCurrentInvoiceState({ preserveFeedback: true })
      saveActiveTicketSnapshot()
    } catch (errorObj) {
      error.value = errorObj?.message || 'قرار دادن عملیات در صف پس‌زمینه ناموفق بود.'
    } finally {
      submitting.value = false
    }
    return
  }
`
  code = injectWithin(
    code,
    '  const payload = {',
    '  submitting.value = true',
    bgSubmit,
  )

  const editPayBlock = `    submitting.value = true
    error.value = ''
    successMessage.value = ''
    try {
      const queued = await enqueuePOSBackgroundSettlement(
        editingOriginalOrder.name,
        paymentPayload || paymentMeta || {},
        withProduction,
      )
      trackPOSBackgroundJob(
        queued,
        withProduction ? 'تسویه و تحویل' : 'تسویه',
      )
      successMessage.value = \`فاکتور \${editingOriginalOrder.order_code || editingOriginalOrder.name} در صف پردازش پس‌زمینه قرار گرفت؛ می‌توانید فاکتور بعدی را ثبت کنید.\`
      resetCurrentInvoiceState({ preserveFeedback: true })
      saveActiveTicketSnapshot()
    } catch (errorObj) {
      error.value = errorObj?.message || 'قرار دادن تسویه در صف پس‌زمینه ناموفق بود.'
    } finally {
      submitting.value = false
    }
    return
`
  code = injectWithin(
    code,
    '  if (payNow && editingOriginalOrder.isEditing && editingOriginalOrder.name) {',
    '    submitting.value = true',
    editPayBlock,
  )

  const settleInvoiceBlock = `  try {
    const queued = await enqueuePOSBackgroundSettlement(invoice.name, paymentSelection || {}, false)
    trackPOSBackgroundJob(queued, 'تسویه')
    successMessage.value = \`فاکتور \${invoice.name} در صف تسویه قرار گرفت؛ می‌توانید کار بعدی را انجام دهید.\`
  } catch (errorObj) {
    error.value = errorObj?.message || 'قرار دادن تسویه در صف ناموفق بود.'
  }
  return
`
  code = injectWithin(
    code,
    'async function settleSelectedInvoice(invoice, paymentSelection = {}) {',
    '  settlingOpenInvoice.value = true',
    settleInvoiceBlock,
  )

  const settleDeliverBlock = `  try {
    const queued = await enqueuePOSBackgroundSettlement(invoice.name, paymentSelection || {}, true)
    trackPOSBackgroundJob(queued, 'تسویه و تحویل')
    successMessage.value = \`فاکتور \${invoice.name} در صف تسویه و تحویل قرار گرفت؛ می‌توانید کار بعدی را انجام دهید.\`
  } catch (errorObj) {
    error.value = errorObj?.message || 'قرار دادن تسویه و تحویل در صف ناموفق بود.'
  }
  return
`
  code = injectWithin(
    code,
    'async function settleAndDeliverFromInvoice(invoice, paymentSelection = {}) {',
    '  settlingOpenInvoice.value = true',
    settleDeliverBlock,
  )

  const selectedOpenBlock = `  try {
    const queued = await enqueuePOSBackgroundSettlement(
      selectedOpenInvoice.value.name,
      {
        method: normalizePaymentMethodKind(payment.method),
        reference_no: payment.reference_no || '',
        rrn: payment.rrn || '',
      },
      false,
    )
    trackPOSBackgroundJob(queued, 'تسویه')
    successMessage.value = \`فاکتور \${selectedOpenInvoice.value.name} در صف تسویه قرار گرفت.\`
  } catch (errorObj) {
    error.value = errorObj?.message || 'قرار دادن تسویه در صف ناموفق بود.'
  }
  return
`
  code = injectWithin(
    code,
    'async function settleSelectedOpenInvoice() {',
    '  settlingOpenInvoice.value = true',
    selectedOpenBlock,
  )

  const detailBlock = `  try {
    const queued = await enqueuePOSBackgroundSettlement(
      orderDetailModal.order.name,
      {
        method: selectedMethod,
        mode_of_payment: selectedOption?.mode_of_payment || selectedOption?.label || '',
        provider: 'manual',
        reference_no: selectedMethod === 'credit' ? '' : (orderDetailModal.settleReference || payment.reference_no || ''),
        rrn: selectedMethod === 'credit' ? '' : (payment.rrn || ''),
      },
      false,
    )
    trackPOSBackgroundJob(queued, 'تسویه')
    orderDetailModal.settleError = ''
    successMessage.value = \`فاکتور \${orderDetailModal.order.name} در صف تسویه قرار گرفت.\`
    closeOrderDetailModal()
  } catch (errorObj) {
    orderDetailModal.settleError = errorObj?.message || 'قرار دادن تسویه در صف ناموفق بود.'
  }
  return
`
  code = injectWithin(
    code,
    'async function confirmSettleOrder() {',
    '  orderDetailModal.settling = true',
    detailBlock,
  )

  code = removeQuickEditStockField(code)

  const jobsUi = `<div v-if="posBackgroundOperations.length" class="pos-background-jobs" dir="rtl">
      <div
        v-for="job in posBackgroundOperations"
        :key="job.job_key"
        class="pos-background-job"
        :class="\`is-\${job.status || 'queued'}\`"
      >
        <span>{{ job.label }} {{ job.order_id || '' }}</span>
        <strong>{{ posBackgroundStatusLabel(job.status) }}</strong>
      </div>
    </div>`
  if (!code.includes('class="pos-background-jobs"')) {
    code = code.replace(
      '<p class="error pos-inline-error" v-if="error">{{ error }}</p>',
      `${jobsUi}\n    <p class="error pos-inline-error" v-if="error">{{ error }}</p>`,
    )
  }

  if (code.includes('<style scoped>') && !code.includes('.pos-background-jobs {')) {
    code = code.replace(
      '<style scoped>',
      `<style scoped>
.pos-background-jobs { display: grid; gap: 0.35rem; margin: 0.35rem 0.85rem; }
.pos-background-job { display: flex; align-items: center; justify-content: space-between; gap: 0.6rem; padding: 0.45rem 0.65rem; border: 1px solid var(--mg-border-light); border-radius: 10px; background: var(--mg-bg-surface); font-size: 0.76rem; }
.pos-background-job.is-queued strong, .pos-background-job.is-running strong { color: var(--mg-primary); }
.pos-background-job.is-done strong { color: var(--mg-success); }
.pos-background-job.is-failed strong { color: var(--mg-danger); }`,
    )
  }

  return code
}

export function transformPosProductPanelAvailability(input) {
  let code = String(input || '')
  if (!code.includes('quantityValue(')) return code

  if (!code.includes('function isProductUnavailableForDisplay(')) {
    const helper = `function isProductUnavailableForDisplay(item) {
  const flag = Number(item?.out_of_stock ?? item?.restaurant_out_of_stock ?? 0) === 1
  if (!flag) return false
  const until = String(item?.out_of_stock_until || item?.restaurant_out_of_stock_until || '').trim()
  if (!until) return true
  const end = new Date(\`\${until}T23:59:59\`)
  if (!Number.isFinite(end.getTime())) return true
  return end.getTime() >= Date.now()
}

`
    const marker = 'function quantityValue'
    if (code.includes(marker)) code = code.replace(marker, `${helper}${marker}`)
  }

  code = code.replaceAll(
    'Number(item.out_of_stock) === 1',
    'isProductUnavailableForDisplay(item)',
  )
  return code
}
