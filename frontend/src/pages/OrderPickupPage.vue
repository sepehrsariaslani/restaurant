<template>
  <section class="order-flow-page order-flow-page--pickup">
    <header class="order-flow-hero">
      <div>
        <p class="order-flow-eyebrow">بیرون‌بر / تحویل توسط مشتری</p>
        <h1 class="order-flow-title">از کدام شرکت تحویل می‌گیرید؟</h1>
        <p class="order-flow-subtitle">شما سفارش را از شرکت انتخاب‌شده تحویل می‌گیرید. هزینه ارسال برای سفارش بیرون‌بر محاسبه نمی‌شود.</p>
      </div>
      <a class="order-flow-secondary" href="/order/type">تغییر نوع سفارش</a>
    </header>

    <div class="order-flow-layout">
      <main class="order-flow-list">
        <p v-if="loading" class="order-flow-alert">در حال دریافت شرکت‌ها...</p>
        <p v-if="error" class="order-flow-alert danger">{{ error }}</p>
        <p v-if="!loading && !error && !branches.length" class="order-flow-alert">فعلاً شرکتِ باز و فعالی برای تحویل حضوری در دسترس نیست.</p>

        <button
          v-for="branch in branches"
          :key="branch.id || branch.name"
          type="button"
          class="order-flow-branch-card"
          :class="{ active: selectedBranchId === branchKey(branch) }"
          @click="selectBranch(branch)"
        >
          <div class="order-flow-card-head">
            <div>
              <h3>{{ branch.title || branch.name }}</h3>
              <p>{{ branch.address || 'آدرس شرکت ثبت نشده است.' }}</p>
            </div>
            <span class="order-flow-pill" :class="branch.isOpen ? '' : 'warning'">{{ branch.open_label || (branch.isOpen ? 'باز' : 'بسته') }}</span>
          </div>
          <div class="order-flow-branch-meta">
            <span class="order-flow-pill">آماده‌سازی حدود {{ branch.prepTime || branch.prep_time_mins || 20 }} دقیقه</span>
            <span class="order-flow-pill">بدون هزینه ارسال</span>
            <span class="order-flow-pill" :class="branch.pickup_available === false ? 'warning' : ''">{{ branch.pickup_available === false ? 'فعلاً پیکاپ ندارد' : 'پیکاپ فعال' }}</span>
          </div>
          <span class="order-flow-primary">تحویل از این شرکت</span>
        </button>

        <section class="order-flow-card" v-if="selectedBranch">
          <h2>زمان تحویل</h2>
          <p>زمان آماده‌سازی تقریبی بر اساس برنامه شرکت انتخاب‌شده نمایش داده می‌شود.</p>
          <div class="order-flow-segmented" style="margin-top:.8rem">
            <button type="button" :class="{ active: pickupTimeType === 'asap' }" @click="pickupTimeType = 'asap'">هرچه سریع‌تر</button>
            <button type="button" :class="{ active: pickupTimeType === 'scheduled' }" @click="pickupTimeType = 'scheduled'">انتخاب زمان</button>
          </div>
          <label class="order-flow-field" v-if="pickupTimeType === 'scheduled'" style="margin-top:.8rem">
            <span>زمان تحویل از شرکت</span>
            <input class="order-flow-input" type="time" v-model="pickupTime" />
          </label>
          <label class="order-flow-field" style="margin-top:.8rem">
            <span>یادداشت اختیاری برای شرکت</span>
            <textarea class="order-flow-textarea" rows="3" v-model="customerNote" placeholder="مثلاً لطفاً سس جدا باشد" />
          </label>
        </section>
      </main>

      <OrderContextSummary class="pickup-order-summary" :next-step="nextStep" :currency="currency">
        <button class="order-flow-primary" type="button" :disabled="!selectedBranch" @click="continueToMenu">{{ continueLabel }}</button>
      </OrderContextSummary>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import OrderContextSummary from '@/components/OrderContextSummary.vue'
import { cartState, saveOrderContext } from '@/stores/cartStore'
import { isCustomerPickupCompany, resolvePickupCompanySelection } from '@/utils/orderBranches'
import { getBranches, getMenuBoot } from '@/utils/api'
import './orderFlow.css'

const branches = ref([])
const loading = ref(false)
const error = ref('')
const currency = ref('IRR')
const selectedBranchId = ref(cartState.orderContext.branch || '')
const pickupTimeType = ref(cartState.orderContext.pickup_time_type || 'asap')
const pickupTime = ref(cartState.orderContext.pickup_time || '')
const customerNote = ref(cartState.orderContext.customer_note || '')

function branchKey(branch = {}) {
  return branch.id || branch.name || ''
}

const selectedBranch = computed(() => branches.value.find((branch) => branchKey(branch) === selectedBranchId.value) || null)
const hasCartLines = computed(() => cartState.lines.length > 0)
const continueLabel = computed(() => hasCartLines.value ? 'ادامه به تکمیل سفارش' : 'مشاهده منو')
const nextStep = computed(() => hasCartLines.value ? 'تکمیل سفارش' : 'مشاهده منو و انتخاب غذا')

watch([selectedBranch, pickupTimeType, pickupTime, customerNote], () => {
  if (!selectedBranch.value) return
  saveOrderContext({
    order_type: 'pickup',
    branch: selectedBranch.value.id || selectedBranch.value.name,
    branch_title: selectedBranch.value.title || selectedBranch.value.name,
    prep_time_mins: Number(selectedBranch.value.prepTime || selectedBranch.value.prep_time_mins || 20),
    pickup_time_type: pickupTimeType.value,
    pickup_time: pickupTimeType.value === 'scheduled' ? pickupTime.value : '',
    delivery_fee: 0,
    customer_note: customerNote.value,
    courier_note: '',
    address: null,
  })
}, { deep: true })

function selectBranch(branch) {
  selectedBranchId.value = branchKey(branch)
}

async function loadBranches() {
  loading.value = true
  error.value = ''
  try {
    const [branchPayload, boot] = await Promise.all([getBranches(), getMenuBoot('')])
    branches.value = (Array.isArray(branchPayload?.branches) ? branchPayload.branches : []).filter(isCustomerPickupCompany)
    selectedBranchId.value = resolvePickupCompanySelection(branches.value, selectedBranchId.value)
    currency.value = boot?.currency || 'IRR'
  } catch (err) {
    error.value = err.message || 'دریافت شرکت‌ها ناموفق بود.'
  } finally {
    loading.value = false
  }
}

function continueToMenu() {
  if (!selectedBranch.value) return
  if (hasCartLines.value) {
    window.location.href = '/checkout'
    return
  }
  window.location.href = `/menu?branch=${encodeURIComponent(branchKey(selectedBranch.value))}`
}

onMounted(() => {
  saveOrderContext({ order_type: 'pickup', delivery_fee: 0, address: null, courier_note: '' })
  loadBranches()
})
</script>

<style scoped>
.order-flow-layout .pickup-branch-grid .order-flow-branch-card,
.order-flow-layout > .order-flow-list > .order-flow-branch-card {
  width: min(100%, 32rem);
  justify-self: start;
}

.order-flow-steps {
  display: flex;
  flex-wrap: nowrap;
  overflow-x: auto;
}

.order-flow-step {
  flex: 0 0 auto;
  white-space: nowrap;
}

.order-flow-hero {
  padding: clamp(1rem, 2vw, 1.3rem);
}

.order-flow-title {
  font-size: clamp(1.55rem, 4vw, 2.25rem);
  line-height: 1.25;
}

.order-flow-hero > .order-flow-secondary {
  width: fit-content;
  max-width: 100%;
  justify-self: start;
  white-space: nowrap;
}

.order-flow-branch-card.active {
  border-color: color-mix(in srgb, var(--ds-color-action-primary) 64%, var(--ds-color-border));
}

.order-flow-steps {
  scroll-snap-type: x proximity;
  scrollbar-width: thin;
}

.order-flow-step {
  scroll-snap-align: start;
}

@media (max-width: 560px) {
  .order-flow-hero > .order-flow-secondary {
    white-space: normal;
  }
}

.order-flow-page--pickup .order-flow-title {
  font-size: clamp(1.45rem, 3vw, 1.9rem);
  line-height: 1.3;
}

.order-flow-page--pickup .pickup-branch-card {
  min-height: 0;
  padding: 0.85rem 1rem;
}

.order-flow-page--pickup .pickup-branch-card.active {
  border-color: color-mix(in srgb, var(--ds-color-action-primary) 58%, var(--ds-color-border));
  border-inline-start: 3px solid var(--ds-color-action-primary);
}

.order-flow-page--pickup .pickup-branch-card__action {
  margin-top: 0.1rem;
}

.order-flow-page--pickup .pickup-time-card__heading {
  padding-bottom: 0.75rem;
  border-bottom: 1px solid var(--ds-color-border);
}

.order-flow-page--pickup .pickup-time-options {
  max-width: 34rem;
}


.order-flow-page--pickup :deep(.pickup-order-summary header > p:last-child),
.order-flow-page--pickup :deep(.pickup-order-summary .order-flow-summary-line:nth-child(-n + 4)) {
  display: none;
}

</style>
