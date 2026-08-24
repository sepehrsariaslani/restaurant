const DEVICE_PAPER_STORAGE_KEY = 'restaurant-pos-paper-width-v1'

function injectBefore(source, marker, insertion) {
  if (source.includes(insertion.trim())) return source
  if (!source.includes(marker)) return `${insertion}\n${source}`
  return source.replace(marker, `${insertion}\n${marker}`)
}

export function transformManagementPosPage(input) {
  let code = String(input || '')

  const helpers = `const POS_PAPER_WIDTH_STORAGE_KEY = '${DEVICE_PAPER_STORAGE_KEY}'

function normalizeThermalPaperWidth(value) {
  return Number(value) === 58 ? 58 : 80
}

function readDevicePaperWidths() {
  if (typeof window === 'undefined') return {}
  try {
    const parsed = JSON.parse(window.localStorage.getItem(POS_PAPER_WIDTH_STORAGE_KEY) || '{}')
    return parsed && typeof parsed === 'object' ? parsed : {}
  } catch (_) {
    return {}
  }
}

function thermalPaperWidthMm(profile = null) {
  const profileId = String(profile?.profile_id || profile?.label || '').trim()
  const widths = readDevicePaperWidths()
  if (profileId && widths[profileId]) return normalizeThermalPaperWidth(widths[profileId])
  const customerProfile = (bootPosConfig?.print_profiles || []).find(
    (row) => row && String(row.kind || '').toLowerCase() === 'customer' && row.enabled,
  )
  const customerId = String(customerProfile?.profile_id || customerProfile?.label || 'print-customer').trim()
  return normalizeThermalPaperWidth(widths[customerId] || 80)
}
`
  code = injectBefore(code, 'function receiptFontSizePx()', helpers)

  code = code.replace(
    'function receiptStylesCss() {\n  return `',
    'function receiptStylesCss(profile = null) {\n  const paperWidthMm = thermalPaperWidthMm(profile)\n  const horizontalPaddingMm = paperWidthMm === 58 ? 2 : 2.5\n  return `',
  )
  code = code.replaceAll('@page { size: 80mm auto; margin: 3mm; }', '@page { margin: 0; }')
  code = code.replaceAll(
    'html, body { width: 100%; margin: 0; padding: 0; }',
    'html, body { width: ${paperWidthMm}mm; max-width: ${paperWidthMm}mm; min-height: 0; margin: 0; padding: 0; overflow: visible; }',
  )
  code = code.replaceAll(
    '.receipt { width: 74mm; margin: 0 auto; font-size: ${receiptFontSizePx()}px; line-height: 1.45; }',
    '.receipt { width: ${paperWidthMm}mm; max-width: ${paperWidthMm}mm; min-height: 0; margin: 0; padding: 2mm ${horizontalPaddingMm}mm 3mm; font-size: ${receiptFontSizePx()}px; line-height: 1.45; overflow: visible; }',
  )
  code = code.replaceAll('var(--mg-text-muted)', '#6f625a')

  code = code.replace(/customerName,\s*mobile,/, 'customerName,\n  secondaryCustomer,\n  mobile,')
  code = code.replaceAll(
    "  const mobileLabel = String(mobile || '').trim() || '-'",
    "  const secondaryCustomerLabel = String(secondaryCustomer || '').trim()\n  const mobileLabel = String(mobile || '').trim() || '-'",
  )
  const customerRow = '<div class="meta-row"><span>مشتری</span><span>${escapeHtml(customerName || \'مشتری POS\')}</span></div>'
  const secondaryRow = '${secondaryCustomerLabel ? `<div class="meta-row"><span>مشتری ثانویه</span><span>${escapeHtml(secondaryCustomerLabel)}</span></div>` : \'\'}'
  if (code.includes(customerRow) && !code.includes('مشتری ثانویه</span><span>${escapeHtml(secondaryCustomerLabel)')) {
    code = code.replace(customerRow, `${customerRow}\n      ${secondaryRow}`)
  }
  code = code.replaceAll(
    "customerName: form.customer_name || 'مشتری POS',\n    mobile: form.mobile || '',",
    "customerName: form.customer_name || 'مشتری POS',\n    secondaryCustomer: form.secondary_customer || '',\n    mobile: form.mobile || '',",
  )
  code = code.replace(
    /customerName: form\.customer_name \|\| 'مشتری POS',\s*mobile: form\.mobile \|\| '',/,
    "customerName: form.customer_name || 'مشتری POS', secondaryCustomer: form.secondary_customer || '', mobile: form.mobile || '',",
  )
  code = code.replaceAll(
    "customerName: customer,\n        mobile: orderData.mobile || order.mobile || '',",
    "customerName: customer,\n        secondaryCustomer: orderData.secondary_customer || order.secondary_customer || '',\n        mobile: orderData.mobile || order.mobile || '',",
  )
  code = code.replaceAll(
    "customerName: customer,\n    mobile: orderData.mobile || order.mobile || '',",
    "customerName: customer,\n    secondaryCustomer: orderData.secondary_customer || order.secondary_customer || '',\n    mobile: orderData.mobile || order.mobile || '',",
  )
  code = code.replace(
    /customerName: customer,\s*mobile: orderData\.mobile \|\| order\.mobile \|\| '',/,
    "customerName: customer, secondaryCustomer: orderData.secondary_customer || order.secondary_customer || '', mobile: orderData.mobile || order.mobile || '',",
  )

  code = code.replace(
    "function buildConfirmedTableReceiptContext() {\n  const flatLines = []\n  const noteParts = []",
    "function buildConfirmedTableReceiptContext() {\n  const flatLines = []\n  const noteParts = []\n  const secondaryCustomers = []",
  )
  code = code.replace(
    "    const orderCode = String(order.name || '').trim()\n    const cleanTableNote = cleanReceiptNote(order.note)",
    "    const orderCode = String(order.name || '').trim()\n    const secondaryCustomer = String(order.secondary_customer || '').trim()\n    if (secondaryCustomer && !secondaryCustomers.includes(secondaryCustomer)) secondaryCustomers.push(secondaryCustomer)\n    const cleanTableNote = cleanReceiptNote(order.note)",
  )
  code = code.replace(
    "    customerName: selectedDineInTable.value?.label || 'میز سالن',\n    mobile: '-',",
    "    customerName: selectedDineInTable.value?.label || 'میز سالن',\n    secondaryCustomer: secondaryCustomers.join('، ') || form.secondary_customer || '',\n    mobile: '-',",
  )

  const productionCustomerLine = '<p class="receipt-meta">مشتری: ${escapeHtml(form.customer_name || \'مشتری POS\')}</p>'
  const productionSecondaryLine = '${String(form.secondary_customer || \'\').trim() ? `<p class="receipt-meta">مشتری ثانویه: ${escapeHtml(form.secondary_customer)}</p>` : \'\'}'
  if (code.includes(productionCustomerLine) && !code.includes('مشتری ثانویه: ${escapeHtml(form.secondary_customer)')) {
    code = code.replace(productionCustomerLine, `${productionCustomerLine}\n            ${productionSecondaryLine}`)
  }

  code = code.replaceAll(
    "          category_title: String(product?.category_title || product?.category || '').trim(),\n          note: orderCode ? `کد سفارش: ${orderCode}` : '',",
    "          category_title: String(product?.category_title || product?.category || '').trim(),\n          secondary_customer: order.secondary_customer || '',\n          note: orderCode ? `کد سفارش: ${orderCode}` : '',",
  )
  code = code.replaceAll(
    "      category_title: String(product?.category_title || product?.category || '').trim(),\n      note: item.note || '',",
    "      category_title: String(product?.category_title || product?.category || '').trim(),\n      secondary_customer: orderData.secondary_customer || order.secondary_customer || '',\n      note: item.note || '',",
  )

  code = code.replace(
    "  const printerName = String(profile?.printer_name || '').trim()",
    "  const printerName = String(profile?.printer_name || '').trim()\n  const secondaryCustomerLabel = String((lines || []).find((line) => String(line?.secondary_customer || '').trim())?.secondary_customer || form.secondary_customer || '').trim()",
  )
  code = code.replaceAll(
    "${String(form.secondary_customer || '').trim() ? `<p class=\"receipt-meta\">مشتری ثانویه: ${escapeHtml(form.secondary_customer)}</p>` : ''}",
    "${secondaryCustomerLabel ? `<p class=\"receipt-meta\">مشتری ثانویه: ${escapeHtml(secondaryCustomerLabel)}</p>` : ''}",
  )
  code = code.replace(
    '<style>${receiptStylesCss()}</style>\n      </head>\n      <body>\n        <div class="receipt">\n          <header class="receipt-header">',
    '<style>${receiptStylesCss(profile)}</style>\n      </head>\n      <body>\n        <div class="receipt">\n          <header class="receipt-header">',
  )

  const totalsHelper = `function resolveOrderReceiptTotals(orderData = {}, items = []) {
  const totalsData = orderData?.totals && typeof orderData.totals === 'object' ? orderData.totals : {}
  const modifiers = orderData?.financial_modifiers && typeof orderData.financial_modifiers === 'object' ? orderData.financial_modifiers : {}
  const itemSubtotal = (items || []).reduce((sum, item) => {
    const explicit = Number(item?.line_total)
    if (Number.isFinite(explicit) && explicit !== 0) return sum + explicit
    return sum + Number(item?.qty || item?.quantity || 0) * Number(item?.unit_price || item?.price || item?.price_at_time || 0)
  }, 0)
  const pick = (...values) => {
    for (const value of values) {
      if (value === null || value === undefined || value === '') continue
      const number = Number(value)
      if (Number.isFinite(number)) return number
    }
    return 0
  }
  return {
    itemsTotal: pick(orderData.items_total, orderData.subtotal, totalsData.itemsTotal, totalsData.items_total, itemSubtotal),
    discountAmount: pick(orderData.discount_amount, totalsData.discountAmount, totalsData.discount_amount, modifiers.discount_amount),
    walletApplied: pick(orderData.wallet_applied, totalsData.walletApplied, totalsData.wallet_applied, modifiers.wallet_applied),
    taxAmount: pick(orderData.tax_amount, totalsData.taxAmount, totalsData.tax_amount, modifiers.tax_amount),
    tipAmount: pick(orderData.tip_amount, totalsData.tipAmount, totalsData.tip_amount, modifiers.tip_amount),
    serviceAmount: pick(orderData.service_amount, totalsData.serviceAmount, totalsData.service_amount, modifiers.service_amount),
    packagingAmount: pick(orderData.packaging_amount, totalsData.packagingAmount, totalsData.packaging_amount, modifiers.packaging_amount),
    payableAmount: pick(orderData.grand_total, totalsData.payableAmount, totalsData.payable_amount, itemSubtotal),
  }
}
`
  code = injectBefore(code, 'async function printOrderReceipt(order)', totalsHelper)
  code = code.replaceAll(
    `    const totalsRows = buildReceiptTotalsRowsHtml({
      itemsTotal: Number(total || 0),
      discountAmount: 0,
      walletApplied: 0,
      taxAmount: 0,
      tipAmount: 0,
      serviceAmount: 0,
      payableAmount: Number(total || 0),
    })`,
    '    const totalsRows = buildReceiptTotalsRowsHtml(resolveOrderReceiptTotals(orderData, items))',
  )
  code = code.replaceAll(
    `  const totalsRows = buildReceiptTotalsRowsHtml({
    itemsTotal: Number(total || 0),
    discountAmount: 0,
    walletApplied: 0,
    taxAmount: 0,
    tipAmount: 0,
    serviceAmount: 0,
    payableAmount: Number(total || 0),
  })`,
    '  const totalsRows = buildReceiptTotalsRowsHtml(resolveOrderReceiptTotals(orderData, items))',
  )
  if (!code.includes("label: 'کسر از کیف پول'")) {
    code = code.replace(
      "    {\n      label: 'مالیات',",
      "    {\n      label: 'کسر از کیف پول',\n      value: totalValues.walletApplied || 0,\n      always: false,\n      negative: true,\n      className: '',\n    },\n    {\n      label: 'مالیات',",
    )
  }

  const printStart = `function printReceiptDocument(html) {
  if (typeof window === 'undefined' || typeof document === 'undefined') {
    return false
  }`
  const readyHelper = `async function waitForPOSPrintReady(targetWindow) {
  const targetDocument = targetWindow?.document
  if (!targetDocument) return
  try {
    if (targetDocument.readyState !== 'complete') {
      await new Promise((resolve) => {
        let settled = false
        const done = () => { if (!settled) { settled = true; resolve() } }
        targetWindow.addEventListener?.('load', done, { once: true })
        window.setTimeout(done, 900)
      })
    }
    if (targetDocument.fonts?.ready) {
      await Promise.race([
        targetDocument.fonts.ready,
        new Promise((resolve) => window.setTimeout(resolve, 1500)),
      ])
    }
  } catch (_) {}
}
`
  if (code.includes(printStart) && !code.includes('async function waitForPOSPrintReady')) {
    code = code.replace(printStart, `${readyHelper}\n${printStart}`)
  }
  code = code.replace(
    '  const triggerPrint = (target, cleanup = () => {}) => {\n    try {\n      target.focus?.()\n      target.print()',
    '  const triggerPrint = async (target, cleanup = () => {}) => {\n    await waitForPOSPrintReady(target)\n    try {\n      target.focus?.()\n      target.print()',
  )
  code = code.replaceAll('        triggerPrint(printWindow,', '        void triggerPrint(printWindow,')
  code = code.replaceAll('        triggerPrint(frame.contentWindow,', '        void triggerPrint(frame.contentWindow,')

  return code
}

export function transformManagementPosDefaultsPage(input) {
  let code = String(input || '')

  const helpers = `const POS_PAPER_WIDTH_STORAGE_KEY = '${DEVICE_PAPER_STORAGE_KEY}'

function normalizePaperWidth(value) {
  return Number(value) === 58 ? 58 : 80
}

function loadDevicePaperWidths() {
  if (typeof window === 'undefined') return {}
  try {
    const parsed = JSON.parse(window.localStorage.getItem(POS_PAPER_WIDTH_STORAGE_KEY) || '{}')
    return parsed && typeof parsed === 'object' ? parsed : {}
  } catch (_) {
    return {}
  }
}

function persistDevicePaperWidths() {
  if (typeof window === 'undefined') return
  const widths = {}
  for (const profile of printProfiles.value || []) {
    const key = String(profile?.profile_id || profile?.label || '').trim()
    if (key) widths[key] = normalizePaperWidth(profile.paper_width_mm)
  }
  window.localStorage.setItem(POS_PAPER_WIDTH_STORAGE_KEY, JSON.stringify(widths))
}
`
  code = injectBefore(code, 'const activeTab = ref(', helpers)

  const printerBlock = `              <label>
                نام پرینتر
                <input
                  class="input"
                  v-model="profile.printer_name"
                  placeholder="مثلاً: EPSON-TM20 / Kitchen Printer"
                />
              </label>`
  const widthBlock = `${printerBlock}
              <label>
                عرض رول
                <select class="input" v-model.number="profile.paper_width_mm" @change="persistDevicePaperWidths">
                  <option :value="58">58 میلی‌متر</option>
                  <option :value="80">80 میلی‌متر</option>
                </select>
                <small class="field-help">عرض رول روی همین دستگاه POS ذخیره می‌شود.</small>
              </label>`
  if (code.includes(printerBlock) && !code.includes('v-model.number="profile.paper_width_mm"')) {
    code = code.replace(printerBlock, widthBlock)
  }
  const compactPrinter = '<label>نام پرینتر<input class="input" v-model="profile.printer_name" /></label>'
  if (code.includes(compactPrinter) && !code.includes('v-model.number="profile.paper_width_mm"')) {
    code = code.replace(compactPrinter, compactPrinter + '<label>عرض رول<select class="input" v-model.number="profile.paper_width_mm" @change="persistDevicePaperWidths"><option :value="58">58 میلی‌متر</option><option :value="80">80 میلی‌متر</option></select></label>')
  }

  code = code.replaceAll("      printer_name: '',\n      item_groups:", "      printer_name: '',\n      paper_width_mm: 80,\n      item_groups:")
  code = code.replaceAll("    printer_name: '',\n    item_groups:", "    printer_name: '',\n    paper_width_mm: 80,\n    item_groups:")
  code = code.replaceAll(
    "      printer_name: profile.printer_name || '',\n      item_groups:",
    "      printer_name: profile.printer_name || '',\n      paper_width_mm: normalizePaperWidth(loadDevicePaperWidths()[profile.profile_id || profile.label] || 80),\n      item_groups:",
  )
  code = code.replace(
    "watch(printProfiles, markDirty, { deep: true })",
    "watch(printProfiles, () => { markDirty(); persistDevicePaperWidths() }, { deep: true })",
  )

  code = code.replace(
    "  const groupNames = (profile?.item_groups || []).join('، ') || 'همه'",
    "  const groupNames = (profile?.item_groups || []).join('، ') || 'همه'\n  const paperWidthMm = normalizePaperWidth(profile?.paper_width_mm || 80)\n  const horizontalPaddingMm = paperWidthMm === 58 ? 2 : 2.5",
  )
  code = code.replaceAll('@page { size: 80mm auto; margin: 3mm; }', '@page { margin: 0; }')
  code = code.replaceAll(
    'html, body { margin: 0; padding: 0; direction: rtl; font-family: Tahoma, Arial, sans-serif; color: #222; }',
    'html, body { width: ${paperWidthMm}mm; max-width: ${paperWidthMm}mm; min-height: 0; margin: 0; padding: 0; overflow: visible; direction: rtl; font-family: Tahoma, Arial, sans-serif; color: #222; }',
  )
  code = code.replaceAll(
    '.sheet { width: 74mm; margin: 0 auto; padding: 4mm 0; font-size: 12px; line-height: 1.6; }',
    '.sheet { width: ${paperWidthMm}mm; max-width: ${paperWidthMm}mm; min-height: 0; margin: 0; padding: 2mm ${horizontalPaddingMm}mm 3mm; font-size: 12px; line-height: 1.6; overflow: visible; }',
  )

  return code
}
