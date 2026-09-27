<template>
  <section class="order-flow-page order-flow-page--mobile-cta">
    <header class="order-flow-hero"><div><p class="order-flow-eyebrow">کنار هم، سر یک میز</p><h1 class="order-flow-title">برای کدام میز سفارش می‌دهید؟</h1><p class="order-flow-subtitle">اگر در رستوران هستید میز خود را انتخاب کنید. برای مراجعهٔ بعدی، میز رزرو کنید.</p></div><a class="order-flow-secondary" href="/order/type">تغییر روش دریافت</a></header>
    <a class="dine-reservation-link" href="/table-reservation"><CalendarDays :size="24" /><span><strong>برای بعد میز می‌خواهم</strong><small>روز، ساعت و تعداد نفرات را انتخاب کنید</small></span><ChevronLeft :size="20" /></a>
    <div class="order-flow-layout">
      <main class="order-flow-list">
        <p v-if="loading" class="order-flow-alert" role="status">در حال دریافت میزها…</p>
        <p v-if="error" class="order-flow-alert danger" role="alert">{{ error }} <button class="order-flow-secondary" @click="load">تلاش دوباره</button></p>
        <section class="order-flow-card">
          <h2>الان در رستوران هستم</h2>
          <p>QR روی میز، میز شما را مستقیم انتخاب می‌کند. انتخاب دستی هم از فهرست زیر ممکن است.</p>
          <label v-if="branches.length > 1" class="order-flow-field"><span>شعبه</span><select class="order-flow-select" v-model="branch"><option value="">انتخاب شعبه</option><option v-for="row in branches" :key="row.id" :value="row.id">{{ row.title || row.name }}</option></select></label>
          <p v-else-if="branches.length">{{ branches[0].title || branches[0].name }}</p>
          <div v-for="area in areas" :key="area" class="dine-area"><h3>{{ customerTableAreaLabel(area) }}</h3><div class="dine-table-grid">
            <button v-for="row in tables.filter(t => t.branch === area)" :key="row.id" type="button" :disabled="row.status === 'reserved' && selectedTableId !== row.id" :aria-pressed="selectedTableId === row.id" :class="{ active: selectedTableId === row.id }" @click="selectedTableId = row.id"><Armchair :size="21" /><strong>میز {{ row.label }}</strong><small>{{ row.status === 'reserved' ? 'رزروشده' : 'انتخاب این میز' }}</small></button>
          </div></div>
          <p v-if="!loading && !error && !tables.length" class="order-flow-alert">میزی برای سفارش آنلاین ثبت نشده است؛ از کارکنان رستوران کمک بگیرید.</p>
        </section>
      </main>
      <OrderContextSummary :next-step="nextStep" :currency="currency"><button class="order-flow-primary" :disabled="!canContinue" @click="continueToMenu">{{ continueLabel }}</button></OrderContextSummary>
    </div>
    <div class="order-mobile-cta" role="region" aria-label="ادامه سفارش سر میز"><div><small>سفارش سر میز</small><strong>{{ selectedTable ? `میز ${selectedTable.label}` : 'میز خود را انتخاب کنید' }}</strong></div><button class="order-flow-primary" type="button" :disabled="!canContinue" @click="continueToMenu">{{ continueLabel }}</button></div>
  </section>
</template>
<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { Armchair, CalendarDays, ChevronLeft } from 'lucide-vue-next'
import OrderContextSummary from '@/components/OrderContextSummary.vue'
import { cartState, saveOrderContext } from '@/stores/cartStore'
import { consumeNutritionScheduleReturn } from '@/utils/orderFlow'
import { isCustomerCompany } from '@/utils/orderBranches'
import { getAvailableTables, getBranches, getMenuBoot } from '@/utils/api'
import { customerTableAreaLabel } from '@/utils/customerTableAreas'
import './orderFlow.css'
const query = new URLSearchParams(window.location.search)
const branches = ref([]), tables = ref([]), loading = ref(true), error = ref(''), currency = ref('IRR')
const branch = ref(query.get('branch') || cartState.orderContext.branch || '')
const selectedTableId = ref(query.get('table') || query.get('table_no') || cartState.orderContext.table || window._BOOT?.table_context?.table?.name || '')
const selectedTable = computed(() => tables.value.find(t => t.id === selectedTableId.value || t.label === selectedTableId.value))
const areas = computed(() => [...new Set(tables.value.map(t => t.branch || ''))])
const canContinue = computed(() => Boolean(branch.value && selectedTable.value && !loading.value && !error.value))
const continueLabel = computed(() => cartState.lines.length ? 'تکمیل سفارش' : 'انتخاب غذا')
const nextStep = computed(() => cartState.lines.length ? 'تکمیل سفارش' : 'مشاهده منو')
function persist() {
  saveOrderContext({ order_type: 'dine_in', branch: branch.value, branch_title: branches.value.find(b => b.id === branch.value)?.title || branch.value, table: selectedTable.value?.id || '', table_title: selectedTable.value ? `میز ${selectedTable.value.label}` : '', delivery_fee: 0, address: null, pickup_vehicle: null, courier_note: '' })
}
watch([branch, selectedTable], persist)
async function load() {
  loading.value = true; error.value = ''
  try {
    const [places, seats, boot] = await Promise.all([getBranches(), getAvailableTables(), getMenuBoot('')])
    branches.value = (places.branches || []).filter(isCustomerCompany)
    if (!branches.value.some(b => b.id === branch.value)) branch.value = branches.value.length === 1 ? branches.value[0].id : ''
    tables.value = seats.tables || []; currency.value = boot.currency || 'IRR'
    persist()
  } catch (err) { error.value = err.message || 'دریافت میزها ناموفق بود.' }
  finally { loading.value = false }
}
function continueToMenu() { if (!canContinue.value) return; persist(); window.location.href = cartState.lines.length ? (consumeNutritionScheduleReturn() || '/checkout') : `/menu?branch=${encodeURIComponent(branch.value)}&table=${encodeURIComponent(selectedTable.value.id)}&order_type=dine_in` }
onMounted(load)
</script>
<style scoped>
.dine-reservation-link { display: flex; align-items: center; gap: 1rem; padding: 1rem 1.2rem; border-radius: var(--ds-radius-md); border: 1px solid var(--ds-color-border); background: var(--ds-color-action-primary-soft); color: var(--ds-color-action-primary); margin-bottom: 1rem; text-decoration: none; }
.dine-reservation-link span { display: grid; gap: .35rem; flex: 1; }
.dine-reservation-link small { color: var(--ds-color-text-secondary); }
.dine-area { margin-top: 1.5rem; }
.dine-area h3 { font-size: .95rem; margin-bottom: .7rem; }
.dine-table-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(110px, 1fr)); gap: .75rem; }
.dine-table-grid button { display: grid; justify-items: center; gap: .5rem; padding: 1rem .5rem; border: 1px solid var(--ds-color-border); border-radius: var(--ds-radius-md); color: var(--ds-color-text-secondary); background: var(--ds-color-surface-raised); font: inherit; cursor: pointer; }
.dine-table-grid button.active { background: var(--ds-color-action-primary-soft); border-color: var(--ds-color-action-primary); color: var(--ds-color-action-primary); }
.dine-table-grid button:disabled { opacity: .5; cursor: default; }
.dine-table-grid small { font-size: .75rem; }
</style>
