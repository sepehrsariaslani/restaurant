<template>
  <ManagementPageScaffold :title="detail?.name ? `جزئیات ${detail.name}` : 'جزئیات سند'" :subtitle="doctypeLabel">
    <template #actions>
      <a class="secondary-btn" href="/management/inventory/documents">بازگشت به اسناد</a>
      <a v-if="nativeUrl" class="secondary-btn" :href="nativeUrl">بازکردن سند در ERPNext</a>
    </template>

    <p v-if="loading" class="muted" role="status">در حال دریافت جزئیات سند...</p>
    <p v-if="error" class="error">{{ error }}</p>

    <template v-if="detail && !loading">
      <section class="document-summary">
        <article><small>نوع سند</small><strong>{{ doctypeLabel }}</strong></article>
        <article><small>شماره</small><strong dir="ltr">{{ detail.name }}</strong></article>
        <article><small>تاریخ</small><strong>{{ detail.posting_date ? formatDate(detail.posting_date) : '—' }}</strong></article>
        <article><small>وضعیت</small><strong>{{ detail.status || statusLabel(detail.docstatus) }}</strong></article>
      </section>

      <ManagementSurfaceCard title="اطلاعات سند" subtitle="مرجع اصلی این اطلاعات سند native ERPNext است.">
        <dl class="document-fields">
          <template v-for="field in summaryFields" :key="field.key">
            <div v-if="detail[field.key] !== undefined && detail[field.key] !== ''">
              <dt>{{ field.label }}</dt>
              <dd>{{ displayValue(detail[field.key], field.key) }}</dd>
            </div>
          </template>
        </dl>
      </ManagementSurfaceCard>

      <ManagementSurfaceCard v-if="itemRows.length" title="اقلام سند" subtitle="ردیف‌های child table به‌صورت مشترک نمایش داده می‌شوند.">
        <ManagementSmartDataTable :columns="itemColumns" :rows="itemRows" row-key="idx">
          <template #cell-item_code="{ value }"><strong dir="ltr">{{ value || '—' }}</strong></template>
          <template #cell-warehouse="{ value }">{{ value || '—' }}</template>
          <template #cell-qty="{ value }">{{ quantity(value) }}</template>
          <template #cell-rate="{ value }">{{ formatMoney(value) }}</template>
          <template #cell-amount="{ value }">{{ formatMoney(value) }}</template>
        </ManagementSmartDataTable>
      </ManagementSurfaceCard>
    </template>
  </ManagementPageScaffold>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import ManagementPageScaffold from '@/components/management/ManagementPageScaffold.vue'
import ManagementSmartDataTable from '@/components/management/ManagementSmartDataTable.vue'
import ManagementSurfaceCard from '@/components/management/ManagementSurfaceCard.vue'
import { callMethodByPath } from '@/utils/api'
import { formatMoney, parseQuery } from '@/utils/format'
import { formatPersianDate } from '@/utils/persianDate'

const query = parseQuery()
const doctype = String(query.doctype || '').trim()
const name = String(query.name || '').trim()
const loading = ref(false)
const error = ref('')
const detail = ref(null)

const typeLabels = {
  'Purchase Invoice': 'فاکتور خرید',
  'Purchase Receipt': 'رسید خرید',
  'Stock Entry': 'سند انتقال انبار',
}
const doctypeLabel = computed(() => typeLabels[doctype] || doctype || 'سند')
const nativeUrl = computed(() => doctype && name ? `/app/${doctype.toLowerCase().replace(/\s+/g, '-')}/${encodeURIComponent(name)}` : '')
const summaryFields = computed(() => {
  if (doctype === 'Stock Entry') return [
    { key: 'stock_entry_type', label: 'نوع گردش' },
    { key: 'from_warehouse', label: 'انبار مبدأ' },
    { key: 'to_warehouse', label: 'انبار مقصد' },
    { key: 'remarks', label: 'شرح' },
    { key: 'company', label: 'شرکت' },
  ]
  return [
    { key: 'supplier_name', label: 'تأمین‌کننده' },
    { key: 'company', label: 'شرکت' },
    { key: 'currency', label: 'ارز' },
    { key: 'grand_total', label: 'مبلغ کل' },
    { key: 'remarks', label: 'شرح' },
  ]
})
const itemColumns = [
  { key: 'item_code', label: 'کالا' },
  { key: 'warehouse', label: 'انبار' },
  { key: 'qty', label: 'مقدار' },
  { key: 'rate', label: 'نرخ' },
  { key: 'amount', label: 'مبلغ' },
]
const itemRows = computed(() => (Array.isArray(detail.value?.items) ? detail.value.items : []).map((row, index) => ({
  ...row,
  idx: row.idx || index + 1,
  warehouse: row.warehouse || row.s_warehouse || row.t_warehouse || '',
  qty: row.qty ?? row.transfer_qty ?? row.actual_qty ?? 0,
  rate: row.rate ?? row.basic_rate ?? row.valuation_rate ?? 0,
  amount: row.amount ?? row.basic_amount ?? 0,
})))

function formatDate(value) { return value ? formatPersianDate(value) : '—' }
function quantity(value) { return Number(value || 0).toLocaleString('fa-IR', { maximumFractionDigits: 3 }) }
function statusLabel(value) { return Number(value) === 1 ? 'ثبت نهایی' : Number(value) === 2 ? 'لغوشده' : 'پیش‌نویس' }
function displayValue(value, key = '') {
  if (typeof value === 'number' && /total|amount|rate/i.test(String(key))) return formatMoney(value)
  return String(value ?? '—')
}

async function load() {
  if (!doctype || !name) {
    error.value = 'نوع و شماره سند مشخص نشده است.'
    return
  }
  loading.value = true
  error.value = ''
  try {
    detail.value = await callMethodByPath('frappe.client.get', { doctype, name })
  } catch (err) {
    error.value = err?.message || 'دریافت جزئیات سند ناموفق بود.'
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.document-summary {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0.7rem;
}

.document-summary article {
  display: grid;
  gap: 0.25rem;
  padding: 0.85rem 1rem;
  border: 1px solid var(--mg-border-light);
  border-radius: var(--mg-radius-md);
  background: var(--mg-bg-surface);
}

.document-summary small, dt { color: var(--mg-text-muted); }
.document-summary strong, dd { color: var(--mg-text-main); }
.document-fields { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 0.75rem; margin: 0; }
.document-fields div { padding: 0.7rem; border-radius: var(--mg-radius-sm); background: var(--mg-bg-page); }
dt { font-size: 0.75rem; }
dd { margin: 0.25rem 0 0; font-weight: 800; word-break: break-word; }
.error { color: var(--mg-danger); }

@media (max-width: 760px) {
  .document-summary, .document-fields { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}

@media (max-width: 480px) {
  .document-summary, .document-fields { grid-template-columns: 1fr; }
}
</style>
