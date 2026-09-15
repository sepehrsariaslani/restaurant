<template>
  <InventorySectionShell title="دفتر گردش کالا" :subtitle="itemTitle ? `گردش کامل «${itemTitle}»` : 'جستجو و بررسی گردش کالا در انبارها'">
    <template #actions>
      <a v-if="itemName" class="secondary-btn" :href="`/management/product?item_name=${encodeURIComponent(itemName)}`">بازگشت به محصول</a>
      <button class="secondary-btn" type="button" :disabled="loading" @click="loadLedger">{{ loading ? 'در حال بروزرسانی...' : 'بروزرسانی' }}</button>
    </template>

    <ManagementSurfaceCard tone="accent" class="ledger-filter-card">
      <div class="ledger-filter-grid">
        <label>
          جستجو در گردش
          <input class="input" v-model.trim="filters.search" placeholder="شماره سند، نوع سند یا انبار" @keyup.enter="loadFirstPage" />
        </label>
        <label>
          از تاریخ
          <PersianDateInput v-model="filters.date_from" />
        </label>
        <label>
          تا تاریخ
          <PersianDateInput v-model="filters.date_to" />
        </label>
        <label>
          انبار
          <SearchableDropdown
            v-model="filters.warehouse"
            :options="warehouseOptions"
            placeholder="همه انبارها"
            search-placeholder="جستجوی انبار..."
            include-empty-option
            empty-label="همه انبارها"
            :create-config="warehouseCreateConfig"
            @item-created="loadWarehouses"
          />
        </label>
        <button class="primary-btn" type="button" @click="loadFirstPage">اعمال فیلتر</button>
      </div>
    </ManagementSurfaceCard>

    <p v-if="!itemName" class="ledger-state ledger-state--error">برای نمایش دفتر گردش، ابتدا یک کالا را از صفحه محصول انتخاب کنید.</p>
    <p v-else-if="error" class="ledger-state ledger-state--error">{{ error }}</p>
    <ManagementSurfaceCard v-else title="گردش ثبت‌شده" :subtitle="`${formatNumber(totalCount)} ردیف در نتیجه فعلی`">
      <ManagementSmartDataTable
        :columns="columns"
        :rows="rows"
        row-key="ledger_key"
        :loading="loading"
        :show-search="false"
        :filterable="false"
        :freezable="false"
        :resizable="false"
        empty-text="برای این کالا در بازه انتخاب‌شده گردش ثبت نشده است."
      >
        <template #cell-posting_date="{ value }">{{ formatPersianDate(value) }}</template>
        <template #cell-posting_time="{ value }">{{ value || '—' }}</template>
        <template #cell-actual_qty="{ value }"><span :class="Number(value) < 0 ? 'qty-negative' : 'qty-positive'">{{ formatQuantity(value) }}</span></template>
        <template #cell-qty_after_transaction="{ value }">{{ formatQuantity(value) }}</template>
        <template #cell-stock_value_difference="{ value }">{{ formatMoney(value) }}</template>
        <template #cell-voucher_type="{ value }">{{ voucherTypeLabel(value) }}</template>
        <template #cell-voucher_no="{ row }">
          <a v-if="row.voucher_no" class="ledger-link" :href="voucherRoute(row)" target="_blank" rel="noreferrer" @click.stop>{{ row.voucher_no }}</a>
          <span v-else>—</span>
        </template>
      </ManagementSmartDataTable>

      <footer class="ledger-pagination" v-if="totalCount">
        <span>صفحه {{ formatNumber(pageNumber) }} از {{ formatNumber(pageCount) }}</span>
        <div>
          <button class="secondary-btn" type="button" :disabled="pageNumber <= 1 || loading" @click="goToPage(pageNumber - 1)">قبلی</button>
          <button class="secondary-btn" type="button" :disabled="pageNumber >= pageCount || loading" @click="goToPage(pageNumber + 1)">بعدی</button>
        </div>
      </footer>
    </ManagementSurfaceCard>
  </InventorySectionShell>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import PersianDateInput from '@/components/PersianDateInput.vue'
import SearchableDropdown from '@/components/SearchableDropdown.vue'
import ManagementSmartDataTable from '@/components/management/ManagementSmartDataTable.vue'
import ManagementSurfaceCard from '@/components/management/ManagementSurfaceCard.vue'
import InventorySectionShell from '@/components/management/inventory/InventorySectionShell.vue'
import { getManagementProductStockLedger, listManagementWarehouses } from '@/utils/api'
import { formatMoney, parseQuery } from '@/utils/format'
import { formatPersianDate } from '@/utils/managementProductDetail'
import { getSearchableCreateConfig } from '@/utils/managementSearchableCreate'

const query = parseQuery()
const itemName = ref(String(query.item_name || query.item || '').trim())
const itemTitle = ref(itemName.value)
const rows = ref([])
const totalCount = ref(0)
const warehouseOptions = ref([{ value: '', label: 'همه انبارها' }])
const loading = ref(false)
const error = ref('')
const pageSize = 50
const pageNumber = ref(1)
const filters = reactive({ search: '', warehouse: '', date_from: '', date_to: '' })
const columns = [
  { key: 'posting_date', label: 'تاریخ' }, { key: 'posting_time', label: 'زمان' }, { key: 'warehouse', label: 'انبار' },
  { key: 'actual_qty', label: 'تغییر مقدار' }, { key: 'qty_after_transaction', label: 'موجودی پس از گردش' },
  { key: 'stock_value_difference', label: 'تغییر ارزش' }, { key: 'voucher_type', label: 'نوع سند' }, { key: 'voucher_no', label: 'شماره سند' },
]
const warehouseCreateConfig = getSearchableCreateConfig('Warehouse')
const pageCount = computed(() => Math.max(1, Math.ceil(totalCount.value / pageSize)))

function formatNumber(value) { return Number(value || 0).toLocaleString('fa-IR') }
function formatQuantity(value) { return Number(value || 0).toLocaleString('fa-IR', { maximumFractionDigits: 3 }) }
function voucherTypeLabel(value) {
  return ({ 'Stock Entry': 'سند انبار', 'Purchase Receipt': 'رسید خرید', 'Purchase Invoice': 'فاکتور خرید', 'Delivery Note': 'حواله تحویل', 'Sales Invoice': 'فاکتور فروش', 'Stock Reconciliation': 'انبارگردانی' })[value] || (value ? 'سند مرتبط' : 'سند')
}
function voucherRoute(row) {
  const routes = { 'Stock Entry': '/management/inventory/documents', 'Purchase Receipt': '/management/inventory/documents', 'Purchase Invoice': '/management/inventory/documents', 'Stock Reconciliation': '/management/inventory/count' }
  return routes[row.voucher_type] || '/management/inventory'
}
async function loadWarehouses() {
  try {
    const payload = await listManagementWarehouses({ options_only: 1 })
    warehouseOptions.value = [{ value: '', label: 'همه انبارها' }, ...(payload?.leaf_warehouses || []).map((name) => ({ value: name, label: name }))]
  } catch (_) { /* فهرست انبار برای فیلتر اختیاری است. */ }
}
async function loadLedger() {
  if (!itemName.value) return
  loading.value = true
  error.value = ''
  try {
    const payload = await getManagementProductStockLedger({ item_name: itemName.value, ...filters, limit: pageSize, offset: (pageNumber.value - 1) * pageSize })
    itemName.value = payload?.item_name || itemName.value
    itemTitle.value = payload?.item_title || itemName.value
    rows.value = (payload?.rows || []).map((row, index) => ({ ...row, ledger_key: `${row.posting_date}-${row.posting_time}-${row.voucher_no}-${index}` }))
    totalCount.value = Number(payload?.total_count || 0)
  } catch (err) {
    error.value = err?.message || 'دریافت دفتر گردش ناموفق بود.'
    rows.value = []
    totalCount.value = 0
  } finally { loading.value = false }
}
function loadFirstPage() { pageNumber.value = 1; loadLedger() }
function goToPage(page) { pageNumber.value = Math.min(Math.max(Number(page) || 1, 1), pageCount.value); loadLedger() }

onMounted(() => { loadWarehouses(); loadLedger() })
</script>

<style scoped>
.ledger-filter-card, .ledger-filter-grid { min-width: 0; }
.ledger-filter-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)) auto; align-items: end; gap: .65rem; }
.ledger-filter-grid label { display: grid; gap: .28rem; color: var(--mg-text-muted); font-size: .76rem; font-weight: 800; min-width: 0; }
.ledger-state { padding: 1rem; border: 1px dashed var(--mg-border); border-radius: var(--mg-radius-md); text-align: center; }
.ledger-state--error { color: var(--mg-danger); }
.ledger-pagination { display: flex; justify-content: space-between; align-items: center; gap: .6rem; margin-top: .75rem; padding-top: .75rem; border-top: 1px solid var(--mg-border-light); color: var(--mg-text-muted); font-size: .76rem; }
.ledger-pagination > div { display: flex; gap: .4rem; }
.qty-negative { color: var(--mg-danger); font-weight: 800; }
.qty-positive { color: var(--mg-success); font-weight: 800; }
.ledger-link { color: var(--mg-primary); font-weight: 800; text-decoration: none; }
@media (max-width: 1000px) { .ledger-filter-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } .ledger-filter-grid > button { width: 100%; } }
@media (max-width: 560px) { .ledger-filter-grid { grid-template-columns: 1fr; } .ledger-pagination { align-items: stretch; flex-direction: column; } .ledger-pagination > div, .ledger-pagination button { width: 100%; } }
</style>
