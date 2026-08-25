import test from 'node:test'
import assert from 'node:assert/strict'
import { transformManagementPosPage, transformManagementPosDefaultsPage } from '../scripts/pos-print-transform.mjs'
import { transformPosReliabilityPage } from '../scripts/pos-reliability-transform.mjs'

test('POS receipt transform makes thermal output continuous and width-aware', () => {
  const source = `
function receiptStylesCss() {
  return \`@page { size: 80mm auto; margin: 3mm; }\nhtml, body { width: 100%; margin: 0; padding: 0; }\n.receipt { width: 74mm; margin: 0 auto; font-size: \${receiptFontSizePx()}px; line-height: 1.45; }\`
}
`
  const result = transformPosReliabilityPage(transformManagementPosPage(source))
  assert.match(result, /thermalPaperWidthMm/)
  assert.match(result, /@page \{ margin: 0; \}/)
  assert.match(result, /\*, \*::before, \*::after \{ box-sizing: border-box; \}/)
  assert.match(result, /\.receipt \{[^}]*width: \$\{paperWidthMm\}mm[^}]*max-width: 100%/s)
  assert.match(result, /overflow-wrap: anywhere/)
  assert.match(result, /\.receipt table[^}]*max-width: 100%/s)
  assert.doesNotMatch(result, /size:\s*80mm auto/)
  assert.doesNotMatch(result, /page-break|break-before|break-after|break-inside/i)
})

test('POS receipt transform adds secondary customer to current and reprinted receipts', () => {
  const source = `
function buildReceiptMarkup({ printableItems, totalsRows, paymentLabel, customerName, mobile, orderMode, place, note, invoiceNo = receiptInvoiceNumber.value, }) {
  const mobileLabel = String(mobile || '').trim() || '-'
  return \`<div class="meta-row"><span>مشتری</span><span>\${escapeHtml(customerName || 'مشتری POS')}</span></div><div class="meta-row"><span>موبایل مشتری</span><span>\${escapeHtml(mobileLabel)}</span></div>\`
}
function buildCurrentTicketReceiptMarkup(paymentMethodOverride = '') { return buildReceiptMarkup({ customerName: form.customer_name || 'مشتری POS', mobile: form.mobile || '', }) }
const context = { printableItems, totalsRows, paymentLabel, customerName: customer, mobile: orderData.mobile || order.mobile || '', }
`
  const result = transformManagementPosPage(source)
  assert.match(result, /secondaryCustomer/)
  assert.match(result, /مشتری ثانویه/)
  assert.match(result, /form\.secondary_customer/)
  assert.match(result, /orderData\.secondary_customer/)
})

test('defaults transform adds 58mm and 80mm device-local paper width controls', () => {
  const source = `
<label>نام پرینتر<input class="input" v-model="profile.printer_name" /></label>
function defaultPrintProfiles() { return [{ profile_id: \`print-customer\`, kind: 'customer', printer_name: '', item_groups: [], show_prices: true, enabled: true }] }
function addPrintProfile() { printProfiles.value.push({ profile_id: 'x', kind: 'kitchen', printer_name: '', item_groups: [], show_prices: false, enabled: true }) }
`
  const result = transformManagementPosDefaultsPage(source)
  assert.match(result, /عرض رول/)
  assert.match(result, />58 میلی‌متر</)
  assert.match(result, />80 میلی‌متر</)
  assert.match(result, /paper_width_mm/)
  assert.match(result, /localStorage/)
})

test('secondary customer survives dine-in and kitchen/bar reprint paths', () => {
  const source = `
function buildConfirmedTableReceiptContext() {
  const flatLines = []
  const noteParts = []
  for (const order of confirmedDineInOrders.value) {
    const orderCode = String(order.name || '').trim()
    const cleanTableNote = cleanReceiptNote(order.note)
  }
  return {
    customerName: selectedDineInTable.value?.label || 'میز سالن',
    mobile: '-',
  }
}
function buildKitchenBarReceiptMarkup(profile, lines = []) {
  const printerName = String(profile?.printer_name || '').trim()
  return \`<p class="receipt-meta">مشتری: \${escapeHtml(form.customer_name || 'مشتری POS')}</p>\`
}
function currentProfileLines() {
  for (const order of confirmedDineInOrders.value) {
    lines.push({
          category_title: String(product?.category_title || product?.category || '').trim(),
          note: orderCode ? \`کد سفارش: \${orderCode}\` : '',
    })
  }
}
const lines = items.map((item) => ({
      category_title: String(product?.category_title || product?.category || '').trim(),
      note: item.note || '',
}))
`
  const result = transformManagementPosPage(source)
  assert.match(result, /secondaryCustomers/)
  assert.match(result, /order\.secondary_customer/)
  assert.match(result, /secondary_customer: orderData\.secondary_customer/)
  assert.match(result, /secondaryCustomerLabel/)
})
