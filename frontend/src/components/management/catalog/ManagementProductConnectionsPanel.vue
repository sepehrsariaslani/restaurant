<template>
  <section class="product-connections-panel" dir="rtl">
    <ManagementSurfaceCard title="اتصالات محصول" subtitle="اسناد native ERPNext که به این کالا متصل هستند">
      <div v-if="loading" class="connection-state">در حال دریافت اتصالات اسناد...</div>
      <div v-else-if="error" class="connection-state connection-state--error">
        <p>{{ error }}</p>
        <button type="button" class="secondary-btn" @click="$emit('retry')">تلاش دوباره</button>
      </div>
      <div v-else-if="!groups.length" class="connection-state">برای این محصول هنوز سند متصل ثبت نشده است.</div>

      <div v-else class="connection-groups">
        <section v-for="group in groups" :key="group.key" class="connection-group">
          <header class="connection-group__head">
            <div>
              <strong>{{ group.label }}</strong>
              <small>{{ group.count.toLocaleString('fa-IR') }} اتصال</small>
            </div>
            <span class="connection-count">{{ group.count.toLocaleString('fa-IR') }}</span>
          </header>

          <ManagementSmartDataTable
            :columns="columns"
            :rows="group.rows || []"
            row-key="name"
            :show-search="false"
            :filterable="false"
            :freezable="false"
            :resizable="false"
            :row-clickable="true"
            empty-text="اتصالی در این گروه وجود ندارد."
            @row-click="row => $emit('open', row)"
          >
            <template #cell-title="{ row }">
              <div class="connection-title">
                <strong>{{ row.title || row.name }}</strong>
                <small>{{ connectionTypeLabels[row.doctype] || row.doctype }}</small>
              </div>
            </template>
            <template #cell-amount="{ value }">{{ formatMoney(value) }}</template>
            <template #cell-actions="{ row }">
              <a class="secondary-btn mini-link-btn" :href="row.route" target="_blank" rel="noreferrer" @click.stop>باز کردن</a>
            </template>
          </ManagementSmartDataTable>
        </section>
      </div>
    </ManagementSurfaceCard>

    <ManagementSurfaceCard title="مرزهای داده" subtitle="این صفحه فقط نمای عملیاتی است؛ ثبت نهایی اسناد در ERPNext انجام می‌شود." tone="soft">
      <p class="connection-note">اتصالات فروش، خرید، رسید، Stock Entry، BOM و Item Price از اسناد native خوانده می‌شوند و اینجا مدل موازی ساخته نمی‌شود.</p>
    </ManagementSurfaceCard>
  </section>
</template>

<script setup>
import ManagementSmartDataTable from '@/components/management/ManagementSmartDataTable.vue'
import ManagementSurfaceCard from '@/components/management/ManagementSurfaceCard.vue'

defineProps({
  groups: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  error: { type: String, default: '' },
  itemName: { type: String, default: '' },
})

defineEmits(['retry', 'open'])

const columns = [
  { key: 'title', label: 'سند' },
  { key: 'date', label: 'تاریخ' },
  { key: 'status', label: 'وضعیت' },
  { key: 'qty', label: 'مقدار' },
  { key: 'amount', label: 'مبلغ' },
  { key: 'warehouse', label: 'انبار' },
  { key: 'actions', label: 'عملیات' },
]

const connectionTypeLabels = {
  'Sales Invoice': 'فاکتور فروش',
  'Sales Order': 'سفارش فروش',
  'Delivery Note': 'حواله تحویل',
  'Purchase Invoice': 'فاکتور خرید',
  'Purchase Receipt': 'رسید خرید',
  'Purchase Order': 'سفارش خرید',
  'Stock Entry': 'سند انبار',
  'Material Request': 'درخواست مواد',
  BOM: 'فرمول و BOM',
  'Item Price': 'قیمت کالا',
}

function formatMoney(value) {
  const amount = Number(value || 0)
  return amount ? `${new Intl.NumberFormat('fa-IR').format(Math.round(amount))} ریال` : '—'
}
</script>

<style scoped>
.product-connections-panel { display: grid; gap: 1rem; }
.connection-groups { display: grid; gap: 1rem; }
.connection-group { overflow: hidden; border: 1px solid var(--mg-border); border-radius: var(--mg-radius-md); background: var(--mg-bg-surface); }
.connection-group__head { display: flex; align-items: center; justify-content: space-between; gap: .75rem; padding: .85rem 1rem; border-bottom: 1px solid var(--mg-border); }
.connection-group__head div { display: grid; gap: .2rem; }
.connection-group__head small { color: var(--mg-text-muted); font-size: .72rem; }
.connection-count { min-width: 2rem; padding: .35rem .55rem; border-radius: 999px; background: var(--mg-bg-soft); color: var(--mg-primary); text-align: center; font-weight: 900; }
.connection-title { display: grid; gap: .2rem; }
.connection-title small { color: var(--mg-text-muted); font-size: .68rem; }
.connection-state { display: grid; place-items: center; gap: .7rem; min-height: 9rem; border: 1px dashed var(--mg-border); border-radius: var(--mg-radius-md); color: var(--mg-text-muted); text-align: center; }
.connection-state--error { color: var(--mg-danger); }
.connection-note { margin: 0; color: var(--mg-text-muted); font-size: .78rem; line-height: 1.9; }
</style>
