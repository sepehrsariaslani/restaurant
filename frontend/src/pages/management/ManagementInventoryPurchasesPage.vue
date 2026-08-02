<template>
  <InventorySectionShell title="خرید مواد" subtitle="سفارش خرید، ارسال به تأمین‌کننده و دریافت مرحله‌ای">
    <template #actions><button type="button" class="primary-btn" @click="openNew">+ سفارش خرید جدید</button></template>
    <ManagementSurfaceCard title="لیست سفارش‌های خرید" subtitle="برای مشاهده اقلام و ثبت دریافت، یک سفارش را انتخاب کنید.">
      <div class="inventory-toolbar"><select class="input" v-model="filters.status" @change="load"><option value="">همه وضعیت‌ها</option><option v-for="status in statuses" :key="status" :value="status">{{ status }}</option></select><input class="input" v-model.trim="filters.search" placeholder="شماره یا تأمین‌کننده..." @keyup.enter="load" /><button type="button" class="secondary-btn" @click="load" :disabled="loading">{{ loading ? '...' : 'جستجو' }}</button></div>
      <p v-if="error" class="error">{{ error }}</p><p v-if="loading" class="muted">در حال دریافت سفارش‌های خرید...</p>
      <InventoryResponsiveList v-else :columns="columns" :rows="orders" row-key="name" @row-click="openRow" empty-text="سفارش خریدی ثبت نشده است.">
        <template #cell-name="{ row }"><strong>{{ row.name }}</strong><small class="sub">{{ row.posting_date }}</small></template>
        <template #cell-status="{ value }"><span :class="['status-pill', statusClass(value)]">{{ value }}</span></template>
        <template #cell-supplier_name="{ value }">{{ value || '—' }}</template>
        <template #cell-total_qty="{ value }">{{ qty(value) }}</template>
        <template #cell-grand_total="{ value }">{{ money(value) }}</template>
        <template #card="{ row }"><div class="card-head"><strong>{{ row.name }}</strong><span :class="['status-pill', statusClass(row.status)]">{{ row.status }}</span></div><small class="sub">{{ row.supplier_name || 'بدون تأمین‌کننده' }} • {{ row.posting_date }}</small><div class="card-meta"><span>{{ qty(row.total_qty) }} قلم</span><strong>{{ money(row.grand_total) }}</strong></div></template>
      </InventoryResponsiveList>
    </ManagementSurfaceCard>
  </InventorySectionShell>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import InventoryResponsiveList from '@/components/management/inventory/InventoryResponsiveList.vue'
import InventorySectionShell from '@/components/management/inventory/InventorySectionShell.vue'
import ManagementSurfaceCard from '@/components/management/ManagementSurfaceCard.vue'
import { listManagementPurchaseOrders } from '@/utils/api'
import { formatMoney } from '@/utils/format'
const orders=ref([]), loading=ref(false), error=ref(''), filters=reactive({status:'',search:''})
const statuses=['پیش‌نویس','ارسال‌شده','دریافت جزئی','دریافت کامل','لغوشده']
const columns=[{key:'name',label:'شماره'},{key:'supplier_name',label:'تأمین‌کننده'},{key:'posting_date',label:'تاریخ'},{key:'status',label:'وضعیت'},{key:'total_qty',label:'تعداد'},{key:'grand_total',label:'مبلغ'}]
function qty(v){return Number(v||0).toLocaleString('fa-IR',{maximumFractionDigits:3})};function money(v){return formatMoney(Number(v||0),'IRR')};function statusClass(v){return v==='دریافت کامل'?'ok':v==='لغوشده'?'danger':''}
function openNew(){window.location.href='/management/inventory/purchases/detail?new=1'}
function openRow(row){window.location.href=`/management/inventory/purchases/detail?name=${encodeURIComponent(row.name)}`}
async function load(){loading.value=true;error.value='';try{const p=await listManagementPurchaseOrders({...filters,limit:200});orders.value=p.orders||[]}catch(e){error.value=e.message||'دریافت سفارش‌های خرید ناموفق بود.'}finally{loading.value=false}}
onMounted(load)
</script>

<style scoped>
.inventory-toolbar{display:flex;flex-wrap:wrap;gap:.5rem;margin-bottom:.8rem}.inventory-toolbar .input{width:auto;min-width:190px;flex:1 1 190px}.sub{display:block;color:var(--mg-text-muted);font-size:.68rem;margin-top:.15rem}.card-head,.card-meta{display:flex;justify-content:space-between;gap:.5rem;align-items:center}.card-meta{margin-top:.5rem;color:var(--mg-text-muted);font-size:.74rem}.status-pill{display:inline-flex;padding:.18rem .5rem;border-radius:999px;background:color-mix(in srgb,var(--mg-primary) 11%,transparent);color:var(--mg-primary);font-size:.68rem;font-weight:800}.status-pill.ok{background:color-mix(in srgb,var(--mg-success) 13%,transparent);color:var(--mg-success)}.status-pill.danger{background:color-mix(in srgb,var(--mg-danger) 12%,transparent);color:var(--mg-danger)}.error{color:var(--mg-danger)}
@media(max-width:620px){.inventory-toolbar{display:grid;grid-template-columns:1fr}.inventory-toolbar .input{width:100%;min-width:0}}
</style>
