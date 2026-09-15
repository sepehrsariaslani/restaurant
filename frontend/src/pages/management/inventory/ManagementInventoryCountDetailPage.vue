<template>
  <ManagementPageScaffold
    :title="detail?.name ? `جزئیات انبارگردانی ${detail.name}` : 'جزئیات انبارگردانی'"
    subtitle="سند ثبت‌شده، مغایرت اقلام و اثر ارزشی در ERPNext"
  >
    <template #actions>
      <a class="secondary-btn" href="/management/inventory/count">بازگشت به انبارگردانی</a>
    </template>

    <p v-if="loading" class="muted" role="status">در حال دریافت جزئیات سند...</p>
    <p v-if="error" class="error">{{ error }}</p>

    <template v-if="detail && !loading">
      <section class="count-detail-summary">
        <article class="summary-card"><small>شماره سند</small><strong dir="ltr">{{ detail.name }}</strong></article>
        <article class="summary-card"><small>تاریخ ثبت</small><strong>{{ formatDate(detail.posting_date) }}</strong></article>
        <article class="summary-card"><small>شرکت</small><strong>{{ detail.company || '—' }}</strong></article>
        <article class="summary-card"><small>مغایرت ارزشی</small><strong :class="Number(detail.difference_amount || 0) === 0 ? 'ok-text' : 'warn-text'">{{ formatMoney(detail.difference_amount) }}</strong></article>
      </section>

      <ManagementSurfaceCard title="اقلام و مغایرت‌ها" subtitle="این جدول از Stock Ledger Entry سند خوانده می‌شود و فقط برای مشاهده است.">
        <ManagementSmartDataTable
          :columns="columns"
          :rows="detail.rows || []"
          row-key="item_code"
          search-placeholder="جستجوی کالا یا انبار..."
        >
          <template #cell-item_code="{ value }"><strong dir="ltr">{{ value }}</strong></template>
          <template #cell-warehouse="{ value }">{{ value || '—' }}</template>
          <template #cell-diff_qty="{ row }"><span :class="Number(row.diff_qty) >= 0 ? 'ok-text' : 'warn-text'">{{ signedQty(row.diff_qty) }}</span></template>
          <template #cell-diff_value="{ row }"><span :class="Number(row.diff_value) >= 0 ? 'ok-text' : 'warn-text'">{{ formatMoney(row.diff_value) }}</span></template>
          <template #empty>برای این سند جزئیاتی ثبت نشده است.</template>
        </ManagementSmartDataTable>
      </ManagementSurfaceCard>
    </template>
  </ManagementPageScaffold>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import ManagementPageScaffold from '@/components/management/ManagementPageScaffold.vue'
import ManagementSmartDataTable from '@/components/management/ManagementSmartDataTable.vue'
import ManagementSurfaceCard from '@/components/management/ManagementSurfaceCard.vue'
import { getManagementStockReconciliation } from '@/utils/api'
import { formatMoney, parseQuery } from '@/utils/format'
import { formatPersianDate } from '@/utils/persianDate'

const query = parseQuery()
const name = String(query.name || query.reconciliation || '').trim()
const loading = ref(false)
const error = ref('')
const detail = ref(null)
const columns = [
  { key: 'item_code', label: 'کالا' },
  { key: 'warehouse', label: 'انبار' },
  { key: 'diff_qty', label: 'تغییر مقدار' },
  { key: 'diff_value', label: 'تغییر ارزش' },
]

function formatDate(value) {
  return value ? formatPersianDate(value) : '—'
}

function signedQty(value) {
  const amount = Number(value || 0)
  return `${amount > 0 ? '+' : ''}${amount.toLocaleString('fa-IR', { maximumFractionDigits: 4 })}`
}

async function load() {
  if (!name) {
    error.value = 'شماره سند انبارگردانی مشخص نشده است.'
    return
  }
  loading.value = true
  error.value = ''
  try {
    detail.value = await getManagementStockReconciliation(name)
  } catch (err) {
    error.value = err?.message || 'دریافت جزئیات انبارگردانی ناموفق بود.'
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.count-detail-summary {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0.7rem;
}

.summary-card {
  display: grid;
  gap: 0.35rem;
  min-height: 4.6rem;
  padding: 0.85rem 1rem;
  border: 1px solid var(--mg-border-light);
  border-radius: var(--mg-radius-md);
  background: var(--mg-bg-surface);
}

.summary-card small { color: var(--mg-text-muted); }
.summary-card strong { color: var(--mg-text-main); font-size: 1rem; }
.error { color: var(--mg-danger); }

@media (max-width: 800px) {
  .count-detail-summary { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}

@media (max-width: 480px) {
  .count-detail-summary { grid-template-columns: 1fr; }
}
</style>
