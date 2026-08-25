<template>
  <ManagementPageScaffold title="حسابداری یکپارچه ابری" subtitle="تراز دریافت و پرداخت، اسناد، صورت‌های مالی و سامانه مودیان — یکپارچه با فروش و انبار">
    <div class="totals-grid" v-if="boot.kpis">
      <div class="total-box"><small>موجودی صندوق (نقد)</small><strong>{{ formatMoneyValue(boot.kpis.cash_balance) }}</strong></div>
      <div class="total-box"><small>موجودی بانک</small><strong>{{ formatMoneyValue(boot.kpis.bank_balance) }}</strong></div>
      <div class="total-box"><small>حساب بدهکار (دریافتنی)</small><strong class="warn-text">{{ formatMoneyValue(boot.kpis.receivables) }}</strong></div>
      <div class="total-box"><small>حساب بستانکار (پرداختنی)</small><strong>{{ formatMoneyValue(boot.kpis.payables) }}</strong></div>
      <div class="total-box"><small>دریافت امروز</small><strong class="ok-text">{{ formatMoneyValue(boot.kpis.today_receipts) }}</strong></div>
      <div class="total-box"><small>پرداخت امروز</small><strong>{{ formatMoneyValue(boot.kpis.today_payments) }}</strong></div>
    </div>

    <section class="tabs-bar">
      <button v-for="tab in tabs" :key="tab.key" type="button" :class="['tab-btn', { active: activeTab === tab.key }]" @click="setTab(tab.key)">{{ tab.label }}</button>
    </section>

    <!-- دریافت/پرداخت -->
    <section v-if="activeTab === 'balance'" class="tab-body">
      <ManagementSurfaceCard title="تراز دریافت و پرداخت" subtitle="روزانه/دوره‌ای — فیلتر بر اساس تاریخ؛ گزارش کامل BI در مرکز گزارش">
        <div class="toolbar">
          <label class="date-label">از تاریخ<input class="input" type="date" v-model="balanceFilters.date_from" /></label>
          <label class="date-label">تا تاریخ<input class="input" type="date" v-model="balanceFilters.date_to" /></label>
          <button type="button" class="secondary-btn" @click="loadBalance" :disabled="balanceLoading">{{ balanceLoading ? '...' : 'جستجو' }}</button>
          <a class="link-btn" href="/management/reports/receipt-payment-balance">نمودار و تحلیل BI</a>
        </div>
        <div class="totals-grid" v-if="balance.summary">
          <div class="total-box"><small>مجموع دریافت</small><strong class="ok-text">{{ formatMoneyValue(balance.summary.receipts_total) }}</strong></div>
          <div class="total-box"><small>مجموع پرداخت</small><strong>{{ formatMoneyValue(balance.summary.payments_total) }}</strong></div>
          <div class="total-box"><small>خالص</small><strong :class="(balance.summary.net_total || 0) >= 0 ? 'ok-text' : 'warn-text'">{{ formatMoneyValue(balance.summary.net_total) }}</strong></div>
        </div>
        <p class="muted" v-if="balanceLoading">در حال دریافت...</p>
        <div v-else-if="balanceRows.length" class="table-wrap">
          <table class="data-table">
            <thead><tr><th>تاریخ</th><th>تعداد سند</th><th>دریافت</th><th>پرداخت</th><th>خالص</th><th>تراز انباشته</th></tr></thead>
            <tbody>
              <tr v-for="r in balanceRows" :key="r.date">
                <td>{{ r.date }}</td>
                <td>{{ formatQty(r.entries) }}</td>
                <td class="ok-text">{{ formatMoneyValue(r.receipts) }}</td>
                <td>{{ formatMoneyValue(r.payments) }}</td>
                <td :class="r.net >= 0 ? 'ok-text' : 'warn-text'">{{ formatMoneyValue(r.net) }}</td>
                <td>{{ formatMoneyValue(r.balance_run) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <p class="muted" v-else>داده‌ای در این بازه نیست.</p>
        <div v-if="(balance.summary?.by_mop || []).length" class="table-wrap" style="margin-top:0.7rem">
          <table class="data-table">
            <thead><tr><th>نوع</th><th>روش پرداخت</th><th>تعداد</th><th>مبلغ</th></tr></thead>
            <tbody>
              <tr v-for="(m, i) in balance.summary.by_mop" :key="i">
                <td>{{ m.payment_type }}</td><td>{{ m.mode_of_payment }}</td><td>{{ formatQty(m.entries) }}</td><td>{{ formatMoneyValue(m.total) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </ManagementSurfaceCard>
    </section>

    <!-- مودیان -->
    <section v-if="activeTab === 'tax'" class="tab-body">
      <ManagementSurfaceCard title="سامانه مودیان" subtitle="ارسال خودکار فاکتورهای فروش به سازمان مالیاتی، کد رهگیری و تطبیق دوره‌ای">
        <div class="totals-grid" v-if="tax.boot.summary">
          <div class="total-box"><small>در صف ارسال</small><strong>{{ formatQty(tax.boot.summary.queued) }}</strong></div>
          <div class="total-box"><small>ارسال‌شده</small><strong class="ok-text">{{ formatQty(tax.boot.summary.sent) }}</strong></div>
          <div class="total-box"><small>خطا</small><strong :class="{ 'warn-text': tax.boot.summary.error > 0 }">{{ formatQty(tax.boot.summary.error) }}</strong></div>
          <div class="total-box"><small>فاکتورهای ارسال‌نشده (۳۰ روز)</small><strong :class="{ 'warn-text': tax.boot.summary.unsent_invoices_30d > 0 }">{{ formatQty(tax.boot.summary.unsent_invoices_30d) }}</strong></div>
        </div>
        <div class="form-grid" v-if="tax.settings">
          <label class="check-row"><input type="checkbox" v-model="tax.settings.enabled" /> اتصال به سامانه مودیان فعال است</label>
          <label class="check-row"><input type="checkbox" v-model="tax.settings.sandbox" /> حالت آزمایشی (Sandbox)</label>
          <label class="check-row"><input type="checkbox" v-model="tax.settings.auto_submit" /> ارسال خودکار روزانه فاکتورها</label>
          <label>کد حافظه مالیاتی<input class="input" v-model.trim="tax.settings.memory_code" /></label>
          <label>کد اقتصادی<input class="input" v-model.trim="tax.settings.economic_code" /></label>
          <label>آدرس API سامانه<input class="input ltr" v-model.trim="tax.settings.api_url" placeholder="https://..." /></label>
          <label>توکن احراز هویت<input class="input ltr" type="password" v-model.trim="tax.newToken" :placeholder="tax.settings.token_set ? '•••••• (تنظیم شده)' : ''" /></label>
        </div>
        <div class="btn-row">
          <button type="button" class="primary-btn" @click="saveTaxSettings" :disabled="tax.saving">{{ tax.saving ? '...' : 'ذخیره تنظیمات' }}</button>
          <a class="link-btn" href="/management/reports/tax-reconciliation">گزارش تطبیق فروش و مالیات (BI)</a>
        </div>
        <p class="error" v-if="tax.error">{{ tax.error }}</p>
        <p class="success-msg" v-if="tax.message">{{ tax.message }}</p>
        <div class="toolbar" style="margin-top:0.8rem">
          <input class="input" v-model.trim="tax.invoiceInput" placeholder="شماره فاکتور (ACC-SINV-...) برای ارسال دستی" />
          <button type="button" class="secondary-btn" @click="submitInvoice" :disabled="tax.submitting">{{ tax.submitting ? '...' : 'ارسال فاکتور' }}</button>
        </div>
        <div class="table-wrap" v-if="tax.submissions.length">
          <table class="data-table">
            <thead><tr><th>فاکتور</th><th>وضعیت</th><th>شناسه مرجع</th><th>کد رهگیری مالیاتی</th><th>زمان ارسال</th><th></th></tr></thead>
            <tbody>
              <tr v-for="s in tax.submissions" :key="s.name">
                <td><strong>{{ s.sales_invoice }}</strong></td>
                <td><span class="pill" :class="{ ok: s.status === 'ارسال‌شده', warn: s.status === 'خطا' }">{{ s.status }}</span></td>
                <td><small class="muted ltr">{{ s.reference_id || '—' }}</small></td>
                <td><small class="muted ltr">{{ s.tax_id || '—' }}</small></td>
                <td><small class="muted">{{ s.submitted_at || '—' }}</small></td>
                <td class="row-actions">
                  <button v-if="s.status === 'خطا'" type="button" class="tertiary-btn" @click="submitInvoice(s.sales_invoice)">تلاش مجدد</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </ManagementSurfaceCard>
    </section>

    <!-- لینک‌های حسابداری -->
    <section v-if="activeTab === 'links'" class="tab-body">
      <ManagementSurfaceCard title="دفاتر و صورت‌های مالی" subtitle="درخت حساب‌ها (کل/معین/تفصیلی)، اسناد، گزارش گردش حساب و بستن سال مالی — داخل ERPNext">
        <div class="links-grid">
          <a v-for="l in boot.desk_links || []" :key="l.key" class="link-card" :href="l.url" target="_blank" rel="noopener">
            <strong>{{ l.label }}</strong>
            <small class="muted">{{ l.desc }}</small>
          </a>
        </div>
      </ManagementSurfaceCard>
      <ManagementSurfaceCard title="اسناد اخیر" subtitle="آخرین اسناد حسابداری (دستی/خودکار) — یکپارچه با فروش، انبار، باشگاه و صندوق">
        <div v-if="(boot.recent_journal_entries || []).length" class="table-wrap">
          <table class="data-table">
            <thead><tr><th>سند</th><th>تاریخ</th><th>مبلغ بدهکار</th><th>وضعیت</th><th>شرح</th></tr></thead>
            <tbody>
              <tr v-for="j in boot.recent_journal_entries" :key="j.name">
                <td><strong>{{ j.name }}</strong></td>
                <td>{{ j.posting_date }}</td>
                <td>{{ formatMoneyValue(j.total_debit) }}</td>
                <td><span class="pill" :class="{ ok: j.status === 'ثبت‌شده', warn: j.status === 'لغوشده' }">{{ j.status }}</span></td>
                <td class="sms-cell">{{ j.user_remark || '—' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <p class="muted" v-else>سندی ثبت نشده است.</p>
      </ManagementSurfaceCard>
    </section>
  </ManagementPageScaffold>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import ManagementPageScaffold from '@/components/management/ManagementPageScaffold.vue'
import ManagementSurfaceCard from '@/components/management/ManagementSurfaceCard.vue'
import {
  getManagementAccountingBoot,
  getManagementBIReport,
  getManagementTaxBoot,
  setManagementTaxSettings,
  listManagementTaxSubmissions,
  submitManagementTaxInvoice,
} from '@/utils/api'
import { formatMoney as formatMoneyUtil } from '@/utils/format'

const tabs = [
  { key: 'balance', label: 'تراز دریافت/پرداخت' },
  { key: 'tax', label: 'سامانه مودیان' },
  { key: 'links', label: 'دفاتر و صورت‌های مالی' },
]
const activeTab = ref('balance')
const loadedTabs = reactive({})

const boot = ref({ kpis: null, recent_journal_entries: [], desk_links: [] })
const balanceFilters = reactive({ date_from: '', date_to: '' })
const balance = ref({ summary: null, rows: [] })
const balanceLoading = ref(false)
const tax = reactive({ boot: { summary: null }, settings: null, newToken: '', saving: false, submitting: false, error: '', message: '', invoiceInput: '', submissions: [] })

const balanceRows = ref([])

function formatQty(v) { return Number(v || 0).toLocaleString('fa-IR') }
function formatMoneyValue(v) { return formatMoneyUtil(Number(v || 0)) }

async function loadBoot() {
  try { boot.value = await getManagementAccountingBoot() } catch (err) { /* ignore */ }
}

async function loadBalance() {
  balanceLoading.value = true
  try {
    const payload = await getManagementBIReport('receipt-payment-balance', { ...balanceFilters })
    const data = payload?.report || payload || {}
    balance.value.summary = data.summary || null
    balanceRows.value = data.rows || []
  } catch (err) {
    balance.value = { summary: null, rows: [] }
    balanceRows.value = []
  } finally { balanceLoading.value = false }
}

async function loadTax() {
  tax.error = ''
  try {
    tax.boot = await getManagementTaxBoot()
    tax.settings = { ...tax.boot.settings }
    const payload = await listManagementTaxSubmissions({ limit: 20 })
    tax.submissions = payload.submissions || []
  } catch (err) {
    tax.error = err.message || 'دریافت اطلاعات مودیان ناموفق بود.'
  }
}

async function saveTaxSettings() {
  if (!tax.settings) return
  tax.saving = true
  tax.error = ''
  tax.message = ''
  try {
    await setManagementTaxSettings({
      restaurant_tax_enabled: tax.settings.enabled ? 1 : 0,
      restaurant_tax_sandbox: tax.settings.sandbox ? 1 : 0,
      restaurant_tax_auto_submit: tax.settings.auto_submit ? 1 : 0,
      restaurant_tax_api_url: tax.settings.api_url,
      restaurant_tax_memory_code: tax.settings.memory_code,
      restaurant_tax_economic_code: tax.settings.economic_code,
      ...(tax.newToken ? { restaurant_tax_auth_token: tax.newToken } : {}),
    })
    tax.newToken = ''
    tax.message = 'تنظیمات مودیان ذخیره شد.'
    await loadTax()
  } catch (err) {
    tax.error = err.message || 'ذخیره تنظیمات ناموفق بود.'
  } finally { tax.saving = false }
}

async function submitInvoice(invoice) {
  const name = typeof invoice === 'string' && invoice ? invoice : tax.invoiceInput
  if (!name) { tax.error = 'شماره فاکتور را وارد کنید.'; return }
  tax.submitting = true
  tax.error = ''
  tax.message = ''
  try {
    const payload = await submitManagementTaxInvoice(name)
    tax.message = payload.status === 'success'
      ? `فاکتور ${name} ارسال شد.${payload.tax_id ? ' کد رهگیری: ' + payload.tax_id : ''}`
      : (payload.note || 'در صف قرار گرفت.')
    tax.invoiceInput = ''
    await loadTax()
  } catch (err) {
    tax.error = err.message || 'ارسال فاکتور ناموفق بود.'
  } finally { tax.submitting = false }
}

function setTab(key) {
  activeTab.value = key
  if (loadedTabs[key]) return
  loadedTabs[key] = true
  if (key === 'balance') loadBalance()
  if (key === 'tax') loadTax()
}

onMounted(async () => {
  await loadBoot()
  loadedTabs.balance = true
  await loadBalance()
})
</script>

<style scoped>
.tab-body > * + * { margin-top: 0.9rem; }
.toolbar { display: flex; flex-wrap: wrap; gap: 0.5rem; align-items: flex-end; margin-bottom: 0.75rem; }
.toolbar .input { min-width: 160px; }
.date-label { display: inline-flex; flex-direction: column; gap: 0.25rem; font-size: 0.8rem; color: var(--mg-text-muted); }
.link-btn { font-size: 0.85rem; color: var(--mg-primary); text-decoration: underline; }
.form-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 0.65rem; margin-bottom: 0.7rem; }
.form-grid label { display: grid; gap: 0.3rem; font-size: 0.86rem; align-content: start; }
.ltr { direction: ltr; text-align: left; }
.links-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 0.7rem; }
.link-card { display: grid; gap: 0.25rem; padding: 0.85rem 0.9rem; border: 1px solid rgba(90, 74, 58, 0.16); border-radius: 12px; text-decoration: none; color: inherit; transition: border-color 0.15s; }
.link-card:hover { border-color: var(--mg-primary); }
.row-actions { white-space: nowrap; }
</style>
