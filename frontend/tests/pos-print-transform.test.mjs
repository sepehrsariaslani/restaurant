import test from 'node:test'
import assert from 'node:assert/strict'
import { transformManagementPosPage, transformManagementPosDefaultsPage } from '../scripts/pos-print-transform.mjs'

test('POS receipt transform makes thermal output continuous and width-aware', () => {
  const source = `
function receiptStylesCss() {
  return \`@page { size: 80mm auto; margin: 3mm; }\n.receipt { width: 74mm; margin: 0 auto; }\`
}
`
  const result = transformManagementPosPage(source)
  assert.match(result, /thermalPaperWidthMm/)
  assert.match(result, /@page \{ margin: 0; \}/)
  assert.doesNotMatch(result, /size:\s*80mm auto/)
  assert.doesNotMatch(result, /page-break/i)
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
