<template>
  <section class="product-inventory-panel" dir="rtl">
    <ManagementSurfaceCard title="انبار و عملیات" subtitle="مانده، رزرو، ارزش و مسیرهای عملیاتی همین کالا از native ERPNext">
      <div class="inventory-filters">
        <label>
          از تاریخ
          <PersianDateInput :model-value="dateRange.date_from" @update:modelValue="updateDate('date_from', $event)" />
        </label>
        <label>
          تا تاریخ
          <PersianDateInput :model-value="dateRange.date_to" @update:modelValue="updateDate('date_to', $event)" />
        </label>
        <label>
          انبار
          <SearchableDropdown
            :model-value="warehouse"
            :options="warehouseOptions"
            placeholder="همه انبارها"
            search-placeholder="جستجوی انبار..."
            include-empty-option
            empty-label="همه انبارها"
            @update:modelValue="$emit('update:warehouse', $event)"
          />
        </label>
        <button type="button" class="secondary-btn" :disabled="loading" @click="$emit('refresh')">{{ loading ? 'در حال بروزرسانی...' : 'بروزرسانی' }}</button>
      </div>

      <div v-if="loading" class="inventory-state">در حال دریافت مانده و دفتر موجودی...</div>
      <div v-else-if="error" class="inventory-state inventory-state--error">
        <p>{{ error }}</p>
        <button type="button" class="secondary-btn" @click="$emit('refresh')">تلاش دوباره</button>
      </div>
      <template v-else>
        <div class="inventory-kpis">
          <article v-for="metric in metrics" :key="metric.key" class="inventory-kpi">
            <small>{{ metric.label }}</small>
            <strong>{{ metric.money ? formatMoney(summary[metric.key]) : formatQty(summary[metric.key]) }}</strong>
            <span>{{ metric.suffix || summary.stock_uom || 'واحد' }}</span>
          </article>
        </div>

        <div class="inventory-grid">
          <section class="inventory-surface">
            <header class="inventory-surface__head">
              <div><strong>مانده به تفکیک انبار</strong><small>Bin native</small></div>
              <span>{{ bins.length.toLocaleString('fa-IR') }} انبار</span>
            </header>
            <ManagementSmartDataTable
              :columns="binColumns"
              :rows="bins"
              row-key="warehouse"
              :show-search="false"
              :filterable="false"
              :freezable="false"
              :resizable="false"
              empty-text="برای این کالا مانده‌ای در انبار ثبت نشده است."
            >
              <template #cell-actual_qty="{ value }">{{ formatQty(value) }}</template>
              <template #cell-projected_qty="{ value }">{{ formatQty(value) }}</template>
              <template #cell-reserved_qty="{ value }">{{ formatQty(value) }}</template>
              <template #cell-stock_value="{ value }">{{ formatMoney(value) }}</template>
            </ManagementSmartDataTable>
          </section>

          <section class="inventory-surface">
            <header class="inventory-surface__head">
              <div><strong>دفتر موجودی</strong><small>Stock Ledger Entry native</small></div>
              <span>{{ ledger.length.toLocaleString('fa-IR') }} گردش</span>
            </header>
            <ManagementSmartDataTable
              :columns="ledgerColumns"
              :rows="ledger"
              row-key="voucher_no"
              :show-search="true"
              :filterable="true"
              :freezable="false"
              :resizable="false"
              empty-text="در این بازه برای این کالا گردش موجودی ثبت نشده است."
            >
              <template #cell-actual_qty="{ value }">
                <span :class="Number(value) < 0 ? 'qty-negative' : 'qty-positive'">{{ formatQty(value) }}</span>
              </template>
              <template #cell-stock_value_difference="{ value }">{{ formatMoney(value) }}</template>
              <template #cell-voucher_no="{ row }">
                <a class="ledger-link" :href="voucherRoute(row)" target="_blank" rel="noreferrer" @click.stop>{{ row.voucher_no || '—' }}</a>
              </template>
            </ManagementSmartDataTable>
          </section>
        </div>

        <section class="inventory-operations">
          <header class="inventory-surface__head"><div><strong>عملیات مرتبط</strong><small>مسیرهای اجرای عملیات همچنان native هستند.</small></div></header>
          <div class="operation-links">
            <a class="operation-link" href="/management/inventory">مرکز موجودی و گردش‌ها</a>
            <a class="operation-link" href="/management/inventory/count">انبارگردانی</a>
            <a class="operation-link" href="/management/reports?report=stock-movements">گزارش گردش موجودی</a>
            <a class="operation-link" href="/management/inventory/documents">دفتر اسناد خرید و انبار</a>
          </div>
        </section>
      </template>
    </ManagementSurfaceCard>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import ManagementSmartDataTable from '@/components/management/ManagementSmartDataTable.vue'
import ManagementSurfaceCard from '@/components/management/ManagementSurfaceCard.vue'
import PersianDateInput from '@/components/PersianDateInput.vue'
import SearchableDropdown from '@/components/SearchableDropdown.vue'

const props = defineProps({
  summary: { type: Object, default: () => ({}) },
  bins: { type: Array, default: () => [] },
  ledger: { type: Array, default: () => [] },
  reorderLevels: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  error: { type: String, default: '' },
  dateRange: { type: Object, default: () => ({ date_from: '', date_to: '' }) },
  warehouse: { type: String, default: '' },
})

const emit = defineEmits(['update:dateRange', 'update:warehouse', 'refresh', 'open-ledger'])

const metrics = [
  { key: 'actual_qty', label: 'موجودی واقعی' },
  { key: 'projected_qty', label: 'موجودی پیش‌بینی‌شده' },
  { key: 'reserved_qty', label: 'رزرو شده' },
  { key: 'ordered_qty', label: 'سفارش‌شده' },
  { key: 'stock_value', label: 'ارزش موجودی', suffix: 'ریال', money: true },
]
const binColumns = [
  { key: 'warehouse', label: 'انبار' },
  { key: 'actual_qty', label: 'واقعی' },
  { key: 'projected_qty', label: 'پیش‌بینی‌شده' },
  { key: 'reserved_qty', label: 'رزرو' },
  { key: 'stock_value', label: 'ارزش' },
]
const ledgerColumns = [
  { key: 'posting_date', label: 'تاریخ' },
  { key: 'warehouse', label: 'انبار' },
  { key: 'actual_qty', label: 'تغییر مقدار' },
  { key: 'qty_after_transaction', label: 'مانده پس از سند' },
  { key: 'stock_value_difference', label: 'تغییر ارزش' },
  { key: 'voucher_no', label: 'سند' },
]
const warehouseOptions = computed(() => props.bins.map((row) => ({ value: row.warehouse, label: row.warehouse })).filter((row) => row.value))

function updateDate(key, value) {
  emit('update:dateRange', { ...props.dateRange, [key]: value })
}

function formatQty(value) {
  return new Intl.NumberFormat('fa-IR', { maximumFractionDigits: 3 }).format(Number(value || 0))
}

function formatMoney(value) {
  return `${new Intl.NumberFormat('fa-IR', { maximumFractionDigits: 0 }).format(Math.round(Number(value || 0)))} ریال`
}

function voucherRoute(row) {
  const doctype = encodeURIComponent(row?.voucher_type || '')
  const name = encodeURIComponent(row?.voucher_no || '')
  return row?.voucher_type === 'Stock Entry' ? `/management/inventory/documents/detail?doctype=${doctype}&name=${name}` : `/app/${String(row?.voucher_type || '').toLowerCase().replaceAll(' ', '-')}/${name}`
}
</script>

<style scoped>
.product-inventory-panel { min-width: 0; }
.inventory-filters { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)) auto; gap: .75rem; align-items: end; margin-bottom: 1rem; }
.inventory-filters label { display: grid; gap: .35rem; color: var(--mg-text-muted); font-size: .75rem; font-weight: 800; }
.inventory-kpis { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: .75rem; margin-bottom: 1rem; }
.inventory-kpi { display: grid; gap: .3rem; padding: .9rem; border: 1px solid var(--mg-border); border-radius: var(--mg-radius-md); background: var(--mg-bg-soft); }
.inventory-kpi small, .inventory-kpi span { color: var(--mg-text-muted); font-size: .68rem; }
.inventory-kpi strong { color: var(--mg-text-main); font-size: 1.05rem; }
.inventory-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 1rem; }
.inventory-surface, .inventory-operations { min-width: 0; border: 1px solid var(--mg-border); border-radius: var(--mg-radius-md); background: var(--mg-bg-surface); overflow: hidden; }
.inventory-surface__head { display: flex; align-items: center; justify-content: space-between; gap: .75rem; padding: .85rem 1rem; border-bottom: 1px solid var(--mg-border); }
.inventory-surface__head div { display: grid; gap: .2rem; }
.inventory-surface__head small, .inventory-surface__head > span { color: var(--mg-text-muted); font-size: .68rem; }
.qty-negative { color: var(--mg-danger); font-weight: 800; }
.qty-positive { color: var(--mg-success); font-weight: 800; }
.ledger-link { color: var(--mg-primary); font-weight: 800; }
.operation-links { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: .75rem; padding: 1rem; }
.operation-link { min-height: 46px; display: grid; place-items: center; border: 1px solid var(--mg-border); border-radius: var(--mg-radius-sm); color: var(--mg-primary); font-size: .76rem; font-weight: 800; text-align: center; }
.inventory-state { display: grid; place-items: center; gap: .75rem; min-height: 10rem; border: 1px dashed var(--mg-border); border-radius: var(--mg-radius-md); color: var(--mg-text-muted); text-align: center; }
.inventory-state--error { color: var(--mg-danger); }
@media (max-width: 1100px) { .inventory-kpis { grid-template-columns: repeat(3, minmax(0, 1fr)); } .inventory-grid { grid-template-columns: 1fr; } .operation-links { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 700px) { .inventory-filters { grid-template-columns: 1fr; } .inventory-kpis { grid-template-columns: repeat(2, minmax(0, 1fr)); } .operation-links { grid-template-columns: 1fr; } }
</style>
