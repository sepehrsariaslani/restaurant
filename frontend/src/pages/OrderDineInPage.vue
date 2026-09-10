<template>
  <section class="order-flow-page">
    <header class="order-flow-hero">
      <div>
        <p class="order-flow-eyebrow">سفارش حضوری داخل سالن</p>
        <h1 class="order-flow-title">{{ tableContext ? `سفارش برای میز ${tableLabel}` : 'برای سفارش حضوری میز را مشخص کنید' }}</h1>
        <p class="order-flow-subtitle">سفارش حضوری به شرکت و میز متصل می‌شود و آدرس، پیک یا هزینه ارسال ندارد.</p>
      </div>
      <a class="order-flow-secondary" href="/order/type">تغییر نوع سفارش</a>
    </header>

    <div class="order-flow-layout">
      <main class="order-flow-list">
        <section class="order-flow-card" v-if="tableContext">
          <div class="order-flow-card-head">
            <div>
              <h2>سفارش برای میز {{ tableLabel }}</h2>
              <p>{{ branchTitle || 'شرکت از QR میز خوانده شد.' }}</p>
            </div>
            <span class="order-flow-pill">حضوری</span>
          </div>
          <div class="order-flow-facts">
            <div class="order-flow-fact"><small>شرکت</small><strong>{{ branchTitle || branch || 'نامشخص' }}</strong></div>
            <div class="order-flow-fact"><small>میز</small><strong>{{ tableLabel }}</strong></div>
          </div>
        </section>

        <section class="order-flow-card" v-else>
          <h2>اسکن QR میز پیشنهاد می‌شود</h2>
          <p>برای اینکه سفارش دقیقاً به میز شما وصل شود، QR روی میز را اسکن کنید. اگر انتخاب دستی میز فعال باشد، می‌توانید شرکت و شماره میز را وارد کنید.</p>
          <p v-if="loading" class="order-flow-alert">در حال دریافت شرکت‌ها...</p>
          <p v-if="error" class="order-flow-alert danger">{{ error }}</p>
          <div class="order-flow-form" v-if="branches.length">
            <label class="order-flow-field">
              <span>شرکت</span>
              <select class="order-flow-select" v-model="branch">
                <option value="">انتخاب شرکت</option>
                <option v-for="row in branches" :key="row.id" :value="row.id">{{ row.title || row.name }}</option>
              </select>
            </label>
            <label class="order-flow-field">
              <span>شماره میز</span>
              <input class="order-flow-input" v-model="table" placeholder="مثلاً ۱۲" />
            </label>
          </div>
        </section>

        <section class="order-flow-card">
          <h2>وضعیت‌های پیگیری سفارش حضوری</h2>
          <div class="order-flow-steps">
            <span v-for="status in statuses" :key="status" class="order-flow-step active">{{ status }}</span>
          </div>
        </section>
      </main>

      <OrderContextSummary :next-step="nextStep" :currency="currency">
        <button class="order-flow-primary" type="button" :disabled="!canContinue" @click="continueToMenu">{{ continueLabel }}</button>
        <p class="order-flow-alert" v-if="!canContinue">اگر QR میز ندارید، شرکت و شماره میز را وارد کنید یا از کارکنان رستوران کمک بگیرید.</p>
      </OrderContextSummary>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import OrderContextSummary from '@/components/OrderContextSummary.vue'
import { cartState, saveOrderContext } from '@/stores/cartStore'
import { getBranches, getMenuBoot } from '@/utils/api'
import './orderFlow.css'

const query = new URLSearchParams(window.location.search || '')
const branches = ref([])
const loading = ref(false)
const error = ref('')
const currency = ref('IRR')
const branch = ref(query.get('branch') || cartState.orderContext.branch || window._BOOT?.table_context?.table?.branch || '')
const branchTitle = ref(query.get('branch_title') || cartState.orderContext.branch_title || '')
const table = ref(query.get('table') || query.get('table_no') || cartState.orderContext.table || window._BOOT?.table_context?.table?.name || '')
const statuses = ['ثبت شد', 'تایید شد', 'در حال آماده‌سازی', 'آماده سرو', 'سرو شد']

const tableContext = computed(() => Boolean((query.get('branch') || query.get('table') || query.get('table_no') || window._BOOT?.table_context?.table) && branch.value && table.value))
const tableLabel = computed(() => table.value || '-')
const canContinue = computed(() => Boolean(branch.value && table.value))
const hasCartLines = computed(() => cartState.lines.length > 0)
const continueLabel = computed(() => hasCartLines.value ? 'ادامه به تکمیل سفارش' : 'مشاهده منو')
const nextStep = computed(() => hasCartLines.value ? 'تکمیل سفارش' : 'مشاهده منو و انتخاب غذا')

watch([branch, table, branchTitle], () => {
  const selected = branches.value.find((row) => row.id === branch.value || row.name === branch.value)
  saveOrderContext({
    order_type: 'dine_in',
    branch: branch.value,
    branch_title: branchTitle.value || selected?.title || selected?.name || branch.value,
    table: table.value,
    table_title: table.value ? `میز ${table.value}` : '',
    delivery_fee: 0,
    address: null,
    courier_note: '',
  })
})

async function loadBranches() {
  loading.value = true
  try {
    const [branchPayload, boot] = await Promise.all([getBranches(), getMenuBoot('')])
    branches.value = Array.isArray(branchPayload?.branches) ? branchPayload.branches : []
    currency.value = boot?.currency || 'IRR'
    const selected = branches.value.find((row) => row.id === branch.value || row.name === branch.value)
    if (selected && !branchTitle.value) branchTitle.value = selected.title || selected.name
  } catch (err) {
    error.value = err.message || 'دریافت شرکت‌ها ناموفق بود.'
  } finally {
    loading.value = false
  }
}

function continueToMenu() {
  if (!canContinue.value) return
  if (hasCartLines.value) {
    window.location.href = '/checkout'
    return
  }
  window.location.href = `/menu?branch=${encodeURIComponent(branch.value)}&table=${encodeURIComponent(table.value)}&order_type=dine_in`
}

onMounted(() => {
  saveOrderContext({ order_type: 'dine_in', delivery_fee: 0, address: null, courier_note: '' })
  loadBranches()
})
</script>
