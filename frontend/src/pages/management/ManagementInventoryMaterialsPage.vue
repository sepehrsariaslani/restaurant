<template>
  <InventorySectionShell title="مواد اولیه" subtitle="فهرست مواد، واحد اندازه‌گیری، موجودی و تأمین‌کننده">
    <template #actions>
      <button type="button" class="primary-btn" @click="openDetail('')">+ ماده اولیه جدید</button>
    </template>
    <ManagementSurfaceCard title="لیست مواد اولیه" subtitle="برای مشاهده و ویرایش جزئیات، ردیف یا کارت را انتخاب کنید.">
      <div class="inventory-toolbar">
        <input class="input" v-model.trim="search" placeholder="جستجوی نام یا کد ماده..." @keyup.enter="load" />
        <label class="check"><input v-model="includeInactive" type="checkbox" @change="load" /> نمایش غیرفعال‌ها</label>
        <button type="button" class="secondary-btn" @click="load" :disabled="loading">{{ loading ? '...' : 'جستجو' }}</button>
      </div>
      <p v-if="error" class="error">{{ error }}</p>
      <p v-if="loading" class="muted">در حال دریافت مواد اولیه...</p>
      <InventoryResponsiveList
        v-else
        :columns="columns"
        :rows="materials"
        row-key="name"
        @row-click="openRow"
        empty-text="ماده اولیه‌ای ثبت نشده است."
      >
        <template #cell-name="{ row }"><strong>{{ row.item_name }}</strong><small class="sub">{{ row.name }}</small></template>
        <template #cell-item_group="{ value }">{{ value || '—' }}</template>
        <template #cell-stock="{ row }">{{ qty(row.qty) }} {{ row.stock_uom }}</template>
        <template #cell-purchase_rate="{ value }">{{ money(value) }}</template>
        <template #cell-default_supplier="{ value }">{{ value || '—' }}</template>
        <template #card="{ row }">
          <div class="card-head"><strong>{{ row.item_name }}</strong><span v-if="row.below_reorder" class="warning-pill">کمبود</span></div>
          <small class="sub">{{ row.name }} • {{ row.item_group || 'بدون گروه' }}</small>
          <div class="card-meta"><span>{{ qty(row.qty) }} {{ row.stock_uom }}</span><span>{{ money(row.purchase_rate) }}</span></div>
          <small class="sub">تأمین‌کننده: {{ row.default_supplier || 'ثبت نشده' }}</small>
        </template>
      </InventoryResponsiveList>
    </ManagementSurfaceCard>
  </InventorySectionShell>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import InventoryResponsiveList from '@/components/management/inventory/InventoryResponsiveList.vue'
import InventorySectionShell from '@/components/management/inventory/InventorySectionShell.vue'
import ManagementSurfaceCard from '@/components/management/ManagementSurfaceCard.vue'
import { listManagementRawMaterials } from '@/utils/api'
import { formatMoney } from '@/utils/format'

const materials = ref([])
const search = ref('')
const includeInactive = ref(false)
const loading = ref(false)
const error = ref('')
const columns = [
  { key: 'name', label: 'ماده اولیه' },
  { key: 'item_group', label: 'گروه' },
  { key: 'stock', label: 'موجودی' },
  { key: 'purchase_rate', label: 'نرخ خرید' },
  { key: 'default_supplier', label: 'تأمین‌کننده' },
]
function qty(value) { return Number(value || 0).toLocaleString('fa-IR', { maximumFractionDigits: 3 }) }
function money(value) { return formatMoney(Number(value || 0), 'IRR') }
function openDetail(name) { window.location.href = name ? `/management/inventory/materials/detail?item=${encodeURIComponent(name)}` : '/management/inventory/materials/detail?new=1' }
function openRow(row) { openDetail(row.name) }
async function load() {
  loading.value = true; error.value = ''
  try {
    const payload = await listManagementRawMaterials({ search: search.value, include_inactive: includeInactive.value ? 1 : 0, limit: 200 })
    materials.value = payload.items || []
  } catch (err) { error.value = err.message || 'دریافت مواد اولیه ناموفق بود.' }
  finally { loading.value = false }
}
onMounted(load)
</script>

<style scoped>
.inventory-toolbar { display: flex; flex-wrap: wrap; align-items: center; gap: 0.55rem; margin-bottom: 0.8rem; }
.inventory-toolbar .input { width: auto; min-width: 210px; flex: 1 1 220px; }
.check { display: inline-flex; align-items: center; gap: 0.3rem; color: var(--mg-text-muted); font-size: 0.76rem; }
.sub { display: block; margin-top: 0.16rem; color: var(--mg-text-muted); font-size: 0.68rem; }
.card-head, .card-meta { display: flex; align-items: center; justify-content: space-between; gap: 0.5rem; }
.card-meta { margin-top: 0.5rem; color: var(--mg-text-muted); font-size: 0.75rem; }
.warning-pill { padding: 0.15rem 0.45rem; border-radius: 999px; color: var(--mg-danger); background: color-mix(in srgb, var(--mg-danger) 12%, transparent); font-size: 0.65rem; }
.error { color: var(--mg-danger); }
@media (max-width: 600px) { .inventory-toolbar { display: grid; grid-template-columns: 1fr; } .inventory-toolbar .input { width: 100%; min-width: 0; } }
</style>
