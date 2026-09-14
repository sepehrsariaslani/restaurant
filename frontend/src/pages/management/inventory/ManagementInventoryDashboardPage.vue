<template>
  <InventorySectionShell title="موجودی و ارزش" subtitle="نمایش سریع موجودی مقداری و ارزش ریالی انبارها">
    <template #actions>
      <button type="button" class="secondary-btn" @click="loadAll" :disabled="loading">{{ loading ? 'در حال بروزرسانی...' : 'بروزرسانی' }}</button>
    </template>

    <p v-if="error" class="error">{{ error }}</p>
    <section v-if="boot" class="inventory-kpis">
      <article><small>مواد اولیه</small><strong>{{ fa(boot.kpis?.materials_total) }}</strong></article>
      <article><small>انبارها</small><strong>{{ fa(boot.kpis?.warehouses_total) }}</strong></article>
      <article :class="{ warning: Number(boot.kpis?.below_reorder || 0) > 0 }"><small>زیر نقطه سفارش</small><strong>{{ fa(boot.kpis?.below_reorder) }}</strong></article>
      <article><small>ارزش موجودی</small><strong>{{ money(boot.kpis?.stock_value_total) }}</strong></article>
      <article><small>خریدهای باز</small><strong>{{ fa(boot.kpis?.open_purchase_orders) }}</strong></article>
    </section>

    <ManagementSurfaceCard title="موجودی لحظه‌ای" subtitle="برای مشاهده جزئیات ماده، ردیف را انتخاب کنید.">
      <div class="inventory-toolbar">
        <select class="input" v-model="filters.warehouse" @change="loadOverview">
          <option value="">همه انبارها</option>
          <option v-for="warehouse in boot?.leaf_warehouses || []" :key="warehouse" :value="warehouse">{{ warehouse }}</option>
        </select>
        <input class="input" v-model.trim="filters.search" placeholder="جستجوی کالا یا کد..." @keyup.enter="loadOverview" />
        <label class="check"><input v-model="filters.only_materials" type="checkbox" @change="loadOverview" /> فقط مواد اولیه</label>
        <button type="button" class="secondary-btn" @click="loadOverview">جستجو</button>
      </div>
      <p v-if="overviewLoading" class="muted">در حال دریافت موجودی...</p>
      <InventoryResponsiveList
        v-else
        :columns="columns"
        :rows="overviewRows"
        row-key="item_code"
        :row-clickable="false"
        empty-text="موجودی برای نمایش وجود ندارد."
      >
        <template #cell-item_name="{ row }"><strong>{{ row.item_name }}</strong><small class="sub">{{ row.item_code }}</small></template>
        <template #cell-qty="{ row }">{{ moneyNumber(row.qty) }} {{ row.stock_uom }}</template>
        <template #cell-rate="{ value }">{{ money(value) }}</template>
        <template #cell-value="{ value }"><strong>{{ money(value) }}</strong></template>
        <template #cell-warehouse_count="{ row }">{{ fa(Object.keys(row.warehouses || {}).length || 1) }}</template>
        <template #card="{ row }">
          <div class="inventory-card-head"><strong>{{ row.item_name }}</strong><span>{{ money(row.value) }}</span></div>
          <small class="sub">{{ row.item_code }}</small>
          <div class="inventory-card-meta"><span>{{ moneyNumber(row.qty) }} {{ row.stock_uom }}</span><span>{{ money(row.rate) }}</span></div>
        </template>
      </InventoryResponsiveList>
    </ManagementSurfaceCard>
  </InventorySectionShell>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import InventoryResponsiveList from '@/components/management/inventory/InventoryResponsiveList.vue'
import InventorySectionShell from '@/components/management/inventory/InventorySectionShell.vue'
import ManagementSurfaceCard from '@/components/management/ManagementSurfaceCard.vue'
import { getManagementInventoryBoot, getManagementStockOverview } from '@/utils/api'
import { formatMoney } from '@/utils/format'

const boot = ref(null)
const overview = ref(null)
const loading = ref(false)
const overviewLoading = ref(false)
const error = ref('')
const filters = reactive({ warehouse: '', search: '', only_materials: false })
const columns = [
  { key: 'item_name', label: 'کالا' },
  { key: 'warehouse_count', label: 'انبارها' },
  { key: 'qty', label: 'موجودی' },
  { key: 'rate', label: 'نرخ' },
  { key: 'value', label: 'ارزش' },
]

const overviewRows = computed(() => overview.value?.items || [])

function fa(value) {
  return Number(value || 0).toLocaleString('fa-IR')
}
function moneyNumber(value) {
  return Number(value || 0).toLocaleString('fa-IR', { maximumFractionDigits: 3 })
}
function money(value) {
  return formatMoney(Number(value || 0), 'IRR')
}

async function loadBoot() {
  boot.value = await getManagementInventoryBoot()
}
async function loadOverview() {
  overviewLoading.value = true
  try {
    overview.value = await getManagementStockOverview({
      warehouse: filters.warehouse,
      search: filters.search,
      only_materials: filters.only_materials ? 1 : 0,
    })
  } finally {
    overviewLoading.value = false
  }
}
async function loadAll() {
  loading.value = true
  error.value = ''
  try {
    await Promise.all([loadBoot(), loadOverview()])
  } catch (err) {
    error.value = err.message || 'دریافت اطلاعات انبار ناموفق بود.'
  } finally {
    loading.value = false
  }
}

onMounted(loadAll)
</script>

<style scoped>
.inventory-kpis {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(145px, 1fr));
  gap: 0.6rem;
}
.inventory-kpis article {
  display: grid;
  gap: 0.2rem;
  padding: 0.75rem;
  border: 1px solid var(--mg-border-light);
  border-radius: 15px;
  background: var(--mg-bg-surface);
}
.inventory-kpis article.warning { border-color: color-mix(in srgb, var(--mg-danger) 45%, transparent); }
.inventory-kpis small, .sub { color: var(--mg-text-muted); font-size: 0.72rem; }
.inventory-kpis strong { color: var(--mg-primary); font-size: 1.05rem; }
.inventory-toolbar { display: flex; flex-wrap: wrap; align-items: center; gap: 0.5rem; margin-bottom: 0.8rem; }
.inventory-toolbar .input { width: auto; min-width: 160px; flex: 1 1 160px; }
.check { display: inline-flex; align-items: center; gap: 0.3rem; color: var(--mg-text-muted); font-size: 0.75rem; }
.inventory-card-head, .inventory-card-meta { display: flex; justify-content: space-between; gap: 0.5rem; }
.inventory-card-head span { color: var(--mg-success); font-weight: 800; }
.inventory-card-meta { margin-top: 0.45rem; color: var(--mg-text-muted); font-size: 0.75rem; }
.error { color: var(--mg-danger); }
@media (max-width: 600px) { .inventory-toolbar { display: grid; grid-template-columns: 1fr; } .inventory-toolbar .input { width: 100%; } }
</style>
