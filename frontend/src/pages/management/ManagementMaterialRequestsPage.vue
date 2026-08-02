<template>
  <InventorySectionShell title="درخواست مواد" subtitle="لیست نیازهای ثبت‌شده و انتقال به خرید">
    <template #actions><button type="button" class="primary-btn" @click="openDetail('new')">+ درخواست جدید</button></template>
    <ManagementSurfaceCard title="لیست درخواست‌های مواد" subtitle="برای مشاهده جزئیات هر درخواست، کارت یا ردیف را انتخاب کنید.">
      <div class="inventory-toolbar">
        <select class="input" v-model="filters.status" @change="load"><option value="">همه وضعیت‌ها</option><option value="draft">پیش‌نویس</option><option value="pending">در انتظار خرید</option><option value="ordered">خرید کامل</option><option value="cancelled">لغوشده</option></select>
        <PersianDateInput v-model="filters.date_from" placeholder="از تاریخ" @update:model-value="load" />
        <PersianDateInput v-model="filters.date_to" placeholder="تا تاریخ" @update:model-value="load" />
        <input class="input" v-model.trim="filters.search" placeholder="جستجوی شماره یا ماده..." @keyup.enter="load" />
        <button type="button" class="secondary-btn" @click="load" :disabled="loading">{{ loading ? '...' : 'جستجو' }}</button>
      </div>
      <p v-if="error" class="error">{{ error }}</p>
      <p v-if="loading" class="muted">در حال دریافت درخواست‌ها...</p>
      <InventoryResponsiveList v-else :columns="columns" :rows="requests" row-key="name" @row-click="openRow" empty-text="درخواستی ثبت نشده است.">
        <template #cell-name="{ row }"><strong>{{ row.name }}</strong><small class="sub">{{ row.transaction_date }}</small></template>
        <template #cell-status_label="{ row }"><span :class="['status-pill', statusClass(row.status)]">{{ row.status_label }}</span></template>
        <template #cell-items="{ row }">{{ qty(row.item_count) }} قلم</template>
        <template #cell-total_qty="{ value }">{{ qty(value) }}</template>
        <template #cell-schedule_date="{ value }">{{ value || '—' }}</template>
        <template #cell-purchase="{ row }">{{ row.purchase_orders?.length ? 'خرید ایجاد شده' : '—' }}</template>
        <template #card="{ row }"><div class="card-head"><strong>{{ row.name }}</strong><span :class="['status-pill', statusClass(row.status)]">{{ row.status_label }}</span></div><small class="sub">درخواست: {{ row.transaction_date }} • نیاز: {{ row.schedule_date || '—' }}</small><div class="card-meta"><span>{{ qty(row.item_count) }} قلم • {{ qty(row.total_qty) }} مقدار</span><span>{{ row.set_warehouse || 'همه انبارها' }}</span></div><small class="sub">{{ row.purchase_orders?.length ? 'پیش‌نویس خرید متصل دارد' : 'برای جزئیات لمس کنید' }}</small></template>
      </InventoryResponsiveList>
    </ManagementSurfaceCard>
  </InventorySectionShell>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import InventoryResponsiveList from '@/components/management/inventory/InventoryResponsiveList.vue'
import InventorySectionShell from '@/components/management/inventory/InventorySectionShell.vue'
import ManagementSurfaceCard from '@/components/management/ManagementSurfaceCard.vue'
import PersianDateInput from '@/components/PersianDateInput.vue'
import { listManagementMaterialRequests } from '@/utils/api'

const requests = ref([])
const loading = ref(false)
const error = ref('')
const filters = reactive({ status: '', search: '', date_from: '', date_to: '' })
const columns = [
  { key: 'name', label: 'شماره' },
  { key: 'status_label', label: 'وضعیت' },
  { key: 'items', label: 'اقلام' },
  { key: 'total_qty', label: 'مقدار' },
  { key: 'schedule_date', label: 'تاریخ نیاز' },
  { key: 'purchase', label: 'خرید' },
]
function qty(value) { return Number(value || 0).toLocaleString('fa-IR', { maximumFractionDigits: 3 }) }
function statusClass(status) { return ['ordered', 'partially ordered'].includes(String(status || '').toLowerCase()) ? 'ok' : ['cancelled', 'stopped'].includes(String(status || '').toLowerCase()) ? 'danger' : '' }
function openDetail(name) { window.location.href = name === 'new' ? '/management/inventory/requests/detail?new=1' : `/management/inventory/requests/detail?name=${encodeURIComponent(name.name || name)}` }
function openRow(row) { openDetail(row.name) }
async function load() { loading.value = true; error.value = ''; try { const payload = await listManagementMaterialRequests({ ...filters, limit: 200 }); requests.value = payload.requests || [] } catch (err) { error.value = err.message || 'دریافت درخواست‌ها ناموفق بود.' } finally { loading.value = false } }
onMounted(load)
</script>

<style scoped>
.inventory-toolbar { display: flex; flex-wrap: wrap; gap: 0.5rem; align-items: center; margin-bottom: 0.8rem; }
.inventory-toolbar .input, .inventory-toolbar :deep(.persian-date-input) { flex: 1 1 150px; min-width: 145px; }
.sub { display: block; margin-top: 0.15rem; color: var(--mg-text-muted); font-size: 0.68rem; }
.card-head, .card-meta { display: flex; justify-content: space-between; gap: 0.5rem; align-items: center; }
.card-meta { margin-top: 0.5rem; color: var(--mg-text-muted); font-size: 0.73rem; }
.status-pill { display: inline-flex; padding: 0.18rem 0.5rem; border-radius: 999px; background: color-mix(in srgb, var(--mg-primary) 11%, transparent); color: var(--mg-primary); font-size: 0.68rem; font-weight: 800; white-space: nowrap; }
.status-pill.ok { background: color-mix(in srgb, var(--mg-success) 13%, transparent); color: var(--mg-success); }
.status-pill.danger { background: color-mix(in srgb, var(--mg-danger) 12%, transparent); color: var(--mg-danger); }
.error { color: var(--mg-danger); }
@media (max-width: 650px) { .inventory-toolbar { display: grid; grid-template-columns: 1fr; } .inventory-toolbar .input, .inventory-toolbar :deep(.persian-date-input) { width: 100%; min-width: 0; } }
</style>
